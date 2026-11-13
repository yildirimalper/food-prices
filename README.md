# Türkiye food prices: why a record fruit harvest did not stop food inflation

A reproducible data study of the gap between what Turkish farmers are paid and
what Turkish consumers pay, built for the 2026 season.

**The question.** In 2026 fruit production rose **+60.8%** and vegetable production
was flat (**−0.8%**), yet food inflation stayed near **28%**. Traders are buying
from farmers at prices that are sometimes nominally below last year. Who is
capturing the difference — intermediaries, retailers, or input costs?

**The short answer.** See [`docs/FINDINGS.md`](docs/FINDINGS.md). In one line: the
farm gate is the *slowest-moving* link in the entire chain (+12.9% y/y against
+30.3% for farm inputs), the bumper fruit harvest *did* reach consumers (retail
fruit −1.0% y/y, worth ~3pp of avoided food inflation), and the inflation lives in
the 76.5% of the food basket that is not fresh produce — meat, dairy, bread and
beverages, whose costs are set by energy, imported feed, packaging, labour and rent
rather than by Turkish orchards.

## Layout

```
data/raw/         exactly what was downloaded, untouched
data/processed/   tidy CSVs produced by scripts/fetch_*.py
data/curated/     figures transcribed from TurkStat releases, one row per figure,
                  each carrying its source (TurkStat's API is now login-gated)
scripts/          fetch_*.py  acquisition      an0*.py  analysis
output/           analysis results as CSV + charts.json
docs/FINDINGS.md  the write-up
```

## Reproducing

```bash
python3 scripts/fetch_eurostat_hicp.py     # retail food prices, 5-digit COICOP
python3 scripts/fetch_eurostat_other.py    # producer prices, FX, minimum wage
python3 scripts/fetch_worldbank.py         # global energy / fertiliser / grain
python3 scripts/fetch_faostat.py           # farm-gate prices and production
for f in scripts/an0*.py; do python3 "$f"; done
```

## Sources and why these ones

| Layer | Series | Source | Coverage |
|---|---|---|---|
| Shelf | HICP, ECOICOP-2018, 409 categories to 5 digits | Eurostat (republishing TurkStat) | 2010-01 → 2026-09 |
| Basket | HICP item weights | Eurostat | 2015 → 2026 |
| Factory | Domestic PPI by NACE, 26 branches | Eurostat (republishing TurkStat) | 2015-01 → 2026-10 |
| Farm gate | Tarım-ÜFE, Tarım-GFE | TurkStat releases (curated) | 2026-06 → 2026-09 |
| Farm gate | Producer prices, LCU/tonne, monthly, 99 items | FAOSTAT | 2010 → 2024 |
| Farm gate | Producer price index, 145 items | FAOSTAT | 1991 → 2025 |
| Production | Crop and livestock output | FAOSTAT / TurkStat estimates | 1961 → 2026 |
| Inputs | Energy, fertiliser, grain, oils | World Bank Pink Sheet | 1960-01 → 2026-10 |
| Macro | EUR/TRY, USD/TRY, minimum wage | Eurostat | 2015 → 2026 |

**A note on TurkStat.** TurkStat's data portal moved to `veriportali.tuik.gov.tr`
during 2026 and its SDMX API (`nsiws.tuik.gov.tr`) now returns `401` without a
Keycloak login, so it cannot be scripted anonymously. Eurostat republishes
TurkStat's harmonised CPI and PPI, which is why those are the backbone here. The
agricultural producer and input price indices have no such mirror, so they are
transcribed from TurkStat's monthly releases into `data/curated/` with the source
recorded on every row. A free [EVDS](https://evds2.tcmb.gov.tr) key from the
central bank, or a TurkStat portal login, would let the whole thing be automated —
note that `evds2.tcmb.gov.tr` is currently blocked by this session's network policy.

**Caveat worth keeping in mind.** Tarım-ÜFE and the food CPI do not measure the
same basket: the farm index covers everything Turkish agriculture sells (including
cotton, tobacco and exported crops) while the food CPI covers what households buy
(including imported and heavily processed food). Comparing their growth rates is
informative but is not a clean margin measurement. The per-commodity work in
`an04_freshproduce.py` exists to check the aggregate story against matched pairs.
