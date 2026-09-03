# Reproduction Run Order

## Phase 0A - Nature asset integrity - COMPLETE

Completed on 2026-09-03:

1. Supplementary Information obtained and inspected.
2. Reporting Summary obtained and inspected.
3. Transparent Peer Review obtained and mined for implementation clarifications.
4. Source Data XLSX obtained and structurally/numerically audited.
5. SHA256 recorded for all four files.
6. Verified parameter/provenance facts transferred into GitHub documentation and `config/paper_parameters.json`.

**Gate G0A:** PASS.

## Phase 0B - Code Ocean integrity - NEXT LOCAL BLOCKER

1. Resolve/export Code Ocean capsule `10.24433/CO.0939560.v1` including code, metadata, environment and process data if exposed.
2. Preserve original capsule archive unchanged.
3. Record SHA256 and recursive file inventory.
4. Record capsule license before rehosting author files in this public repository.
5. Inspect environment definition, run script and full file tree.
6. Map each script to Fig.1-Fig.6 / Fig.S1-Fig.S21.
7. Resolve `KNOWN_UNCERTAINTIES.md` using the actual author implementation.

**Gate G0B:** capsule present + hashes + license/provenance + file inventory + code map.

## Phase 1 - Direct author-package rerun (G1)

Do not download ERA5/GLDAS/FluxSat globally yet.

1. Run the GitHub Source Data smoke checks first.
2. Reproduce the capsule's smallest documented workflow without changing parameters.
3. Preserve logs and MATLAB/environment metadata.
4. Compare generated outputs with Source Data and paper targets.
5. Prioritize Fig.1-3; then Fig.4-5.
6. Record numerical tolerances and any non-determinism.

**Gate G1:** principal author outputs numerically/visually consistent.

## Phase 2 - Independent drought-event engine (part of G2)

1. Rebuild ERA5-Land depth-weighted 0-1 m SM.
2. Harmonize with GLDAS_CLSM and reproduce the author's combined SM.
3. Reproduce exact detrending/deseasonalization, pentad/calendar and percentile construction from capsule.
4. Reproduce flash/slow event tables.
5. Validate at a small set of grids before global processing.
6. Reproduce count/severity/onset speed/flash-ratio summaries and BEAST turning points.

## Phase 3 - MFDI and hotspot classification (remaining G2)

1. Reproduce energy-/water-limitation map.
2. Reproduce aridity classes.
3. Reproduce vegetation classes.
4. Reproduce 29-region partition.
5. Implement the exact MFDI convention from author code.
6. Verify grid MFDI directly against Source Data `FigureS4a` before hotspot aggregation.
7. Verify hotspot/non-hotspot counts and Fig.2 source statistics.

**Gate G2:** event and hotspot outputs match author package on test grids and global summaries.

## Phase 4 - Vegetation resilience

1. Reproduce FluxSat preprocessing and 1-degree aggregation.
2. Reproduce pixel-specific growing season using the author code; use the peer-review clarification (minimum +30% amplitude; tropical year-round rule) as an audit check.
3. Reproduce drought-event separation/filtering.
4. Reproduce drought response and <=2-year recovery windows.
5. Reproduce GPP resilience.
6. Repeat with CSIF and FLUXNET verification.
7. Match Fig.3 and supplementary validation results.

## Phase 5 - Driver attribution (G3)

1. Assemble the 15 predictors exactly as capsule does.
2. Detrend/deseasonalize all temporal predictors.
3. Reproduce VIF screen (`VIF > 5` removal) and match Source Data `FigureS21a`.
4. Resolve the `5 leaves` vs `minimum terminal node size=5` wording conflict from MATLAB code.
5. Fit the four RF models with the capsule's exact implementation/seeds.
6. Reproduce OOB permutation importance.
7. Reproduce top-10 partial dependence and uncertainty bands.
8. Match Fig.4-5 and Fig.S21 accuracy output.

**Gate G3:** attribution ranking and response curves match within documented tolerance.

## Phase 6 - CMIP6 future analysis (G4)

1. Obtain only the exact nine candidate SSP245 `mrso`, `r1i1p1f1` datasets if absent from author process data.
2. Reproduce the Taylor-plot screening using Source Data `FigureS15` as a direct numerical target.
3. Verify exclusion of CMCC-CM2-SR5.
4. Use the retained eight models.
5. Reproduce calendar handling, nearest-neighbor 1-degree remapping and pentad means.
6. Run flash/slow event engine for 2024-2100.
7. Reproduce future trends and Fig.S10/S15.

**Gate G4:** future model ensemble results reproduced.

## Efficiency rule

Global upstream data are downloaded only after the author-package inventory demonstrates which exact files/variables/time windows are missing. GitHub stores logic, manifests, scripts and lightweight audit outputs; the local workspace stores large author/raw/process data.
