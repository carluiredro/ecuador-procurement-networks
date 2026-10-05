"""Step 1. Extract a compact table from SERCOP OCDS bulk files.

Input : data/raw/<year>.jsonl.gz  (yearly files from https://data.open-contracting.org/en/publication/110)
Output: data/interim/<year>.gz    (award-supplier rows + a parties table, separated by '###PARTIES###')

Usage : python code/01_extract.py 2015 2016 ... 2021
"""
import gzip, json, sys, os

H = ['ocid', 'tender_start', 'tender_end', 'method_details', 'category', 'buyer_id', 'n_tenderers',
     'n_tenderers_list', 'tender_value', 'tender_cpc', 'n_enquiries', 'award_date', 'award_value',
     'supplier_id', 'contract_signed', 'contract_value', 'n_suppliers_award']


def cl(s):
    return '' if s is None else str(s).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')


def sid(s):
    return (s or '').replace('EC-RUC-', '', 1) if (s or '').startswith('EC-RUC-') else (s or '')


def d10(s):
    return (s or '')[:10]


def num(x):
    if x is None:
        return ''
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)


def extract(year):
    src = os.path.join('data', 'raw', f'{year}.jsonl.gz')
    rows, parties = [], {}
    for line in gzip.open(src, 'rt', encoding='utf-8'):
        if not line.strip():
            continue
        r = json.loads(line)
        for p in r.get('parties') or []:
            pid = sid(p.get('id')); a = p.get('address') or {}
            roles = [x for x in (p.get('roles') or []) if x]
            if pid not in parties:
                parties[pid] = [cl(p.get('name')), cl(a.get('region')), cl(a.get('locality')), list(dict.fromkeys(roles))]
            else:
                for x in roles:
                    if x not in parties[pid][3]:
                        parties[pid][3].append(x)
        t = r.get('tender') or {}; tp = t.get('tenderPeriod') or {}
        items = t.get('items') or []
        tcpc = ((items[0] if items else {}).get('classification') or {}).get('id', '') or ''
        base = [cl(r.get('ocid')).replace('ocds-5wno2w-', ''), d10(tp.get('startDate')), d10(tp.get('endDate')),
                cl(t.get('procurementMethodDetails')), cl(t.get('mainProcurementCategory')),
                sid((r.get('buyer') or {}).get('id')), num(t.get('numberOfTenderers')),
                str(len(t.get('tenderers') or [])), num((t.get('value') or {}).get('amount')), tcpc,
                str(len(t.get('enquiries') or []))]
        cby = {c.get('awardID'): c for c in (r.get('contracts') or [])}
        awards = r.get('awards') or []
        if not awards:
            rows.append(base + ['', '', '', '', '', '0']); continue
        for a in awards:
            c = cby.get(a.get('id'), {})
            sups = a.get('suppliers') or []
            for s in (sups or [{'id': ''}]):
                rows.append(base + [d10(a.get('date')), num((a.get('value') or {}).get('amount')), sid(s.get('id')),
                                    d10(c.get('dateSigned')), num((c.get('value') or {}).get('amount')), str(len(sups))])
    txt = '\t'.join(H) + '\n' + '\n'.join('\t'.join(x) for x in rows) + '\n###PARTIES###\nid\tname\tregion\tlocality\troles\n'
    txt += ''.join(f'{k}\t{v[0]}\t{v[1]}\t{v[2]}\t{",".join(v[3])}\n' for k, v in parties.items())
    os.makedirs(os.path.join('data', 'interim'), exist_ok=True)
    with gzip.open(os.path.join('data', 'interim', f'{year}.gz'), 'wt', encoding='utf-8') as f:
        f.write(txt)
    print(year, len(rows), 'rows', len(parties), 'parties')


if __name__ == '__main__':
    for y in sys.argv[1:] or [str(y) for y in range(2015, 2022)]:
        extract(y)
