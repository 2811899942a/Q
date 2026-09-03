# Data Manifest

## A. Official paper assets

| Asset | Canonical location | Expected role | Repo status |
|---|---|---|---|
| Article DOI | https://doi.org/10.1038/s41467-026-70417-z | Version of Record | linked |
| Supplementary Information | https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM1_ESM.pdf | Figs S1-S21, Tables, implementation detail | obtained locally; SHA256 locked |
| Reporting Summary | https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM2_ESM.pdf | research-design metadata | obtained locally; SHA256 locked |
| Transparent Peer Review | https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM3_ESM.pdf | reviewer/editor context | obtained locally; SHA256 locked |
| Source Data | https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM4_ESM.xlsx | source values underlying figures | obtained locally; audited; SHA256 locked |
| Author code capsule | https://doi.org/10.24433/CO.0939560.v1 | code to generate main results | pending capsule inspection |

## B. Upstream datasets explicitly named by the paper

| Dataset | Period/use | Native -> analysis resolution | Paper use | Preferred acquisition route |
|---|---|---|---|---|
| ERA5-Land | 1950-2023 | 0.1° -> 1° | T2m, radiation, precip, evaporation, dewpoint, SM 0-7/7-28/28-100 cm | **GEE first**: `ECMWF/ERA5_LAND/DAILY_AGGR`; preprocess server-side and export compact 1° products |
| GLDAS_CLSM | 1950-2023 drought chain | 0.25° -> 1° | 0-1 m SM + SWE | **author capsule / targeted GES DISC subset**; GEE GLDAS-2.2 CLSM starts in 2003 and is not an exact substitute for the historical chain |
| FluxSat GPP v2 | 2001-2019 | 0.05° -> 1° | primary vegetation productivity | author processed data if bundled; otherwise targeted ORNL/NASA subset, then reduce before local transfer |
| CSIF | 2001-2019 | 0.05° -> 1° | SIF validation | author processed data if bundled; otherwise targeted Figshare subset |
| FLUXNET2015 | site observations | site | validation | source/site subset only; no global raster issue |
| MCD12C1 | annual land cover | native -> 1° mode | vegetation type | **GEE first**: `MODIS/061/MCD12C1`; exact year/class-collapse awaits author code |
| Global tree density | spatial | gridded | RF predictor | author processed 1° layer preferred; otherwise targeted source download |
| Global canopy height | spatial | 1 km | RF predictor | author processed 1° layer preferred; otherwise targeted source download |
| Maximum rooting depth | spatial | gridded | RF predictor | author processed 1° layer preferred; exact product identity from capsule before download |
| Regridded HWSD v1.2 | spatial | gridded | soil cation exchange capacity | author processed 1° layer preferred; otherwise targeted ORNL product |
| NOAA GML atmospheric CO2 | daily | global series | CO2 fertilization predictor | small direct time series download |
| CMIP6 `mrso` SSP245 | 2024-2100 analysis | model native -> 1° nearest-neighbor | future flash/slow drought | author processed data if bundled; otherwise targeted ESGF subset for exact models/member/variable only |

## C. Retained CMIP6 models

After initial screening, the paper retained:

`ACCESS-CM2`, `BCC-CSM2-MR`, `MIROC6`, `MPI-ESM1-2-HR`, `MPI-ESM1-2-LR`, `MRI-ESM2-0`, `NorESM2-LM`, `NorESM2-MM`.

`CMCC_CM2_SR5` was evaluated and then excluded because of poorer standard deviation/RMSD performance in the Taylor-plot screening while retaining high-correlation models.

## D. Data-volume strategy: cloud preprocess, local compact outputs

The independent rebuild should avoid raw global archive downloads wherever possible.

Priority order:

1. reproduce the official author capsule from its bundled processed data;
2. for datasets available exactly in GEE, run spatial/temporal preprocessing in GEE and download only analysis-ready products;
3. for datasets not available exactly in GEE, use author-processed inputs or server-side source subsetting (GES DISC/ESGF/etc.);
4. download raw global archives only as a last resort.

Do **not** commit raw global ERA5-Land/GLDAS/CMIP6 to git. Keep in GitHub:

- checksums/manifests;
- exact GEE/source queries;
- small author-provided source tables when redistribution is licensed;
- processed test fixtures;
- compact event/metric summaries;
- code and metadata.

### GEE-specific plan

See `gee/README.md`.

For ERA5-Land, GEE is the preferred route because the official catalog provides the paper-required daily variables back to 1950. GEE should perform the 0-1 m depth weighting and 1° reduction server-side. After Code Ocean resolves the exact calendar/grid convention, it may also perform pentad aggregation and possibly drought-event extraction.

For MCD12C1, GEE should perform the paper-described 1° mode reduction once the exact source year/static-map convention is confirmed.

### Exact-reproduction guard

Cloud convenience must not change the dataset definition. In particular:

- GEE `NASA/GLDAS/V022/CLSM/G025/DA1D` begins in 2003 and is a GRACE-assimilated GLDAS-2.2 product; it cannot replace the paper's 1950-2023 GLDAS_CLSM contribution.
- CMIP6 must remain the paper's `mrso`, SSP245, exact retained models/member; do not substitute an easier downscaled climate product.
- GEE's grid/reducer defaults must be explicitly locked to the author's 1° grid before an exact reproduction claim.
