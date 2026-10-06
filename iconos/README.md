# Gobiernos locales, región y riesgo de corrupción en la contratación pública del Ecuador (2015-2021)

Código de replicación del artículo enviado a *Íconos. Revista de Ciencias Sociales*.

Los scripts usan el conjunto de datos procesado que está en la raíz de este repositorio (`data/processed`) y las funciones de `code/netanalysis.py`. Deben ejecutarse en orden desde esta carpeta:

| Script | Qué hace | Salidas |
|---|---|---|
| `01_prep.py` | Clasifica a las entidades compradoras por tipo, asigna la región y calcula la densidad del mercado y el localismo | `contracts_ic.parquet` |
| `02_descriptivos.py` | Tasas de oferente único por región, provincia, densidad del mercado y concentración por comprador | `prov.csv`, `thin_bins.csv`, `buyer_conc.csv` |
| `03_modelos.py` | Modelos logit 1 a 5 con errores agrupados por entidad y efectos marginales promedio | `ame_M*.csv`, `fit_M*.json` |
| `04_graficos.py` | Gráficos 1 a 3 (15 cm, 300 dpi) | `figs/` |

Uso de `03_modelos.py`:

```
python 03_modelos.py M1      # también M2, M3, M4, M5
python 03_modelos.py M5 noquake    # sin Manabí y Esmeraldas en 2016-2017
python 03_modelos.py M5 noguayas   # sin Guayas
python 03_modelos.py M5 thick      # solo mercados con más de 20 proveedores
```

Requisitos: los mismos de `requirements.txt` en la raíz del repositorio (pandas, numpy, statsmodels, patsy, scipy, matplotlib, pyarrow).
