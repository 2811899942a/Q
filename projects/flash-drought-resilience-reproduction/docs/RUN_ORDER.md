# Reproduction Run Order

## Phase 0 - Asset integrity and licensing (G0)

1. Download the official Nature Supplementary Information.
2. Download the official Nature Source Data XLSX.
3. Resolve and export Code Ocean capsule `10.24433/CO.0939560.v1` including code, metadata, environment and data if licensed/exportable.
4. Record SHA-256 for every downloaded artifact.
5. Record the capsule license before rehosting author files in this public repository.
6. Inspect `REPRODUCING.md`, environment definition, run script and file tree.
7. Update `KNOWN_UNCERTAINTIES.md` using the actual author implementation.

**Gate G0:** official package present + hashes + license/provenance + file inventory.

## Phase 1 - Direct author-package rerun (G1)

Do not download ERA5/GLDAS/FluxSat globally yet.

1. Reproduce the capsule's documented run without changing parameters.
2. Preserve logs and environment metadata.
3. Compare generated outputs with Source Data and paper targets.
4. Prioritize Fig.1-3; then Fig.4-5.
5. Record numerical tolerances and any non-determinism.

**Gate G1:** principal author outputs numerically/visually consistent.

## Phase 2 - Independent drought-event engine (part of G2)

1. Rebuild ERA5-Land depth-weighted 0-1 m SM.
2. Harmonize with GLDAS_CLSM and reproduce the author's combined SM.
3. Reproduce exact pentad/calendar percentile construction from capsule.
4. Reproduce flash/slow event tables.
5. Validate at a small set of grids before global processing.
6. Reproduce count/severity/onset speed/flash-ratio summaries and BEAST turning points.

## Phase 3 - MFDI and hotspot classification (remaining G2)

1. Reproduce energy-/water-limitation map.
2. Reproduce aridity classes.
3. Reproduce vegetation classes.
4. Reproduce 29-region partition.
5. Implement the exact MFDI sign branch from author code.
6. Verify hotspot/non-hotspot counts and Fig.2 source statistics.

**Gate G2:** event and hotspot outputs match author package on test grids and global summaries.

## Phase 4 - Vegetation resilience

1. Reproduce FluxSat preprocessing and 1° aggregation.
2. Reproduce pixel-specific growing season.
3. Reproduce drought-event separation/filtering.
4. Reproduce drought response and <=2-year recovery windows.
5. Reproduce GPP resilience.
6. Repeat with CSIF and FLUXNET verification.
7. Match Fig.3 and supplementary validation results.

## Phase 5 - Driver attribution (G3)

1. Assemble the 15 predictors exactly as capsule does.
2. Detrend/deseasonalize all temporal predictors.
3. Reproduce VIF screen (`VIF > 5` removal).
4. Fit the four RF models with the capsule's exact implementation/seeds.
5. Reproduce OOB permutation importance.
6. Reproduce top-10 partial dependence and uncertainty bands.
7. Match Fig.4-5.

**Gate G3:** attribution ranking and response curves match within documented tolerance.

## Phase 6 - CMIP6 future analysis (G4)

1. Obtain the nine candidate SSP245 `mrso` datasets.
2. Reproduce the Taylor-plot screening.
3. Verify exclusion of CMCC_CM2_SR5.
4. Use the retained eight models.
5. Reproduce calendar handling, 1° remapping and pentad means.
6. Run flash/slow event engine for 2024-2100.
7. Reproduce future trends and Fig.S10/S15.

**Gate G4:** future model ensemble results reproduced.

## Efficiency rule

Global upstream data are downloaded only after the author-package run demonstrates which exact files/variables/time windows are needed. This avoids spending days reconstructing data that the official capsule may already provide in processed form.
