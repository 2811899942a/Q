# Data Manifest

## A. Official paper assets

| Asset | Canonical location | Expected role | Repo status |
|---|---|---|---|
| Article DOI | https://doi.org/10.1038/s41467-026-70417-z | Version of Record | linked |
| Supplementary Information | https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM1_ESM.pdf | Figs S1-S21, Tables, implementation detail | remote-only pending fetch/license check |
| Reporting Summary | https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM2_ESM.pdf | research-design metadata | remote-only |
| Transparent Peer Review | https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM3_ESM.pdf | reviewer/editor context | remote-only |
| Source Data | https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM4_ESM.xlsx | source values underlying figures | remote-only pending fetch/license check |
| Author code capsule | https://doi.org/10.24433/CO.0939560.v1 | code to generate main results | remote-only pending capsule inspection |

## B. Upstream datasets explicitly named by the paper

| Dataset | Period/use | Native -> analysis resolution | Paper use | Access |
|---|---|---|---|---|
| ERA5-Land | 1950-2023 | 0.1° -> 1° | T2m, radiation, precip, evaporation, dewpoint, SM 0-7/7-28/28-100 cm | https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview |
| GLDAS_CLSM | historical | 0.25° -> 1° | 0-1 m SM + SWE | https://disc.gsfc.nasa.gov/datasets?keywords=GLDAS |
| FluxSat GPP v2 | 2001-2019 | 0.05° -> 1° | primary vegetation productivity | https://www.earthdata.nasa.gov/data/catalog/ornl-cloud-fluxsat-gpp-fpar-1835-2 |
| CSIF | 2001-2019 | 0.05° -> 1° | SIF validation | https://figshare.com/articles/dataset/CSIF/6387494 |
| FLUXNET2015 | site observations | site | validation | https://fluxnet.org/data/fluxnet2015-dataset/ |
| MCD12C1 | annual land cover | native -> 1° mode | vegetation type | https://www.earthdata.nasa.gov/data |
| Global tree density | spatial | gridded | RF predictor | https://elischolar.library.yale.edu/yale_fes_data/1/ |
| Global canopy height | spatial | 1 km | RF predictor | https://www.earthdata.nasa.gov/centers/ornl-daac |
| Maximum rooting depth | spatial | gridded | RF predictor | https://cordis.europa.eu/project/id/603608 |
| Regridded HWSD v1.2 | spatial | gridded | soil cation exchange capacity | https://www.earthdata.nasa.gov/data/catalog/ornl-cloud-hwsd-1247-1 |
| NOAA GML atmospheric CO2 | daily | global series | CO2 fertilization predictor | https://gml.noaa.gov/ccgg/trends/ |
| CMIP6 `mrso` SSP245 | 2024-2100 analysis | model native -> 1° nearest-neighbor | future flash/slow drought | https://aims2.llnl.gov/search/cmip6/ |

## C. Retained CMIP6 models

After initial screening, the paper retained:

`ACCESS-CM2`, `BCC-CSM2-MR`, `MIROC6`, `MPI-ESM1-2-HR`, `MPI-ESM1-2-LR`, `MRI-ESM2-0`, `NorESM2-LM`, `NorESM2-MM`.

`CMCC_CM2_SR5` was evaluated and then excluded because of poorer standard deviation/RMSD performance in the Taylor-plot screening while retaining high-correlation models.

## D. Data-volume strategy

Do **not** commit raw global ERA5-Land/GLDAS/CMIP6 to git. Keep:

- checksums/manifests;
- exact download scripts/queries;
- small author-provided source tables when redistribution is licensed;
- processed test fixtures;
- code and metadata.

Large raw files belong in external/object storage and are recreated by scripts.
