# Codex handoff - Flash drought reproduction

This file is the local execution entry point once Codex quota is available.

## Objective

Reproduce Guo et al. (2026), *Nature Communications* 17:4050 while minimizing local raw-data downloads. First reproduce the author package. For the independent rebuild, use Google Earth Engine (GEE) or source-side subsetting for expensive preprocessing and bring only compact, analysis-ready products to the workstation.

## Current verified state

- Nature Supplementary Information: obtained and SHA256 locked.
- Nature Reporting Summary: obtained and SHA256 locked.
- Nature Transparent Peer Review: obtained and SHA256 locked.
- Nature Source Data XLSX: obtained, 45 sheets audited, SHA256 locked.
- Code Ocean DOI identified: `10.24433/CO.0939560.v1`.
- Code Ocean capsule archive: **still required**.
- GitHub already contains paper logic, method map, parameter lock, figure matrix, uncertainty ledger, Source Data checks, provenance documentation and a guarded GEE preprocessing track.

Read first:

1. `README.md`
2. `docs/REPRODUCTION_STATUS.md`
3. `docs/AUTHOR_ASSET_AUDIT_20260903.md`
4. `docs/PEER_REVIEW_METHOD_CLARIFICATIONS.md`
5. `docs/SOURCE_DATA_AUDIT.md`
6. `docs/KNOWN_UNCERTAINTIES.md`
7. `config/paper_parameters.json`
8. `docs/RUN_ORDER.md`
9. `gee/README.md`

## Local root

Recommended:

```text
D:\FlashDrought_Guo2026_Reproduction\
```

Do not alter or delete the original user-downloaded Nature files. Maintain a read-only original-assets area and a separate working area.

## Task C0 - establish repository and assets

1. Clone/pull `2811899942a/Q`.
2. Work from `projects/flash-drought-resilience-reproduction`.
3. Place the four official Nature files in a local `00_author_assets\nature\` directory.
4. Run:

```powershell
python scripts\verify_official_assets.py --dir D:\FlashDrought_Guo2026_Reproduction\00_author_assets\nature
python scripts\audit_source_data.py D:\FlashDrought_Guo2026_Reproduction\00_author_assets\nature\41467_2026_70417_MOESM4_ESM.xlsx
python scripts\source_data_smoke.py D:\FlashDrought_Guo2026_Reproduction\00_author_assets\nature\41467_2026_70417_MOESM4_ESM.xlsx
```

Acceptance:

- exact Nature hashes PASS;
- workbook opens with 45 worksheets;
- source-data smoke checks PASS.

## Task C1 - obtain and freeze Code Ocean capsule

Open:

```text
https://doi.org/10.24433/CO.0939560.v1
```

Download/export the complete capsule, including environment metadata and process data if Code Ocean exposes them.

Preserve:

```text
00_author_assets\codeocean\CO.0939560.v1_original.*
```

Then create a recursive manifest containing:

- relative path;
- size;
- SHA256;
- extension;
- detected text/binary type.

Do not rename internal files before the manifest is captured.

## Task C2 - capsule audit before running

Identify:

- MATLAB scripts/functions;
- main entry script(s);
- input data directories;
- process/intermediate data already bundled;
- outputs expected by the authors;
- MATLAB toolbox dependencies;
- random seeds or `rng` calls;
- BEAST package/function;
- RF implementation/function and exact terminal-node/leaf parameter;
- MFDI implementation;
- percentile/calendar implementation;
- PDP confidence interval implementation;
- CMIP6 calendar handling.

Create a table:

```text
script | purpose | inputs | outputs | figure(s) | dependencies | runnable now? | blocker
```

Use this audit to update `docs/KNOWN_UNCERTAINTIES.md`. Do not infer missing parameters.

## Task C3 - smallest official rerun

Before reconstructing upstream data, locate the smallest author workflow that can run using bundled process data.

Priority:

1. Fig. 1 source/result generation;
2. Fig. 2 hotspot/MFDI result generation;
3. Fig. 3 resilience;
4. Fig. 4/5 RF/PDP.

For each successful target record:

- command/script;
- MATLAB version/toolboxes;
- runtime;
- input hashes;
- output hashes;
- numerical comparison against Source Data;
- visual comparison against paper;
- PASS/FAIL with tolerance.

## Task C4 - build the independent-reproduction data chain with cloud preprocessing

The default strategy is **GEE/cloud first, local compact outputs second**.

### C4.1 ERA5-Land: GEE preferred

Use the official Earth Engine collection:

```text
ECMWF/ERA5_LAND/DAILY_AGGR
```

GitHub already contains:

```text
gee/01_era5_land_prepare.js
```

Required paper variables:

- temperature_2m;
- dewpoint_temperature_2m;
- volumetric_soil_water_layer_1;
- volumetric_soil_water_layer_2;
- volumetric_soil_water_layer_3;
- surface_solar_radiation_downwards_sum;
- total_precipitation_sum;
- total_evaporation_sum.

GEE should perform server-side:

- the paper's 0-1 m ERA5-Land soil-moisture weighting: `0.07*SM1 + 0.21*SM2 + 0.72*SM3`;
- 0.1° -> 1° aggregation by mean;
- VPD derivation where needed;
- after Code Ocean resolves calendar/grid conventions: pentad aggregation and, if validated, further event preprocessing.

Do not download 74 years of global native-resolution ERA5-Land to Windows.

### C4.2 MCD12C1: GEE preferred

Use:

```text
MODIS/061/MCD12C1
```

GitHub already contains:

```text
gee/02_mcd12c1_prepare.js
```

The paper says 1° vegetation type is obtained by mode. Confirm the exact year/static-map selection and class collapse from Code Ocean before final export.

### C4.3 GLDAS_CLSM: do not substitute the easy GEE product

GEE exposes a GLDAS-2.2 CLSM product beginning in 2003. The paper's flash/slow drought chain uses ERA5-Land + GLDAS_CLSM for 1950-2023. Therefore the GEE 2.2 product alone is not historically equivalent.

Resolve the exact author GLDAS chain from Code Ocean first. Prefer, in order:

1. author-bundled processed 1°/pentad soil moisture;
2. targeted GES DISC server-side subset/OPeNDAP for only the required variable/time span;
3. a locally downloaded subset if unavoidable.

Do not bulk-download the complete GLDAS archive.

### C4.4 FluxSat / CSIF / static RF predictors

First use author-bundled 1° processed layers if present. If absent, use source-specific subsetting and preprocess before local transfer wherever possible.

### C4.5 CMIP6

Do not download a full CMIP6 archive. Preserve the paper definition exactly:

- variable: `mrso`;
- scenario: SSP2-4.5;
- member: `r1i1p1f1` as stated in the paper;
- exact retained eight models.

Prefer author-processed inputs if bundled. Otherwise request only those variables/models/times through ESGF/server-side subsetting. Do not replace `mrso` with an easier GEE/downscaled climate dataset.

## Task C5 - compact local products

The intended local inputs should be compact and auditable, such as:

- 1° pentad soil-moisture products by year;
- 1° pentad climate-driver products for 2001-2019;
- annual/period flash and slow drought event tables;
- MFDI/hotspot masks;
- 1° vegetation/static predictor grids;
- retained CMIP6 `mrso` pentad products only.

Every cloud-exported product must carry a manifest with:

- source collection/product;
- band/variable;
- date range;
- reducer;
- projection/grid transform;
- units/sign convention;
- mask;
- output hash;
- GEE task ID or source-side request identifier.

## Task C6 - GitHub return package

Do not commit large raw NetCDF/HDF/MAT/GeoTIFF archives.

Return to GitHub only auditable lightweight artifacts:

- capsule file manifest (CSV/JSON);
- environment/toolbox manifest;
- resolved method notes;
- run logs;
- GEE scripts and export manifests;
- figure comparison metrics;
- small CSV/Parquet event summaries;
- selected reproduced figures if redistribution/size permits;
- updated status/gates.

## Hard rules

1. No claim of exact reproduction from Source Data plotting alone.
2. No silent replacement of MATLAB parameters with Python/sklearn analogues.
3. If Version of Record and peer review conflict, inspect author code.
4. Prefer GEE/cloud-side preprocessing to local raw-data downloads whenever the exact dataset/product is available.
5. Cloud convenience must not change the scientific dataset definition; GLDAS/CMIP6 substitutes are prohibited without explicit validation.
6. No declaring G1 PASS solely because scripts run; outputs must be compared against Source Data/paper.
7. Preserve original author assets and hashes.
8. Errors should be diagnosed from first principles; do not repeatedly patch a broken pipeline when the author package can clarify the intended process.
