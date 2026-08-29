# M15 four-level DTR trigger ablation prespecification

Timestamp: 2026-08-29 CST
Branch: `research/dssat-dtr-matrix`

## Purpose

Test whether modestly lowering the M15 trigger expands useful coverage of Xinjiang large-DTR days while preserving independent hourly-temperature skill and downstream crop behavior.

## Prespecified thresholds

The complete candidate set is fixed before inspecting new results:

- `T14P0`: DTRc = 14.0 C
- `T14P3`: DTRc = 14.3 C
- `T14P5`: DTRc = 14.5 C
- `T14P8`: DTRc = 14.8 C, current frozen M15 reference

No 12-13 C candidate is allowed in this experiment because the existing structural-break diagnostics place the error transition around 14.3-15.0 C.

## Two temperature-side comparisons

### A. Pure trigger ablation

Hold `alpha = 7.8094` fixed for all four thresholds. This isolates the mathematical consequence of changing DTRc only. It is diagnostic and is not automatically eligible to replace M15 because lowering DTRc also increases correction amplitude on already-high-DTR days.

### B. Threshold-specific temperature calibration

For each threshold independently, fit the sunset coefficient `alpha` only from dense Diwopu station 51463599999 calibration data (2000-2016), using the same through-origin mechanism:

`sunset_error = alpha * max(0, DTR-DTRc) * CLOUDS`

Then freeze that alpha and evaluate without refitting on primary station 51463099999 during 2017-2024.

Crop yield is never used to fit or select DTRc or alpha.

## Independent temperature decision metrics

For every threshold report:

- alpha fitted from dense-station 2000-2016 data;
- number and proportion of independent target-station days entering M15;
- May-Sep RMSE, MAE, bias and R2;
- DTR >= 15 C RMSE and bias;
- performance in DTR strata around the transition and in 15-18, 18-20 and >=20 C regimes;
- complete-curve physical-shape violations and Tmin-cap frequency.

The temperature-side candidate ranking is frozen before crop results are inspected. A lower threshold is only scientifically eligible if it does not materially degrade independent temperature skill or physical QA relative to T14P8.

## Crop propagation comparison

Build `H0TT`, `T14P0`, `T14P3`, `T14P5`, `T14P8` with threshold-specific alpha values frozen from temperature calibration. Use identical Shihezi soil, weather, cultivar, planting and irrigation inputs across arms.

Primary crop scenarios:

- `RAW_N_OFF`
- `SRAD19P8_N_OFF`

Nitrogen remains disabled because exact 2019-2020 fertilizer/mineral-N inputs are not published in the current source package.

For each threshold report 2019, 2020 and ALL8 RRMSE/MAE/Bias, absolute-error wins, yield shift versus H0TT, and comparison versus the frozen T14P8 reference.

## Hard interpretation rule

The final threshold must be justified from the temperature-side independent validation and mechanism evidence first. Crop output is downstream validation only. Do not choose 14.0/14.3/14.5 merely because it gives the lowest yield error.
