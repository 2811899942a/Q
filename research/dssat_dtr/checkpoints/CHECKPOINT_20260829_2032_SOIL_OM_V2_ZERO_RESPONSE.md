# CHECKPOINT 2026-08-29 20:32 CST — Shihezi soil-OM V2 zero-response result

## Run status

Workflow: `Shihezi M0 Soil OM Diagnostic V2`
Run: `33251645551`
Conclusion: workflow PASS; all HIGHOM finite-N cases completed.

## Diagnostic hypothesis

Guo Table 2-1 reports OM values such as 1.485 with the unit printed as g/kg. A later same-station Xinyu66 measurement is around 14.12 g/kg. HIGHOM therefore tested the conditional interpretation `1.485% OM = 14.85 g/kg`, converted to DSSAT SLOC by OM/1.724.

No M15 or Xinyu66 parameter was changed.

## 2020 M0 results

| Scenario | HIGHOM RRMSE % | Corresponding LOWOM RRMSE % | RMSE kg/ha | Bias kg/ha | Mean HWAM kg/ha |
|---|---:|---:|---:|---:|---:|
| HIGHOM_N129_SPLIT | 24.890 | 24.890 | 2737.9 | -2600.2 | 8399.8 |
| HIGHOM_N193_SPLIT | 16.909 | 16.909 | 1860.0 | -1598.2 | 9401.8 |
| HIGHOM_N129_BASAL | 24.403 | 24.403 | 2684.4 | -2513.2 | 8486.8 |

The HIGHOM outputs are numerically identical to the corresponding LOWOM corrected-N V2 cases.

## Interpretation

The OM-unit hypothesis currently produces **zero crop-output response** in this reconstruction.

Two explanations remain possible:

1. SLOC is entering DSSAT correctly, but changing it by this amount has negligible impact under the present one-season initialization and finite-N configuration;
2. the custom `SH.SOL` SLOC values are not actually reaching the model state used by the executable.

The identical values are too exact to assume biological insensitivity without checking the model-read path once.

Therefore a dedicated `Shihezi Soil SLOC Read Audit` has been triggered (run `33251858968`) to compare LOWOM/HIGHOM in the actual model-read input and detailed nitrogen state.

## Decision rule

- If the SLOC read audit proves LOWOM/HIGHOM differ inside DSSAT and outputs remain identical, close OM as a meaningful source-gap lever.
- If DSSAT sees identical SLOC/model state, correct the soil input path once and repeat the diagnostic.

Until that audit resolves the path, HIGHOM is not promoted to the formal 2019–2020 reconstruction.
