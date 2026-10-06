import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, numpy as np, json, sys, warnings; warnings.filterwarnings('ignore')
import statsmodels.formula.api as smf
W=pd.read_parquet('contracts_ic.parquet')
loc=W.bname.str.contains(r'\b(MUNICIPAL|METROPOLITAN[AO]|CANTON|PROVINCIAL|GOBIERNO AUTONOMO|MANCOMUNAD[AO])\b',regex=True)
W.loc[(W.btype=='Empresa pública')&loc,'btype']='Empresa pública local'
W.loc[W.btype=='Empresa pública','btype']='Empresa pública nacional'
D=W[W.region.isin(['COSTA','SIERRA','AMAZONIA'])&(W.cpc2!='')].copy()
D['lsup']=np.log(D.n_sup_market); D['lbuy']=np.log(D.buyer_n)
R=['SIERRA','COSTA','AMAZONIA']; B=['Gobierno central','GAD provincial','GAD municipal','GAD parroquial','Empresa pública local','Empresa pública nacional','Salud','Educación','Otros']
D['region']=pd.Categorical(D.region,R); D['btype']=pd.Categorical(D.btype,B)
D['grp']=pd.Categorical(np.where(D.btype.isin(B[1:4]),'GAD',np.where(D.btype=='Gobierno central','Central','Resto')),['Central','GAD','Resto'])
vc=D.cpc2.value_counts(); D['cpc2']=D.cpc2.where(D.cpc2.map(vc)>=100,'OTH')
vc=D.method.value_counts(); D['method']=D.method.where(D.method.map(vc)>=100,'OTH')
g=pd.factorize(D.buyer_id)[0]
ctrl=' + C(method) + C(cpc2) + C(year) + C(category)'
F={'M1':'sb ~ C(region)'+ctrl,'M2':'sb ~ C(region) + C(btype)'+ctrl,'M3':'sb ~ C(region) + C(btype) + lsup + local_sup + lbuy'+ctrl,
   'M4':'sb ~ C(btype) + lsup + local_sup + lbuy + C(breg)'+ctrl,
   'M5':'sb ~ C(region)*C(grp) + lsup + local_sup + lbuy'+ctrl}
k=sys.argv[1]; flt=sys.argv[2] if len(sys.argv)>2 else ''
if flt=='noquake': D=D[~(D.breg.isin(['MANABI','ESMERALDAS'])&D.year.isin(['2016','2017']))].copy()
if flt=='thick': D=D[D.n_sup_market>20].copy()
if flt=='noguayas': D=D[D.breg!='GUAYAS'].copy()
g=pd.factorize(D.buyer_id)[0]
m=smf.logit(F[k],data=D).fit(disp=0,method='newton',maxiter=300,cov_type='cluster',cov_kwds={'groups':g})
print(k,'converged',m.mle_retvals.get('converged'),m.nobs,round(m.prsquared,3),flush=True)
# AMEs by simulation with delta-method-free bootstrap of params (parametric, 200 draws)
rng=np.random.default_rng(1); V=m.cov_params(); P=m.params
draws=rng.multivariate_normal(P.values,V.values,200)
from patsy import dmatrix
import patsy; di=patsy.dmatrices(F[k],D,return_type='dataframe')[1].design_info
def pred(X,params): return 1/(1+np.exp(-(dmatrix(di,X,return_type='dataframe').values@params)))
def ame(fn):
    X0,X1=fn()
    pt=(pred(X1,P.values)-pred(X0,P.values)).mean()
    M0=dmatrix(di,X0,return_type='dataframe').values; M1=dmatrix(di,X1,return_type='dataframe').values
    s=[(1/(1+np.exp(-(M1@d)))-1/(1+np.exp(-(M0@d)))).mean() for d in draws]
    return pt,np.std(s)
res={}
def setv(col,val):
    X=D.copy(); X[col]=pd.Categorical([val]*len(X),D[col].cat.categories) if hasattr(D[col],'cat') else val; return X
if k!='M4':
    for r in R[1:]: res['region_'+r]=ame(lambda: (setv('region','SIERRA'),setv('region',r)))
for b in (B[1:] if k!='M5' else []): res['btype_'+b]=ame(lambda: (setv('btype','Gobierno central'),setv('btype',b)))
if k!='M1' and k!='M2':
  res['local_sup']=ame(lambda:(setv('local_sup',0),setv('local_sup',1)))
for c in (['lsup','lbuy'] if k not in ('M1','M2') else []):
    def f(c=c):
        X0=D.copy(); X1=D.copy(); X1[c]=X1[c]+np.log(2); return X0,X1
    res[c+'_x2']=ame(f)
if k=='M5':
    res={}
    for gv in ['Central','GAD','Resto']:
        for r in R:
            X=setv('region',r); X['grp']=pd.Categorical([gv]*len(X),['Central','GAD','Resto'])
            M=dmatrix(di,X,return_type='dataframe').values
            res[f'pm_{gv}_{r}']=(float((1/(1+np.exp(-(M@P.values)))).mean()),float(np.std([(1/(1+np.exp(-(M@d)))).mean() for d in draws])))
        for r in R[1:]:
            X0=setv('region','SIERRA'); X1=setv('region',r)
            for X in (X0,X1): X['grp']=pd.Categorical([gv]*len(X),['Central','GAD','Resto'])
            res[f'diff_{gv}_{r}']=ame(lambda: (X0,X1))
out=pd.DataFrame(res,index=['ame','se']).T; out['z']=out.ame/out.se
out.to_csv(f'ame_{k}{flt}.csv'); print(out.round(4),flush=True)
json.dump({'n':int(m.nobs),'pr2':float(m.prsquared),'conv':bool(m.mle_retvals.get('converged'))},open(f'fit_{k}{flt}.json','w'))
