"""Network measures used in the article: weighted k-shell (s-core) cores, core over-representation of
single bidding against a permutation null, and clustering of single bidding across edge communities
(line graph + Louvain), following Wachs, Fazekas and Kertesz (2021)."""
import os, numpy as np, pandas as pd, igraph as ig, heapq
from collections import defaultdict

COMP = ['Subasta Inversa Electrónica','Menor Cuantía','Cotización','Licitación','Licitación de Seguros',
        'Lista corta','Concurso publico','Comunicación Social – Proceso de Selección']

def load():
    df = pd.read_parquet(os.path.join('data', 'processed', 'contracts_raw.parquet'))
    P = pd.read_parquet(os.path.join('data', 'processed', 'parties.parquet')).set_index('id')
    c = df[df.method_details.isin(COMP) & (df.supplier_id != '') & df.n_tenderers.notna()].copy()
    c['year'] = c.tender_start.str[:4]
    c['breg'] = c.buyer_id.map(P.region).fillna('')
    c['sreg'] = c.supplier_id.map(P.region).fillna('')
    c['sb'] = (c.n_tenderers == 1).astype(int)
    c['cpc2'] = c.tender_cpc.str[:2]
    c['supplier_id'] = c.supplier_id.str.split('-').str[0]  # harmonise suppliers by taxpayer number (RUC)
    c['method'] = c.method_details
    c['stratum'] = c.cpc2 + '|' + c.method
    c = c.drop_duplicates(['ocid', 'supplier_id'])
    return c, P

def score_core(edges):
    """edges: DataFrame buyer, supplier, w. Strength-based core decomposition (s-core)."""
    nodes = {}
    adj = defaultdict(dict)
    for b, s, w in edges[['buyer_id', 'supplier_id', 'w']].itertuples(index=False):
        u, v = 'B' + b, 'S' + s
        adj[u][v] = adj[u].get(v, 0) + w
        adj[v][u] = adj[v].get(u, 0) + w
    st = {u: sum(nb.values()) for u, nb in adj.items()}
    core = {}
    heap = [(s, u) for u, s in st.items()]
    heapq.heapify(heap)
    removed = set(); k = 0
    while heap:
        s, u = heapq.heappop(heap)
        if u in removed or s != st[u]:
            continue
        k = max(k, s); core[u] = k; removed.add(u)
        for v, w in adj[u].items():
            if v not in removed:
                st[v] -= w
                heapq.heappush(heap, (st[v], v))
    return core, adj

def core_analysis(c, nperm=1000, rng=None, rule='paper', q=0.9, strata='cpc2'):
    rng = rng or np.random.default_rng(42)
    e = c.groupby(['buyer_id', 'supplier_id']).size().rename('w').reset_index()
    core, adj = score_core(e)
    sb_ = {u: sum(nb.values()) for u, nb in adj.items()}
    bs = np.mean([v for u, v in sb_.items() if u[0] == 'B'])
    ss = np.mean([v for u, v in sb_.items() if u[0] == 'S'])
    if rule == 'paper':
        cb = {u[1:] for u, k in core.items() if u[0] == 'B' and k > bs}
        cs = {u[1:] for u, k in core.items() if u[0] == 'S' and k > 2 * ss}
    else:  # quantile of the core-number distribution on each side (robust in sparse networks)
        kb = np.quantile([k for u, k in core.items() if u[0] == 'B'], q)
        ks = np.quantile([k for u, k in core.items() if u[0] == 'S'], q)
        cb = {u[1:] for u, k in core.items() if u[0] == 'B' and k >= kb}
        cs = {u[1:] for u, k in core.items() if u[0] == 'S' and k >= ks}
    incore = (c.buyer_id.isin(cb) & c.supplier_id.isin(cs)).values
    sb = c.sb.values
    obs = sb[incore].mean() if incore.sum() else np.nan
    # null model: permute single-bid labels within strata
    sv = c[strata].values; groups = [np.where(sv == g)[0] for g in np.unique(sv)]
    nulls = np.empty(nperm)
    for i in range(nperm):
        p = sb.copy()
        for idx in groups:
            p[idx] = rng.permutation(sb[idx])
        nulls[i] = p[incore].mean() if incore.sum() else np.nan
    return dict(n_contracts=len(c), n_buyers=c.buyer_id.nunique(), n_suppliers=c.supplier_id.nunique(),
                sb_rate=sb.mean(), core_buyers=len(cb), core_suppliers=len(cs), core_share=incore.mean(),
                sb_core=obs, sb_core_null=np.nanmean(nulls) if incore.sum() else np.nan, p_core=(np.mean(nulls>=obs) if incore.sum() else np.nan), core_ratio=obs / np.nanmean(nulls) if incore.sum() else np.nan)

def edge_clustering(c, nperm=1000, rng=None, max_line_edges=30_000_000, strata='cpc2', n_runs=10):
    """Clustering of single bidding across edge communities.

    The bipartite network is turned into its line graph and partitioned with Louvain. Because Louvain is
    stochastic, the partition is repeated n_runs times with fixed seeds; the function returns the median
    clustering ratio and median permutation p value across runs, and the mean modularity.
    """
    import random
    rng = rng or np.random.default_rng(7)
    e = c.groupby(['buyer_id', 'supplier_id']).agg(w=('sb', 'size')).reset_index()
    names = pd.Index(pd.concat(['B' + e.buyer_id, 'S' + e.supplier_id]).unique())
    src = names.get_indexer('B' + e.buyer_id); dst = names.get_indexer('S' + e.supplier_id)
    g = ig.Graph(n=len(names), edges=list(zip(src, dst)))
    deg = np.array(g.degree())
    if (deg * (deg - 1) / 2).sum() > max_line_edges:
        return dict(modularity=np.nan, n_comm=np.nan, cv_obs=np.nan, cv_null=np.nan, clust_ratio=np.nan, p_clust=np.nan)
    L = g.linegraph()
    # map every contract to its buyer-supplier edge
    key = pd.Series(np.arange(len(e)), index=pd.MultiIndex.from_frame(e[['buyer_id', 'supplier_id']]))
    eidx = key.reindex(pd.MultiIndex.from_frame(c[['buyer_id', 'supplier_id']])).values
    sb = c.sb.values.astype(float)
    sv = c[strata].values; groups = [np.where(sv == x)[0] for x in np.unique(sv)]
    # one shared set of null permutations, reused for every partition
    perms = []
    for i in range(nperm):
        p = sb.copy()
        for idx in groups:
            p[idx] = rng.permutation(sb[idx])
        perms.append(p)
    res = []
    for run in range(n_runs):
        ig.set_random_number_generator(random.Random(1000 + run))
        comm = L.community_multilevel()
        memb = np.array(comm.membership)
        _, cl = np.unique(memb[eidx], return_inverse=True)
        nsz = np.bincount(cl); C = len(nsz)
        def wcv(lbl):
            m = np.bincount(cl, weights=lbl) / nsz
            if C < 2: return np.nan
            mu = (nsz * m).sum() / nsz.sum()
            var = (nsz * (m - mu) ** 2).sum() / ((C - 1) / C * nsz.sum())
            return np.sqrt(var) / mu if mu > 0 else np.nan
        obs = wcv(sb); nulls = np.array([wcv(p) for p in perms]); nm = np.nanmean(nulls)
        res.append((comm.modularity, C, obs, nm, obs / nm, float(np.mean(nulls >= obs))))
    ig.set_random_number_generator(random)
    r = np.array(res)
    return dict(modularity=float(r[:, 0].mean()), n_comm=float(np.median(r[:, 1])), cv_obs=float(np.median(r[:, 2])),
                cv_null=float(np.median(r[:, 3])), clust_ratio=float(np.median(r[:, 4])), p_clust=float(np.median(r[:, 5])),
                clust_ratio_min=float(r[:, 4].min()), clust_ratio_max=float(r[:, 4].max()))
