import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, numpy as np, json
from scipy import stats
W=pd.read_parquet('contracts_ic.parquet')
loc=W.bname.str.contains(r'\b(MUNICIPAL|METROPOLITAN[AO]|CANTON|PROVINCIAL|GOBIERNO AUTONOMO|MANCOMUNAD[AO])\b',regex=True)
W.loc[(W.btype=='Empresa pública')&loc,'btype']='Empresa pública local'
W.loc[W.btype=='Empresa pública','btype']='Empresa pública nacional'
D=W[W.region.isin(['COSTA','SIERRA','AMAZONIA'])&(W.cpc2!='')].copy()
print('N',len(D),'buyers',D.buyer_id.nunique(),'suppliers',D.supplier_id.nunique(),'sb',D.sb.mean().round(3), 'all W',len(W), W.region.value_counts(dropna=False).to_dict())
D['bin']=pd.cut(D.n_sup_market,[0,5,10,20,50,100,1e9],labels=['1-5','6-10','11-20','21-50','51-100','>100'])
tb=D.pivot_table(index='bin',columns='region',values='sb',aggfunc=['mean','size'],observed=True); print(tb.round(3)); tb.to_csv('thin_bins.csv')
print(D.groupby('local_sup').sb.mean().round(3)); print(D.pivot_table(index='btype',columns='local_sup',values='sb',observed=True).round(3))
print(D.groupby('region').local_sup.mean().round(3))
g=D.groupby('buyer_id')
conc=pd.DataFrame({'n':g.size(),'top':g.supplier_id.agg(lambda s: s.value_counts().iloc[0]/len(s)),'hhi':g.supplier_id.agg(lambda s: ((s.value_counts()/len(s))**2).sum()),'btype':g.btype.first(),'region':g.region.first(),'sb':g.sb.mean(),'nsup':g.supplier_id.nunique()})
c=conc[conc.n>=10]; c.to_csv('buyer_conc.csv')
print(len(c)); print(c.groupby('btype')[['top','hhi','sb']].median().round(3)); print(c.groupby('region')[['top','hhi','sb']].median().round(3))
print('spearman top-sb',stats.spearmanr(c.top,c.sb)); print('spearman hhi-sb',stats.spearmanr(c.hhi,c.sb))
for r in ['SIERRA','COSTA','AMAZONIA']:
    x=c[c.region==r]; print(r,len(x),stats.spearmanr(x.top,x.sb))
# provinces table
pv=D.groupby(['breg','region']).agg(n=('sb','size'),sb=('sb','mean'),local=('local_sup','mean'),msup=('n_sup_market','median'),gadshare=('btype',lambda s: s.isin(['GAD provincial','GAD municipal','GAD parroquial']).mean())).reset_index().sort_values('sb',ascending=False)
print(pv.round(3).to_string()); pv.to_csv('prov.csv',index=False)
# yearly by region
print(D.pivot_table(index='year',columns='region',values='sb').round(3))
