# Google Earth Engine preprocessing track

This directory is the server-side preprocessing track for the Guo et al. (2026) flash-drought reproduction.

## Principle

Use Google Earth Engine (GEE) to do expensive global spatial/temporal preprocessing whenever the exact paper dataset is available in the official Earth Engine catalog. Download only compact, analysis-ready products to the local workstation. Raw multi-decade global archives should not be downloaded locally unless there is no equivalent server-side route.

The GEE track is deliberately separated from the author-package rerun. GEE products are for the **independent rebuild** after the Code Ocean implementation has been audited. They must not be used to claim exact reproduction while code-dependent conventions remain unresolved.

## Current GEE eligibility

### Safe / strong candidates

1. **ERA5-Land**
   - Official GEE collection: `ECMWF/ERA5_LAND/DAILY_AGGR`
   - Coverage: 1950 to near-real time.
   - Required bands are present: `temperature_2m`, `dewpoint_temperature_2m`, `volumetric_soil_water_layer_1`, `volumetric_soil_water_layer_2`, `volumetric_soil_water_layer_3`, `surface_solar_radiation_downwards_sum`, `total_precipitation_sum`, `total_evaporation_sum`.
   - Paper explicitly aggregates ERA5-Land from 0.1 degree to 1 degree and computes 0-1 m soil moisture as `0.07*SM1 + 0.21*SM2 + 0.72*SM3`.

2. **MCD12C1 land cover**
   - Official GEE collection: `MODIS/061/MCD12C1`.
   - This is the same MCD12C1 product family named in the paper.
   - Paper uses an IGBP vegetation-type map and a mode operation for 1-degree upscaling.
   - Exact year/static-map choice must still be read from author code before final export.

### GEE available but NOT an exact historical substitute

**GLDAS CLSM**

GEE currently exposes `NASA/GLDAS/V022/CLSM/G025/DA1D`, a GRACE-assimilated GLDAS-2.2 CLSM product beginning in 2003. The paper's flash/slow drought record is based on the mean of ERA5-Land and GLDAS_CLSM over 1950-2023. Therefore GLDAS-2.2 in GEE cannot be silently substituted for the paper's historical GLDAS chain.

NASA documents GLDAS-2.0 CLSM daily 0.25 degree (`GLDAS_CLSM025_D`) from 1948-2014. A continuation after 2014 must be resolved from the Code Ocean capsule/author implementation. If the exact continuation is not in GEE, use GES DISC server-side subsetting/OPeNDAP or the author's processed data rather than downloading the full archive.

### Do not assume official GEE equivalence

The following paper inputs should first be taken from the author capsule/process data when available; otherwise use targeted source-specific subsets:

- FluxSat GPP v2;
- CSIF;
- FLUXNET2015;
- global tree density;
- global canopy height;
- maximum rooting depth;
- Regridded HWSD v1.2 cation exchange capacity;
- CMIP6 `mrso` SSP2-4.5 for the eight retained ESMs.

Do not replace the paper's CMIP6 `mrso` with NEX-GDDP-style climate products merely because they are easier to access.

## Export strategy

The local workstation should receive compact products, not raw archives.

Preferred products after Code Ocean conventions are resolved:

1. yearly 1-degree pentad ERA5-Land 0-1 m soil-moisture stacks;
2. 2001-2019 1-degree pentad climate-driver stacks used for RF attribution;
3. 1-degree MCD12C1 vegetation classes;
4. if the event state machine is reproduced in GEE, annual flash/slow drought metric maps and compact event tables;
5. manifests containing source collection, bands, date range, grid transform, units and export-task identifiers.

Target grid for paper-scale reproduction is expected to be a global geographic 1-degree grid, but exact grid origin/mask must be verified against Code Ocean before G2 is marked PASS.

## Important ERA5-Land catalog caveats

- The GEE daily aggregate is derived from the hourly ERA5-Land asset.
- Flow bands have the `_sum` suffix; non-flow bands are daily means.
- `total_evaporation_sum` follows ECMWF sign convention: evaporation is normally negative.
- The catalog documents occasional packing-related negative/large values in accumulated precipitation and related flow variables; validation/QC is required.
- The catalog documents swapped values for three *component* evaporation bands. This project uses `total_evaporation_sum`, but the known-issues note remains part of provenance.
- The daily aggregate starts at `1950-01-02` in the catalog. Exact first-day/date-label behavior must be validated before an exact 1950 pentad series is accepted.

## Scripts

- `01_era5_land_prepare.js`: parameter-locked ERA5-Land spatial preprocessing and optional pentad export scaffold. Export execution is guarded until the paper's pentad/calendar convention is confirmed from Code Ocean.
- `02_mcd12c1_prepare.js`: MCD12C1 1-degree mode-export scaffold. Final export is guarded until the exact land-cover year/map convention is confirmed.

The guards are intentional. A convenient GEE workflow is not allowed to overwrite an unresolved author-method detail.
