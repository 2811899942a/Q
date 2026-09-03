# Reproduction Status

Last updated: 2026-09-03

## Gate summary

| Gate | State | Evidence |
|---|---|---|
| G0A NATURE_ASSETS_VERIFIED | **PASS** | Supplementary, Reporting Summary, Transparent Peer Review and Source Data supplied by user; file type/content inspected; SHA256 recorded in `AUTHOR_ASSET_AUDIT_20260903.md` |
| G0B CODE_OCEAN_CAPSULE_VERIFIED | **BLOCKED** | DOI confirmed, capsule still not materialized; license/file tree/environment unavailable for audit |
| G0 AUTHOR_ASSETS_VERIFIED | **PARTIAL_PASS** | Nature package complete; Code Ocean is the remaining author-package blocker |
| G1 AUTHOR_RUN_REPRODUCED | NOT_STARTED | requires Code Ocean capsule/environment |
| G2 CORE_METHOD_REBUILT | NOT_STARTED | exact code-dependent edge cases remain |
| G3 ATTRIBUTION_REBUILT | NOT_STARTED | requires fitted author implementation or independent processed predictors |
| G4 CMIP6_REBUILT | NOT_STARTED | intentionally deferred |

## Completed checks

- PASS: correct paper identified: *Nature Communications* 17:4050 (2026), DOI `10.1038/s41467-026-70417-z`.
- PASS: Version of Record PDF inspected.
- PASS: official Supplementary Information obtained and audited: 26 pages, Fig. S1-S21, Table S1-S3.
- PASS: official Reporting Summary obtained and audited; confirms MATLAB R2020b and Code Ocean process data/code deposit.
- PASS: official Transparent Peer Review obtained and audited; key reproduction clarifications extracted.
- PASS: official Source Data XLSX obtained and audited: 45 sheets, 0 formulas, 0 external links, 0 defined names.
- PASS: exact SHA256 hashes recorded for all four Nature assets.
- PASS: source-value OLS checks reproduce the rounded Fig. 1 count/severity/onset-speed linear slopes.
- PASS: Source Data confirm all final RF predictor VIF values are <5.
- PASS: Source Data confirm Fig. S21 RF group sample sizes (437/486/370/722).
- PASS: Source Data contain the nine-model Taylor metrics used for CMIP6 screening and support exclusion of CMCC-CM2-SR5 on STD/RMSD grounds.
- PASS: peer review resolves several previously ambiguous method details, including deseasonalize+detrend before soil-moisture percentiles, GPP growing-season threshold logic, OOB permutation importance intent and minimum terminal node wording.
- CHECKED/UNRESOLVED: literal MFDI reverse engineering from Source Data reaches ~0.98 correlation with published MFDI but not exact equality; author implementation is still required.

## Current blockers

1. Code Ocean capsule `10.24433/CO.0939560.v1` has not yet been exported/materialized.
2. The Version of Record says RF uses `300 binary trees with 5 leaves`; the peer-review response states `minimum terminal node size = 5`. Exact MATLAB parameterization must be read from released code.
3. Exact soil-moisture percentile reference-window/calendar handling and event edge cases require released code.
4. Exact MFDI implementation contains at least one convention not recoverable exactly from the printed equations + Source Data alone.
5. BEAST configuration, RF randomization/seeds, PDP confidence intervals, CO2-beta numerical implementation and CMIP6 calendar handling still require code inspection.

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
- explicit uncertainty ledger.

## Next action when Codex/local work starts

Priority 1 is **Code Ocean capsule export and audit**, not ERA5-Land/GLDAS bulk download.

After the capsule is obtained:

1. preserve original archive;
2. hash every file;
3. inventory file tree/environment;
4. map scripts to figures;
5. resolve `KNOWN_UNCERTAINTIES.md` against executable code;
6. run the smallest official author workflow against bundled process data;
7. only then derive the minimal missing upstream-download list.
