# Reproduction Status

Last updated: 2026-09-03

## Gate summary

| Gate | State | Evidence |
|---|---|---|
| G0A NATURE_ASSETS_VERIFIED | **PASS** | Supplementary, Reporting Summary, Transparent Peer Review and Source Data supplied by user; file type/content inspected; SHA256 recorded in `AUTHOR_ASSET_AUDIT_20260903.md` |
| G0B CODE_OCEAN_CAPSULE_VERIFIED | **BLOCKED_EXTERNAL** | DOI is printed in the published article, but user and ChatGPT access currently return/encounter 403; no verified alternate mirror was found in follow-up search |
| G0 AUTHOR_ASSETS_VERIFIED | **PARTIAL_PASS** | Nature package complete; Code Ocean author-script rerun remains externally blocked |
| G1 AUTHOR_RUN_REPRODUCED | BLOCKED_EXTERNAL | cannot be claimed without author code/environment |
| G2 CORE_METHOD_REBUILT | **READY_TO_START** | independent reconstruction can proceed from article + Supplementary + Peer Review + Source Data + official upstream datasets |
| G2A GEE_ERA5_PIPELINE | **READY_FOR_SMOKE_TEST** | production-ready GEE smoke test + yearly 1-degree ERA5-Land SM exporter committed; Drive staging folder created |
| G2B GLDAS_CHAIN | **SOURCE_IDENTIFIED / STITCH_UNRESOLVED** | NASA GLDAS_CLSM025_D.2.0 gives historical daily CLSM through 2014; paper's 2015-2023 continuation still requires validation |
| G3 ATTRIBUTION_REBUILT | NOT_STARTED | depends on G2 processed predictors and reconstruction decisions |
| G4 CMIP6_REBUILT | NOT_STARTED | intentionally deferred |

## Completed checks

- PASS: correct paper identified: *Nature Communications* 17:4050 (2026), DOI `10.1038/s41467-026-70417-z`.
- PASS: Version of Record PDF inspected.
- PASS: official Supplementary Information obtained and audited: 26 pages, Fig. S1-S21, Table S1-S3.
- PASS: official Reporting Summary obtained and audited; confirms MATLAB R2020b and a Code Ocean deposit.
- PASS: official Transparent Peer Review obtained and audited; key reproduction clarifications extracted.
- PASS: official Source Data XLSX obtained and audited: 45 sheets, 0 formulas, 0 external links, 0 defined names.
- PASS: exact SHA256 hashes recorded for all four Nature assets.
- PASS: source-value OLS checks reproduce the rounded Fig. 1 count/severity/onset-speed linear slopes.
- PASS: Source Data confirm all final RF predictor VIF values are <5.
- PASS: Source Data confirm Fig. S21 RF group sample sizes (437/486/370/722).
- PASS: Source Data contain the nine-model Taylor metrics used for CMIP6 screening and support exclusion of CMCC-CM2-SR5 on STD/RMSD grounds.
- PASS: peer review resolves several previously ambiguous method details, including deseasonalize+detrend before soil-moisture percentiles, GPP growing-season threshold logic, OOB permutation importance intent and minimum terminal node wording.
- CHECKED/UNRESOLVED: literal MFDI reverse engineering from Source Data reaches ~0.98 correlation with published MFDI but not exact equality; this remains an implementation uncertainty.
- PASS: GEE-first preprocessing track prepared for ERA5-Land and MCD12C1.
- PASS: GEE smoke test added; full ERA5 exporter now uses explicit 1-degree grid transform and yearly daily stacks.
- PASS: MCD12C1 exporter now preserves annual 2001-2019 candidate maps so the unstated source-year convention can be validated later.
- PASS: connected Google Drive project/staging folders created; workflow documented in `GOOGLE_DRIVE_WORKFLOW.md`.
- PASS: `CODE_OCEAN_ACCESS_AUDIT_20260903.md` records the 403/access failure and separates author-package rerun from independent reconstruction.

## Current blockers for exact author-script reproduction

1. Code Ocean capsule `10.24433/CO.0939560.v1` is currently inaccessible from the user's network (403) and could not be materialized through available ChatGPT retrieval routes.
2. The Version of Record says RF uses `300 binary trees with 5 leaves`; the peer-review response states `minimum terminal node size = 5`. Exact MATLAB parameterization remains unresolved.
3. Exact soil-moisture percentile reference-window/calendar handling and event edge cases remain unresolved.
4. Exact MFDI implementation contains at least one convention not recoverable exactly from the printed equations + Source Data alone.
5. BEAST configuration, RF randomization/seeds, PDP confidence intervals, CO2-beta numerical implementation and CMIP6 calendar handling remain author-code uncertainties.

These uncertainties block **G1 author-script rerun**, but no longer block an independently validated **G2 method reconstruction**.

## Independent-reconstruction route now authorized

Priority order:

1. Use Nature Source Data as numerical truth targets.
2. Run `gee/00_smoke_test.js` and inspect the single January-2001 output.
3. After smoke PASS, run `gee/01_era5_land_prepare.js` in decade-sized blocks to export daily 1-degree ERA5-Land 0-1 m soil moisture to Drive.
4. Export annual 2001-2019 MCD12C1 1-degree mode maps with `gee/02_mcd12c1_prepare.js`.
5. Resolve the exact historical GLDAS CLSM continuation after the NASA GLDAS-2.0 1948-2014 segment and use source-side subset/OPeNDAP rather than bulk global download.
6. Clean/stage the Drive outputs, preserving original files and manifests.
7. Implement flash/slow drought event logic from the published Methods + Peer Review.
8. Treat unresolved calendar/equality/MFDI details as explicit sensitivity branches and select the branch best supported by Source Data and Supplementary targets.
9. Reproduce Fig. 1/2/3 numerical products before moving to RF attribution.

## Google Drive state

Project root created:

`FlashDrought_Guo2026_Reproduction`

Dedicated Earth Engine root-level export folder created:

`FlashDrought_Guo2026_GEE_exports`

See `docs/GOOGLE_DRIVE_WORKFLOW.md` for folder ids, staging rules, cleaning/QC destinations and return-to-GitHub policy.

## GitHub-side preparation completed before Codex quota is used

- paper logic map;
- methods map;
- figure reproduction matrix;
- staged run order;
- data manifest + local download checklist;
- author-asset SHA256/provenance audit;
- peer-review method clarification audit;
- Source Data numerical/structural audit;
- machine-readable paper parameter lock in `config/paper_parameters.json`;
- Source Data workbook audit script;
- Source Data numerical smoke-test script;
- explicit uncertainty ledger;
- production-ready GEE smoke/export scripts;
- Google Drive staging/cleaning workflow;
- Code Ocean access-failure audit.

## Next user-side action

The next useful manual step is small and low-risk:

1. open Google Earth Engine Code Editor;
2. paste/run `gee/00_smoke_test.js`;
3. start the single generated export task;
4. confirm the resulting `SMOKE_ERA5Land_SM01m_1deg_200101` GeoTIFF appears in `FlashDrought_Guo2026_GEE_exports`.

After that file appears in Drive, it can be inspected/cleaned before any 74-year export is started.
