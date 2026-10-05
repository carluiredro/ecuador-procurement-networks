# Corruption risk in Ecuador's subnational procurement networks

Code and data for the article:

> Reyes-Vanegas L, Matute-Petroche J, Redroban-Ortiz C (2026). *Where does corruption risk sit? Core–periphery structure and clustering of single bidding in Ecuador's subnational public procurement networks.* Submitted to *Applied Network Science*.

The study analyses 46,279 contracts awarded through competitive procedures in Ecuador between 2015 and 2021. It builds weighted buyer–supplier networks nationally by year and for 21 provinces, identifies market cores with a strength-based k-shell decomposition, detects edge communities on line graphs with Louvain, and compares the location and clustering of single bidding with permutation null models. The method follows Wachs, Fazekas and Kertész (2021), *International Journal of Data Science and Analytics* 12(1):45–60, https://doi.org/10.1007/s41060-019-00204-1.

## Repository structure

```
code/
  01_extract.py        Extract a compact table from the OCDS bulk files (raw -> interim)
  02_build_dataset.py  Combine yearly extracts into the processed dataset (interim -> processed)
  netanalysis.py       Network measures: weighted k-shell core, core over-representation, edge clustering
  03_analysis.py       All analyses reported in the article (writes results/)
  04_figures.py        Figures 1-6 of the article (writes figures/)
data/
  raw/                 Place the downloaded OCDS files here (not included, see below)
  interim/             Output of step 1 (not included)
  processed/           contracts_raw.parquet and parties.parquet (included)
results/               CSV and JSON outputs used in the tables and text of the article
figures/               Figures 1-6 (PNG, 300 dpi)
```

## Quick start: reproduce the results from the processed data

Requires Python 3.11 or later.

```bash
pip install -r requirements.txt
python code/03_analysis.py   # about 2 minutes
python code/04_figures.py
```

All commands are run from the repository root. Random seeds are fixed: permutation null models use NumPy seeds and Louvain partitions are repeated ten times with fixed seeds, so the outputs in `results/` are reproduced exactly.

## Full reproduction from the original source

1. Download the yearly JSON files (`2015.jsonl.gz` to `2026.jsonl.gz`) of the Ecuador SERCOP publication from the Open Contracting Partnership data registry: https://data.open-contracting.org/en/publication/110. The data used in the article were retrieved on 2 October 2026.
2. Save them in `data/raw/`.
3. Run:

```bash
python code/01_extract.py 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026
python code/02_build_dataset.py
python code/03_analysis.py
python code/04_figures.py
```

All yearly files are needed even though the study covers 2015–2021: the bulk files group processes by the date of their last update, so calls opened in 2015–2021 also appear in later files. The analysis selects procedures by the year in which the call was opened. Later versions of the source files may differ slightly from the version used here.

## Variables in `data/processed/contracts_raw.parquet`

One row per award–supplier pair within a contracting process.

| Variable | Description |
|---|---|
| `ocid` | Open contracting process identifier (prefix `ocds-5wno2w-` removed) |
| `tender_start`, `tender_end` | Start and end of the bidding period (YYYY-MM-DD) |
| `method_details` | Procurement procedure as recorded by SERCOP (Spanish) |
| `category` | Main procurement category (goods, services, works) |
| `buyer_id` | Buyer identifier (RUC + SERCOP code) |
| `n_tenderers` | Number of tenderers reported in the tender |
| `n_tenderers_list` | Length of the tenderer list |
| `tender_value` | Reference budget (USD) |
| `tender_cpc` | Central Product Classification code of the first tender item |
| `n_enquiries` | Number of enquiries during the call |
| `award_date`, `award_value` | Date and value of the award |
| `supplier_id` | Supplier identifier (RUC + SERCOP code; harmonised by RUC in the analysis) |
| `contract_signed`, `contract_value` | Signature date and value of the contract, when available |
| `n_suppliers_award` | Number of suppliers in the award |
| `file` | Source yearly file |

`parties.parquet` lists every party with its name, province (`region`), canton (`locality`) and roles.

## Main analytical choices

- Competitive procedures only: electronic reverse auction, minor-value procedure, quotation, open tender, insurance tender, short list, public competition and social-communication selection. Catalogue purchases and direct awards are excluded.
- Single bid: `n_tenderers == 1`.
- Core: buyers and suppliers in the top decile of the weighted core-number distribution of their own side (the original rule of Wachs et al. 2021 is also reported).
- Null models: 1,000 permutations of single-bid labels within two-digit CPC codes, and within CPC × procedure strata as a robustness check.

## Data source and licence

Source data: Servicio Nacional de Contratación Pública (SERCOP), Ecuador, published in the Open Contracting Data Standard and distributed by the Open Contracting Partnership (https://data.open-contracting.org/en/publication/110). The processed files are a derived subset of these public records. Code is released under the MIT License.

## Citation

Please cite the article and this repository.

Repository: https://github.com/carluiredro/ecuador-procurement-networks
