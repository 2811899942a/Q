# Google Earth Engine preprocessing track

This directory is the server-side preprocessing track for Guo et al. (2026), *Nature Communications* 17:4050.

## Operational principle

Use GEE for expensive global raster processing whenever the exact paper dataset is available there. Keep the raw native-resolution archives out of the local workstation. Download only compact 1-degree outputs to Google Drive, then clean/validate those products against the official Nature Source Data.

The Code Ocean DOI cited by the paper is currently inaccessible (HTTP 403 in the user environment), so the independent reconstruction track proceeds from the Version of Record + Supplementary + Peer Review + Source Data. Any convention not uniquely recoverable remains an explicit validation branch.

## Run order

### 0. Smoke test first

Run:

```text
00_smoke_test.js
```

It creates a single January-2001 ERA5-Land test task over a small Europe window. Do not start global exports until this task completes and its band count/grid are checked.

### 1. ERA5-Land soil-moisture backbone

Run:

```text
01_era5_land_prepare.js
```

Official GEE collection:

```text
ECMWF/ERA5_LAND/DAILY_AGGR
```

The script performs the paper-defined 0-1 m weighting:

```text
SM_0_1m = 0.07*SM1 + 0.21*SM2 + 0.72*SM3
```

and simple-mean aggregation from native ERA5-Land resolution to an explicit global 1-degree geographic grid:

```text
EPSG:4326
crsTransform = [1, 0, -180, 0, -1, 90]
```

Exports are yearly daily stacks. Run them in decade-sized blocks:

```text
1950-1959
1960-1969
1970-1979
1980-1989
1990-1999
2000-2009
2010-2019
2020-2023
```

The export target is the unique root-level Google Drive folder:

```text
FlashDrought_Guo2026_GEE_exports
```

This keeps the long 1950-2023 soil-moisture backbone compact while preserving daily values for later pentad/calendar sensitivity testing.

### 2. MCD12C1 vegetation classes

Run:

```text
02_mcd12c1_prepare.js
```

Official collection:

```text
MODIS/061/MCD12C1
```

The paper states IGBP vegetation type and 1-degree upscaling by mode. Since the Version of Record does not identify one exact source year, the script exports annual 2001-2019 1-degree candidate maps. These files are small and allow later validation of the year/static-map convention rather than guessing it.

## Dataset eligibility

### Safe GEE inputs

- ERA5-Land: exact paper product family and required soil-water layers are available.
- MCD12C1: exact paper land-cover product family is available.

### GLDAS CLSM: source-side subset, not a blind GEE substitute

The paper uses ERA5-Land + GLDAS_CLSM mean soil moisture for the long 1950-2023 drought chain. NASA's historical daily CLSM product is:

```text
GLDAS_CLSM025_D.2.0
```

with a temporally consistent GLDAS-2.0 record from 1948 through 2014. GEE's convenient CLSM collection is GLDAS-2.2 GRACE-assimilated and starts in 2003, so it cannot silently replace the historical chain.

The post-2014 continuation used by the paper remains a reconstruction question. Handle GLDAS through GES DISC server-side subsetting/OPeNDAP and validate any stitching strategy against published Source Data before acceptance.

### Other paper inputs

Do not force these into GEE if the exact product is not available:

- FluxSat GPP v2;
- CSIF;
- FLUXNET2015;
- tree density;
- canopy height;
- maximum rooting depth;
- HWSD v1.2 cation exchange capacity;
- CMIP6 SSP2-4.5 `mrso` for the exact retained models.

Use source-side subsets or compact author/source products instead.

## Why the ERA5 export remains daily

The paper ultimately works at pentad scale, but the exact calendar edge handling remains partly unresolved because the author's executable capsule is not reachable. Exporting **daily 1-degree** ERA5 soil moisture is still small enough to manage and preserves the information needed to test alternative pentad conventions later. This is safer than hard-coding a potentially wrong pentad definition into a 74-year cloud export.

Once the exact/validated convention is selected, pentad construction, detrending, deseasonalization and percentile conversion can be rerun either in GEE or in the cleaning stage without returning to the native 0.1-degree ERA5 archive.

## Google Drive organization

See:

```text
docs/GOOGLE_DRIVE_WORKFLOW.md
```

Drive project root already created:

```text
FlashDrought_Guo2026_Reproduction
```

GEE staging folder already created:

```text
FlashDrought_Guo2026_GEE_exports
```

After exports arrive, the workflow is:

```text
GEE staging -> metadata/QC -> cleaned analysis-ready store -> Source Data validation
```

Large GeoTIFF/NetCDF/Zarr products remain in Drive. GitHub stores scripts, manifests, logs, small tables and validation metrics.

## Guard rules

1. `exportEnabled` stays `false` until the smoke test passes.
2. Do not substitute GEE GLDAS-2.2 for the full paper historical GLDAS contribution.
3. Do not infer an MCD12C1 year silently; export and validate candidates.
4. Do not claim exact author-package reproduction while Code Ocean remains inaccessible.
5. Independent reconstruction may still reach PASS if its outputs match the official Source Data within documented tolerances and unresolved conventions are explicitly tested.
