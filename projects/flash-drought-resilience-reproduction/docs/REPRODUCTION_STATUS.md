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
2. Build ERA5-Land preprocessing in GEE (`ECMWF/ERA5_LAND/DAILY_AGGR`) to 1-degree products.
3. Resolve the exact historical GLDAS CLSM chain from NASA source metadata and use source-side subset/OPeNDAP rather than bulk global download.
4. Implement flash/slow drought event logic from the published Methods + Peer Review.
5. Treat unresolved calendar/equality/MFDI details as explicit sensitivity branches and select the branch that is best supported by Source Data and Supplementary targets.
6. Reproduce Fig. 1/2/3 numerical products before moving to RF attribution.

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
- GEE preprocessing scaffolds;
- Code Ocean access-failure audit.

## Next action when Codex/local work starts

Do **not** spend time repeatedly retrying the 403 DOI.

Start the independent reconstruction track:

1. verify the four Nature assets locally;
2. pull the GitHub project;
3. run the GEE ERA5-Land preprocessing on a small time/grid test first;
4. resolve and subset the exact NASA GLDAS CLSM historical product chain;
5. reconstruct a small set of flash/slow drought events and compare against Source Data/Supplementary expectations;
6. scale to the global 1-degree/pentad workflow after test-grid validation.

If Code Ocean later becomes reachable, audit it as a separate opportunity to convert G1 from `BLOCKED_EXTERNAL` to a runnable gate.
