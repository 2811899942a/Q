# CHECKPOINT 2026-08-29 20:55 CST — HIGHOM diagnostic V2 completes with zero yield response

## Run
Workflow: `.github/workflows/shihezi-m0-soil-om-diagnostic-v2.yml`
Run ID: `33251645551`
Status: SUCCESS.
Result directory: `research/dssat_dtr/data/shihezi_real_case/m0_soil_om_diagnostic_v2/`.

## Test
All conditions were held as in the validated 2020 M0 finite-N diagnostic except the soil organic-carbon interpretation:
- LOWOM used Guo Table 2-1 values literally as g/kg, giving top SLOC about 0.0861% C.
- HIGHOM interpreted the same numeric values as percent OM, giving top SLOC about 0.8614% C (about 10x higher), consistent in magnitude with a later same-station topsoil OM measurement around 14.12 g/kg.

Three already-established diagnostic N scenarios were repeated without target tuning:
- N129 split
- N193 split
- N129 basal

## Result
The HIGHOM yield metrics are numerically identical to LOWOM V2:
- HIGHOM_N129_SPLIT: RRMSE 24.890%, mean HWAM 8399.8 kg/ha; LOWOM 24.890%.
- HIGHOM_N193_SPLIT: RRMSE 16.909%, mean HWAM 9401.8 kg/ha; LOWOM 16.909%.
- HIGHOM_N129_BASAL: RRMSE 24.403%, mean HWAM 8486.8 kg/ha; LOWOM 24.403%.

Example HIGHOM N129 split W1 nitrogen/output audit:
- HWAM 8078 kg/ha
- NI#M 9
- NICM 117 kg N/ha
- NUCM 150 kg/ha
- NLCM 6 kg/ha
- NMINC 83 kg/ha

## Immediate scientific interpretation
**Changing SLOC by 10x did not change yield in this reconstruction.** Therefore the organic-matter unit ambiguity cannot currently explain the remaining M0 yield mismatch.

However, because the equality is exact, this result must be interpreted in two stages:
1. It is valid to say HIGHOM did not alter the current run output.
2. Before declaring soil OM irrelevant, verify that the custom soil file and SLOC values are actually being read by the frozen DSSAT nitrogen module and are not ignored/defaulted/overridden in this setup.

## Decision
Do NOT spend time tuning OM values. Perform one minimal soil-input-read audit only:
- confirm `SHIH000100` resolves to the custom soil record;
- confirm the model-read SLOC/profile or nitrogen initial/mineralization state changes between LOWOM and HIGHOM;
- if the model genuinely reads both profiles and still gives identical seasonal output, close the OM hypothesis;
- if SLOC is not reaching the model, correct the soil-file input path/format once and rerun only the minimal comparison.

## Formal yield-reproduction gate correction already applied
A separate checkpoint (`CHECKPOINT_20260829_2050_YIELD_GATE_SOURCE_PRECISION.md`) corrected the source-supported gate to Guo's explicit statements:
- 2020 yield RRMSE <10%;
- W2–W4 yield ARE <5%;
- W1 2020 yield ARE about 13.19%.
The previously hard-coded 5.69% exact annual RRMSE is not treated as text-confirmed unless the figure annotation is independently re-verified.

## Rules
- No genotype/M15/N/OM target fitting.
- HIGHOM is not adopted as formal input merely because it is plausible.
- Every material result/failure/method change gets a checkpoint before further work.
