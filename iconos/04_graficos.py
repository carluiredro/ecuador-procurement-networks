import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('figs',exist_ok=True)
import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':8.5,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#555','axes.labelcolor':'#222','xtick.color':'#333','ytick.color':'#333'})
C={'SIERRA':'#2a78d6','COSTA':'#eb6834','AMAZONIA':'#1baf7a'}; LAB={'SIERRA':'Sierra','COSTA':'Costa','AMAZONIA':'Amazonía'}; MK={'SIERRA':'o','COSTA':'s','AMAZONIA':'^'}
W_IN=15/2.54
# G1 provinces
pv=pd.read_csv('prov.csv'); pv=pv[pv.n>=100].sort_values('sb')
name=lambda s: s.title().replace('Rios','Ríos').replace('Bolivar','Bolívar').replace('Manabi','Manabí').replace('Sucumbios','Sucumbíos').replace('Cañar','Cañar')
fig,ax=plt.subplots(figsize=(W_IN,4.6))
y=np.arange(len(pv))
ax.barh(y,pv.sb,color=[C[r] for r in pv.region],height=0.72,edgecolor='white',linewidth=1)
for i,(v,n) in enumerate(zip(pv.sb,pv.n)): ax.text(v+0.004,i,f'{v:.3f}',va='center',fontsize=7,color='#333')
ax.set_yticks(y); ax.set_yticklabels([name(s) for s in pv.breg]); ax.set_xlim(0,0.5)
ax.axvline(0.302,color='#888',lw=0.8,ls='--'); ax.text(0.305,len(pv)-0.6,'Media nacional 0.302',fontsize=7,color='#555')
ax.set_xlabel('Proporción de procesos con oferente único')
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=C[r],label=LAB[r]) for r in ['COSTA','AMAZONIA','SIERRA']],frameon=False,loc='lower right')
ax.grid(axis='x',color='#e6e6e6',lw=0.6); ax.set_axisbelow(True)
plt.tight_layout(); plt.savefig('figs/Grafico1.png',dpi=300); plt.close()
# G2 margins
a=pd.read_csv('ame_M5.csv',index_col=0)
fig,ax=plt.subplots(figsize=(W_IN,3.2))
G=['Central','GAD','Resto']; GL={'Central':'Gobierno central','GAD':'GAD (provincial, municipal\ny parroquial)','Resto':'Empresas públicas, salud,\neducación y otros'}
off={'SIERRA':-0.22,'COSTA':0,'AMAZONIA':0.22}
for r in ['SIERRA','COSTA','AMAZONIA']:
    xs=[i+off[r] for i in range(3)]; m=[a.loc[f'pm_{g}_{r}','ame'] for g in G]; s=[a.loc[f'pm_{g}_{r}','se'] for g in G]
    ax.errorbar(xs,m,yerr=1.96*np.array(s),fmt=MK[r],color=C[r],ms=6,capsize=2,lw=1.2,label=LAB[r],mec='white',mew=0.8)
    for x,v in zip(xs,m): ax.text(x+0.05,v,f'{v:.2f}',fontsize=6.8,va='center',color='#333')
ax.set_xticks(range(3)); ax.set_xticklabels([GL[g] for g in G]); ax.set_ylim(0.15,0.55)
ax.set_ylabel('Probabilidad predicha de\noferente único'); ax.legend(frameon=False,ncol=3,loc='upper left')
ax.grid(axis='y',color='#e6e6e6',lw=0.6); ax.set_axisbelow(True)
plt.tight_layout(); plt.savefig('figs/Grafico2.png',dpi=300); plt.close()
# G3 two panels
tb=pd.read_csv('thin_bins.csv',header=[0,1],index_col=0)
D=pd.read_parquet('contracts_ic.parquet'); D=D[D.region.isin(['COSTA','SIERRA','AMAZONIA'])&(D.cpc2!='')]
D=D[D.btype.isin(['GAD provincial','GAD municipal','GAD parroquial'])]
D['m2']=D.method.where(D.method.isin(['Subasta Inversa Electrónica','Menor Cuantía','Cotización']),'Otros')
pm=D.pivot_table(index='m2',columns='region',values='sb',aggfunc='mean'); pn=D.pivot_table(index='m2',columns='region',values='sb',aggfunc='size')
fig,(a1,a2)=plt.subplots(1,2,figsize=(W_IN,3.0),gridspec_kw={'width_ratios':[1.1,1]})
bins=list(tb.index)
for r in ['SIERRA','COSTA','AMAZONIA']:
    v=tb[('mean',r)].values; n=tb[('size',r)].values; ok=~np.isnan(v)&(np.nan_to_num(n)>=100)
    a1.plot(np.arange(len(bins))[ok],v[ok],marker=MK[r],color=C[r],lw=1.6,ms=5,label=LAB[r],mec='white',mew=0.7)
a1.set_xticks(range(len(bins))); a1.set_xticklabels(bins,fontsize=7); a1.set_xlabel('Proveedores distintos en el mercado'); a1.set_ylabel('Proporción de oferente único'); a1.set_ylim(0.15,0.48)
a1.set_title('a) Densidad del mercado',fontsize=8.5,loc='left'); a1.legend(frameon=False,fontsize=7,loc='lower left'); a1.grid(axis='y',color='#e6e6e6',lw=0.6)
order=['Subasta Inversa Electrónica','Menor Cuantía','Cotización','Otros']; OL=['Subasta\ninversa','Menor\ncuantía','Cotización','Otros']
w=0.26
for j,r in enumerate(['SIERRA','COSTA','AMAZONIA']):
    a2.bar(np.arange(4)+(j-1)*w,[pm.loc[o,r] for o in order],width=w,color=C[r],edgecolor='white',linewidth=1,label=LAB[r])
a2.set_xticks(range(4)); a2.set_xticklabels(OL,fontsize=7); a2.set_ylim(0,0.75); a2.set_title('b) GAD según procedimiento',fontsize=8.5,loc='left'); a2.grid(axis='y',color='#e6e6e6',lw=0.6); a2.set_axisbelow(True)
plt.tight_layout(); plt.savefig('figs/Grafico3.png',dpi=300); plt.close()
pm.round(3).to_csv('g3b.csv'); pn.to_csv('g3b_n.csv'); print(pm.round(3)); print(pn)
