"""Step 3. All analyses reported in the article (2015-2021). Writes results/*.csv and results/summary.json.
Run from the repository root: python code/03_analysis.py"""
import json, os, numpy as np, pandas as pd, igraph as ig
from scipy import stats
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from netanalysis import load, core_analysis, edge_clustering, score_core

os.makedirs('results', exist_ok=True)
c, P = load()
W = c[c.year.between('2015', '2021')].copy()          # main analysis window
S = {}
S['n_rows_all'] = int(len(c)); S['n_window'] = int(len(W)); S['n_proc_window'] = int(W.ocid.nunique())
S['n_buyers'] = int(W.buyer_id.nunique()); S['n_suppliers'] = int(W.supplier_id.nunique())
S['sb_window'] = float(W.drop_duplicates('ocid').sb.mean())
S['local_supplier_share'] = float((W.breg == W.sreg).mean())

# ---- descriptives by year and by method
proc = W.drop_duplicates('ocid')
proc.groupby('year').agg(n=('ocid', 'size'), sb=('sb', 'mean')).to_csv('results/by_year.csv')
proc.groupby('method').agg(n=('ocid', 'size'), sb=('sb', 'mean'), med_tenderers=('n_tenderers', 'median')).sort_values('n', ascending=False).to_csv('results/by_method.csv')
proc.groupby('category').agg(n=('ocid', 'size'), sb=('sb', 'mean')).to_csv('results/by_category.csv')

# ---- validation of single bidding as risk proxy (process level, within method & year)
v = proc.copy()
v['ratio'] = v.award_value / v.tender_value
v = v[(v.tender_value > 0) & v.ratio.between(0.05, 1.5)]
v['tdays'] = (pd.to_datetime(v.tender_end, errors='coerce') - pd.to_datetime(v.tender_start, errors='coerce')).dt.days
val = {}
val['n_ratio'] = int(len(v))
val['ratio_sb'] = float(v[v.sb == 1].ratio.median()); val['ratio_multi'] = float(v[v.sb == 0].ratio.median())
import statsmodels.formula.api as smf
m1 = smf.ols('ratio ~ sb + C(method) + C(year) + C(category)', data=v).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(v.buyer_id)[0]})
val['ols_sb_coef'] = float(m1.params['sb']); val['ols_sb_se'] = float(m1.bse['sb']); val['ols_sb_p'] = float(m1.pvalues['sb'])
t = proc.copy(); t['tdays'] = (pd.to_datetime(t.tender_end, errors='coerce') - pd.to_datetime(t.tender_start, errors='coerce')).dt.days
t = t[t.tdays.between(0, 120)]
m2 = smf.logit('sb ~ tdays + C(method) + C(year)', data=t).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(t.buyer_id)[0]})
val['n_tdays'] = int(len(t)); val['logit_tdays_coef'] = float(m2.params['tdays']); val['logit_tdays_se'] = float(m2.bse['tdays']); val['logit_tdays_p'] = float(m2.pvalues['tdays'])
val['tdays_sb_median'] = float(t[t.sb == 1].tdays.median()); val['tdays_multi_median'] = float(t[t.sb == 0].tdays.median())
S['validation'] = val
print('validation', val, flush=True)

# ---- national, by year
rows = []
for y, g in W.groupby('year'):
    for rule, q in [('paper', None), ('q', 0.9)]:
        r = {'year': y, 'rule': rule}; r.update(core_analysis(g, 1000, rule=rule, q=q or 0.9)); rows.append(r)
pd.DataFrame(rows).to_csv('results/national_core.csv', index=False)
rows = []
for y, g in W.groupby('year'):
    for st in ['cpc2', 'stratum']:
        r = {'year': y, 'strata': st}; r.update(edge_clustering(g, 1000, strata=st)); rows.append(r)
pd.DataFrame(rows).to_csv('results/national_clust.csv', index=False)
print('national done', flush=True)

# ---- provinces (pooled 2015-2021)
prov = [(p, g) for p, g in W.groupby('breg') if p and len(g) >= 400]
rows = []
for p, g in prov:
    e = g.groupby(['buyer_id', 'supplier_id']).size()
    r = {'province': p, 'density': len(e) / (g.buyer_id.nunique() * g.supplier_id.nunique()),
         'local_share': float((g.breg == g.sreg).mean())}
    r.update(core_analysis(g, 1000, rule='q', q=0.9))
    r2 = core_analysis(g, 1000, rule='q', q=0.9, strata='stratum')
    r['core_ratio_strat'] = r2['core_ratio']; r['p_core_strat'] = r2['p_core']
    r.update(edge_clustering(g, 1000))
    r3 = edge_clustering(g, 1000, strata='stratum')
    r['clust_ratio_strat'] = r3['clust_ratio']; r['p_clust_strat'] = r3['p_clust']
    # subasta inversa only
    gs = g[g.method == 'Subasta Inversa Electrónica']
    r4 = core_analysis(gs, 1000, rule='q', q=0.9); r['core_ratio_sie'] = r4['core_ratio']; r['p_core_sie'] = r4['p_core']; r['sb_sie'] = r4['sb_rate']
    rows.append(r); print(p, flush=True)
PV = pd.DataFrame(rows); PV.to_csv('results/provinces.csv', index=False)

# ---- sensitivity of core definition (provinces + national pooled by year)
rows = []
for q in [0.80, 0.85, 0.90, 0.95]:
    for p, g in prov:
        r = core_analysis(g, 500, rule='q', q=q); rows.append({'unit': p, 'q': q, **r})
pd.DataFrame(rows).to_csv('results/core_sensitivity.csv', index=False)

# ---- cross-province correlations
corr = {}
for x in ['core_share', 'core_ratio', 'clust_ratio', 'modularity', 'density', 'local_share']:
    pr = stats.pearsonr(PV[x], PV.sb_rate); sr = stats.spearmanr(PV[x], PV.sb_rate)
    corr[x] = dict(pearson=float(pr[0]), p=float(pr[1]), spearman=float(sr[0]), sp=float(sr[1]))
S['corr_vs_sb'] = corr
S['n_prov'] = len(PV)
S['n_prov_clust_sig'] = int((PV.p_clust < 0.05).sum()); S['n_prov_clust_sig_strat'] = int((PV.p_clust_strat < 0.05).sum())
S['n_prov_core_over'] = int((PV.p_core < 0.05).sum()); S['n_prov_core_under'] = int((PV.p_core > 0.95).sum())
json.dump(S, open('results/summary.json', 'w'), indent=1, default=float)
print(json.dumps(S, indent=1, default=float))
