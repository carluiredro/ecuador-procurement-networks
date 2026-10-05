"""Step 2. Combine yearly extracts into the processed dataset.

Input : data/interim/<year>.gz  (all yearly files; processes are filed by the year of their last update,
        so calls opened in 2015-2021 also appear in later files)
Output: data/processed/contracts_raw.parquet, data/processed/parties.parquet
"""
import gzip, io, glob, os
import pandas as pd

NUM = ['n_tenderers', 'n_tenderers_list', 'tender_value', 'n_enquiries', 'award_value', 'contract_value', 'n_suppliers_award']
dfs, ps = [], []
for f in sorted(glob.glob(os.path.join('data', 'interim', '*.gz'))):
    a, b = gzip.open(f, 'rt', encoding='utf-8').read().split('\n###PARTIES###\n')
    d = pd.read_csv(io.StringIO(a), sep='\t', dtype=str, quoting=3, keep_default_na=False)
    d['file'] = os.path.basename(f)[:4]
    dfs.append(d)
    ps.append(pd.read_csv(io.StringIO(b), sep='\t', dtype=str, quoting=3, keep_default_na=False))
df = pd.concat(dfs, ignore_index=True)
for c in NUM:
    df[c] = pd.to_numeric(df[c], errors='coerce')
P = pd.concat(ps).drop_duplicates('id', keep='last')
os.makedirs(os.path.join('data', 'processed'), exist_ok=True)
df.to_parquet(os.path.join('data', 'processed', 'contracts_raw.parquet'))
P.to_parquet(os.path.join('data', 'processed', 'parties.parquet'))
print(df.shape, 'rows;', df.ocid.nunique(), 'processes;', len(P), 'parties')
