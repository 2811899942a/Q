# Google Drive staging and cleaning workflow

## Connected Drive folders created on 2026-09-03

Project root:

- `FlashDrought_Guo2026_Reproduction`
- folder id: `1Jo9SM9D44qO1UVE6bOu_zG6Y6TRb1kog`

Subfolders:

- `00_author_assets` — `19rO07T3to2Oi4xomhGVZnVN_esSZyPki`
- `01_GEE_exports` — `13cTcTUIaeUmJJfSr8YCOZGbJAPcuIlNN`
- `02_GLDAS_subsets` — `1JTdVxgQFM7PvRg4H__DG8gsv5hzezqfR`
- `03_cleaned_analysis_ready` — `14wIlNTyk2v4hg0YzaNlzQW-cMe8wQiVr`
- `04_validation_against_source_data` — `1_ufm-YRdtCuwteKNME_Ro8ebe86jTtYF`
- `05_logs_manifests` — `15E_XD1C2uZi4ZWhJaXP1FheVHtOMDJ6C`

## Earth Engine export folder

Earth Engine's `Export.image.toDrive({folder: ...})` is most reliable with a unique root-level folder name. Therefore a dedicated root-level staging folder was also created:

- `FlashDrought_Guo2026_GEE_exports`
- folder id: `1D0hSUXoEzCI18quiUoHRE9gMpH-pNSec`

All GEE scripts use the folder name:

```text
FlashDrought_Guo2026_GEE_exports
```

After exports complete, the files are treated as immutable GEE staging assets. Cleaned products belong under the project root's `03_cleaned_analysis_ready` folder; QC outputs belong under `04_validation_against_source_data`; manifests/logs belong under `05_logs_manifests`.

## Workflow

### Stage D1 — GEE export

Run the scripts under `gee/` in Google Earth Engine Code Editor.

Current safe export targets:

1. `01_era5_land_prepare.js`
   - ERA5-Land 0-1 m soil moisture;
   - exact paper depth weighting `0.07/0.21/0.72`;
   - simple-mean aggregation to explicit 1-degree grid;
   - yearly daily stacks to Drive.

2. `02_mcd12c1_prepare.js`
   - annual 2001-2019 MCD12C1 IGBP;
   - mode aggregation to explicit 1-degree grid;
   - exports all candidate years because the paper does not state a single exact land-cover year.

### Stage D2 — Drive ingestion audit

Once files appear in Drive:

- enumerate every exported file;
- verify expected year coverage;
- record file size and Drive id;
- inspect GeoTIFF metadata (CRS, transform, band count, nodata, dtype);
- verify yearly ERA5 daily-band counts (365/366, subject to the ERA5-Land first-day catalog issue for 1950);
- verify 360 x 150 target-grid geometry for the -60..90 latitude domain;
- generate a machine-readable manifest.

### Stage D3 — cleaning

ERA5 soil-moisture annual stacks:

- preserve source GeoTIFF unchanged;
- parse band dates from `YYYYMMdd_sm_0_1m_era5land`;
- sort chronologically;
- detect duplicate/missing dates;
- normalize nodata representation;
- preserve units as `m3 m-3`;
- convert to an analysis-ready time x lat x lon structure (NetCDF/Zarr/Parquet-event output depending downstream stage);
- do not interpolate missing dates silently.

MCD12C1:

- preserve integer IGBP classes;
- verify class domain;
- compare annual maps to determine land-cover stability and later choose/validate the paper-compatible convention.

### Stage D4 — combine with GLDAS

GLDAS is staged separately in `02_GLDAS_subsets` because the exact long historical CLSM chain is not safely replaceable by the convenient 2003+ GEE GLDAS-2.2 collection.

After exact GLDAS daily 0-1 m soil moisture is obtained and reduced to the same 1-degree grid:

```text
SM_combined = mean(SM_ERA5Land_0_1m, SM_GLDAS_CLSM_0_1m)
```

Only matched dates/cells enter the combined series. Any temporal stitching between GLDAS product generations must be documented and validated.

### Stage D5 — drought processing

From the combined daily 1-degree series:

1. pentad aggregation;
2. deseasonalization;
3. detrending;
4. percentile conversion;
5. growing-season restriction;
6. flash/slow drought state-machine identification;
7. annual/event metrics;
8. MFDI/hotspot reconstruction.

Every uncertain convention must be tested against the official Nature Source Data. The selected branch must be the one best supported by the paper/peer review/source-value targets and documented in `KNOWN_UNCERTAINTIES.md`.

### Stage D6 — validation and compact return package

Validation outputs go to `04_validation_against_source_data`, including:

- Fig.1 trend comparisons;
- event-count/severity/onset-speed comparisons;
- MFDI correlation/error diagnostics;
- hotspot/non-hotspot counts;
- RF input-size/VIF checks later.

Only compact audited products are returned to GitHub:

- code;
- manifests;
- small CSV/Parquet summaries;
- logs;
- validation metrics;
- selected figures.

Large GeoTIFF/NetCDF/Zarr assets remain in Drive.

## Operational note

Google Drive is storage/staging, not the numerical engine itself. Heavy raster reduction is done in GEE; later cleaning/validation can be executed through the connected workflow or Codex/container compute while reading/writing Drive assets. This distinction keeps the data centralized in Drive without pretending that Drive itself runs scientific code.
