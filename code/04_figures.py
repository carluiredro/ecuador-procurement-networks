"""Step 4. Figures 1-6 of the article. Run from the repository root: python code/04_figures.py"""
import json, numpy as np, pandas as pd, matplotlib, igraph as ig
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from netanalysis import load, score_core

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.edgecolor': '#555', 'axes.labelcolor': '#222',
                     'xtick.color': '#444', 'ytick.color': '#444', 'savefig.dpi': 300})
GREY, ACC, RED, REF = '#B8B8B0', '#2A6FDB', '#C8483A', '#777777'
NAME = {'LOS RIOS': 'Los Ríos', 'MANABI': 'Manabí', 'BOLIVAR': 'Bolívar', 'SUCUMBIOS': 'Sucumbíos', 'CAÑAR': 'Cañar'}
nm = lambda p: NAME.get(p, p.title())
PV = pd.read_csv('results/provinces.csv'); PV['name'] = PV.province.map(nm)
FIG = 'figures/'; import os; os.makedirs(FIG, exist_ok=True)

# Fig 1: single bidding by year and by procedure
y = pd.read_csv('results/by_year.csv'); m = pd.read_csv('results/by_method.csv')
mlab = {'Subasta Inversa Electrónica': 'Electronic reverse auction', 'Menor Cuantía': 'Minor-value works/goods',
        'Cotización': 'Quotation', 'Licitación de Seguros': 'Insurance tender', 'Lista corta': 'Short list (consultancy)',
        'Licitación': 'Open tender', 'Comunicación Social – Proceso de Selección': 'Social communication (selection)',
        'Concurso publico': 'Public competition'}
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={'width_ratios': [1, 1.25]})
a = ax[0]; a.plot(y.year, y.sb * 100, color=ACC, lw=2, marker='o', ms=4)
a.scatter(y.year[y.n < 1000], y.sb[y.n < 1000] * 100, s=40, facecolors='white', edgecolors=ACC, zorder=4)
a.text(2018, y.sb[y.year == 2018].iloc[0] * 100 + 2.5, 'n < 500', ha='center', fontsize=7, color='#555')
a.set_ylim(0, 45); a.set_ylabel('Single-bid share of procedures (%)'); a.set_title('a  By year of call', loc='left', fontsize=9)
m = m[m.n >= 100].sort_values('sb'); b = ax[1]
b.barh([mlab[x] for x in m.method], m.sb * 100, color=[ACC if s > .5 else GREY for s in m.sb], height=.6)
for i, (s, n) in enumerate(zip(m.sb, m.n)): b.text(s * 100 + 1, i, f"{s*100:.0f}%  (n={n:,})", va='center', fontsize=7, color='#333')
b.set_xlim(0, 85); b.set_xlabel('Single-bid share (%)'); b.set_title('b  By procedure type, 2015–2021', loc='left', fontsize=9)
plt.tight_layout(); plt.savefig(FIG + 'Fig1.png'); plt.close()

# Fig 2: single bidding by province
p = PV.sort_values('sb_rate'); avg = (PV.sb_rate * PV.n_contracts).sum() / PV.n_contracts.sum()
fig, a = plt.subplots(figsize=(5.2, 4.6))
a.barh(p.name, p.sb_rate * 100, color=[ACC if s >= .385 else GREY for s in p.sb_rate], height=.65)
a.axvline(avg * 100, color=REF, ls='--', lw=1); a.text(avg * 100 + .5, -1.2, f'Contract-weighted mean {avg*100:.1f}%', fontsize=7, color='#444')
for i, s in enumerate(p.sb_rate): a.text(s * 100 + .5, i, f'{s*100:.0f}%', va='center', fontsize=7, color='#333')
a.set_xlabel('Share of competitive contracts with a single bid (%)'); a.set_xlim(0, 50); a.set_ylim(-1.8, len(p) - .4)
plt.tight_layout(); plt.savefig(FIG + 'Fig2.png'); plt.close()

# Fig 3: core network of El Oro (top-decile core), edges coloured by single bidding
c, P = load(); W = c[c.year.between('2015', '2021')]
g = W[W.breg == 'EL ORO']
e = g.groupby(['buyer_id', 'supplier_id']).agg(w=('sb', 'size'), sb=('sb', 'mean')).reset_index()
core, adj = score_core(e)
kb = np.quantile([k for u, k in core.items() if u[0] == 'B'], .9); ks = np.quantile([k for u, k in core.items() if u[0] == 'S'], .9)
cb = {u[1:] for u, k in core.items() if u[0] == 'B' and k >= kb}; cs = {u[1:] for u, k in core.items() if u[0] == 'S' and k >= ks}
ec = e[e.buyer_id.isin(cb) & e.supplier_id.isin(cs)]
names = pd.Index(pd.concat(['B' + ec.buyer_id, 'S' + ec.supplier_id]).unique())
G = ig.Graph(n=len(names), edges=list(zip(names.get_indexer('B' + ec.buyer_id), names.get_indexer('S' + ec.supplier_id))))
G = G.subgraph(G.connected_components().giant().vs.indices) if False else G
import random; ig.set_random_number_generator(random.Random(1))
lay = np.array(G.layout_fruchterman_reingold(weights=list(ec.w), niter=2000, seed=None).coords)
mean_sb = g.sb.mean()
fig, a = plt.subplots(figsize=(6, 5.4))
for (i, j), w, s in zip(G.get_edgelist(), ec.w, ec.sb):
    a.plot(*lay[[i, j]].T, color=RED if s > mean_sb else '#9DB7DE', lw=.4 + .35 * np.sqrt(w), alpha=.75, zorder=1)
isb = np.array([n[0] == 'B' for n in names])
a.scatter(*lay[isb].T, s=26, c='#555555', edgecolors='white', linewidths=.6, zorder=3, label='Buyer (public entity)')
a.scatter(*lay[~isb].T, s=14, c='white', edgecolors='#555555', linewidths=.6, zorder=3, label='Supplier (firm)')
a.plot([], [], color=RED, lw=1.5, label=f'Pair single-bid rate > provincial mean ({mean_sb*100:.0f}%)')
a.plot([], [], color='#9DB7DE', lw=1.5, label='Pair single-bid rate ≤ provincial mean')
a.legend(loc='lower center', bbox_to_anchor=(.5, -.13), ncol=2, fontsize=7, frameon=False); a.axis('off')
plt.tight_layout(); plt.savefig(FIG + 'Fig3.png'); plt.close()
json.dump({'elOro_core_buyers': len(cb), 'elOro_core_suppliers': len(cs), 'elOro_core_edges': len(ec), 'elOro_mean_sb': mean_sb}, open('results/fig3.json', 'w'))

# Fig 4: centralisation vs risk and core over-representation vs risk
from scipy import stats
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.2), sharey=True)
for a, x, lab, t in [(ax[0], 'core_share', 'Core share of contracts', 'a'), (ax[1], 'core_ratio', 'Single bidding in core / null expectation', 'b')]:
    sig = PV.p_core < .05 if x == 'core_ratio' else np.zeros(len(PV), bool)
    a.scatter(PV[x], PV.sb_rate * 100, s=22, c=np.where(sig, ACC, '#8C8C84'), zorder=3)
    k, b0 = np.polyfit(PV[x], PV.sb_rate * 100, 1); xx = np.linspace(PV[x].min(), PV[x].max(), 10)
    a.plot(xx, k * xx + b0, color=REF, lw=1, ls='--')
    r, pv = stats.pearsonr(PV[x], PV.sb_rate); rs, ps = stats.spearmanr(PV[x], PV.sb_rate)
    a.text(.03, .95, f'Pearson r = {r:.2f} (p = {pv:.3f})\nSpearman ρ = {rs:.2f} (p = {ps:.3f})', transform=a.transAxes, va='top', fontsize=7)
    for _, rr in PV.iterrows():
        if rr.name in [] or rr.province in ['EL ORO', 'MANABI', 'LOS RIOS', 'ESMERALDAS', 'LOJA', 'ZAMORA CHINCHIPE', 'PICHINCHA', 'GUAYAS', 'COTOPAXI', 'NAPO', 'BOLIVAR']:
            a.annotate(rr['name'], (rr[x], rr.sb_rate * 100), xytext=(4, 2), textcoords='offset points', fontsize=6.5, color='#333')
    if x == 'core_ratio': a.axvline(1, color=REF, lw=.8, ls=':')
    a.set_xlabel(lab); a.set_title(f'{t}', loc='left', fontsize=9)
ax[0].set_ylabel('Single-bid share (%)')
plt.tight_layout(); plt.savefig(FIG + 'Fig4.png'); plt.close()

# Fig 5: core over-representation vs clustering
off = {'Azuay': (-4, 6, 'right'), 'Tungurahua': (-6, -11, 'right'), 'Cotopaxi': (-6, 4, 'right'), 'Orellana': (5, -10, 'left'),
       'Imbabura': (-6, 4, 'right'), 'Cañar': (5, -8, 'left'), 'Loja': (5, -11, 'left'), 'Zamora Chinchipe': (5, 6, 'left'),
       'El Oro': (-6, 4, 'right'), 'Esmeraldas': (-6, 3, 'right'), 'Pichincha': (-6, 2, 'right'), 'Los Ríos': (5, 4, 'left'),
       'Chimborazo': (-6, -10, 'right'), 'Carchi': (-6, -10, 'right'), 'Manabí': (5, 4, 'left')}
fig, a = plt.subplots(figsize=(6, 4.4))
sig = PV.p_core < .05
a.scatter(PV.core_ratio, PV.clust_ratio, s=30, c=np.where(sig, ACC, '#8C8C84'), zorder=3, edgecolors='white', linewidths=.6)
for _, r in PV.iterrows():
    dx, dy, ha = off.get(r['name'], (5, 2, 'left'))
    a.annotate(r['name'], (r.core_ratio, r.clust_ratio), xytext=(dx, dy), textcoords='offset points', fontsize=7, ha=ha, color='#222' if r.p_core < .05 else '#555')
a.axvline(1, color=REF, lw=.8, ls=':'); a.axhline(1, color=REF, lw=.8, ls=':')
a.set_xlabel('Single bidding in core relative to null model'); a.set_ylabel('Clustering of single bidding relative to null model')
a.scatter([], [], c=ACC, s=30, label='Core over-representation, p < 0.05'); a.scatter([], [], c='#8C8C84', s=30, label='Not significant')
a.legend(fontsize=7, frameon=False, loc='upper left')
plt.tight_layout(); plt.savefig(FIG + 'Fig5.png'); plt.close()

# Fig 6: sensitivity of core over-representation to the core threshold
S = pd.read_csv('results/core_sensitivity.csv'); S['name'] = S.unit.map(nm)
piv = S.pivot(index='name', columns='q', values='core_ratio'); pp = S.pivot(index='name', columns='q', values='p_core')
order = piv.mean(axis=1).sort_values().index; piv = piv.loc[order]; pp = pp.loc[order]
fig, a = plt.subplots(figsize=(4.6, 5.2))
im = a.imshow(piv.values, cmap='RdBu_r', vmin=.6, vmax=1.4, aspect='auto')
a.set_xticks(range(piv.shape[1])); a.set_xticklabels([f'Top {int(round((1-q)*100))}%' for q in piv.columns])
a.set_yticks(range(len(piv))); a.set_yticklabels(piv.index, fontsize=7.5)
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        v = piv.values[i, j]; s = pp.values[i, j]
        a.text(j, i, f'{v:.2f}' + ('*' if s < .05 else ('†' if s > .95 else '')), ha='center', va='center', fontsize=6.5, color='white' if abs(v - 1) > .28 else '#222')
a.set_xlabel('Core definition (share of nodes by weighted core number)')
cb_ = plt.colorbar(im, ax=a, fraction=.05, pad=.03); cb_.set_label('Observed / null single bidding in core', fontsize=7)
for s in a.spines.values(): s.set_visible(False)
plt.tight_layout(); plt.savefig(FIG + 'Fig6.png'); plt.close()
print('ok')
