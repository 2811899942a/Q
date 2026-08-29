# M15 Xinjiang DSSAT temperature correction — next-operator quickstart

Timestamp: 2026-08-29 CST
Branch: `research/dssat-dtr-matrix`

## 1. What the innovation is

This project modifies DSSAT v4.8.5 CERES-Maize only where Xinjiang large diurnal temperature range (DTR) causes a reproducible hourly-temperature reconstruction error.

Core mechanism:
1. Official DSSAT `HTEMP` is always called first.
2. Outside the large-DTR regime, the official result is returned unchanged.
3. Before modeled Tmax, the official daytime curve is unchanged.
4. After Tmax to sunset, only the sunset anchor/cooling amplitude is corrected.
5. Night retains the official Parton-Logan exponential decay form, re-anchored to the corrected sunset temperature.
6. The correction uses DSSAT-native `CLOUDS`; no new weather variable is required.
7. On CERES extreme-temperature days, the existing 24-step thermal-time branch uses the corrected hourly `WEATHER%TGRO` instead of constructing a synthetic symmetric sine wave from Tmax/Tmin.

Current correction form:
`DTS = alpha * max(0, DTR - DTRc) * CLOUDS`
`TS1 = max(TMIN, TS0 - DTS)`

## 2. Current parameter status

Previous frozen reference:
- `DTRc = 14.8 C`
- `alpha = 7.8094`

Leading new candidate after prespecified four-level ablation:
- `DTRc = 14.0 C`
- threshold-specific temperature-only calibration gives `alpha = 6.8051`

Important: 14.0 C is the leading candidate, but has not yet replaced 14.8 C as the final frozen production parameter. Final replacement requires a focused robustness audit. Crop yield must never be used to fit DTRc or alpha.

## 3. Why 14.0 C is currently leading

Independent primary-station validation (2017-2024):
- official May-Sep RMSE: 2.9469 C
- T14P8: 2.8223 C
- T14P0: 2.8053 C
- official DTR>=15 RMSE: 5.1215 C
- T14P8: 4.6783 C
- T14P0: 4.6391 C
- T14P0 May-Sep bias: +0.1545 C
- T14P0 R2: 0.8207
- T14P0 complete-curve physical-shape violations: 0

Pure fixed-alpha threshold ablation also ranks 14.0 > 14.3 > 14.5 > 14.8, so the improvement is not created only by refitting alpha.

Shihezi crop-season active-day coverage rises from about 30-31% at 14.8 C to about 43-44% at 14.0 C.

## 4. Crop evidence — downstream only

Under the thesis-scale SRAD19.8 common-input reconstruction:
- H0TT ALL8 yield RRMSE: 26.915%
- T14P8: 25.038% (6.97% improvement vs H0TT)
- T14P0: 24.288% (9.76% improvement vs H0TT)
- T14P0 wins 6/8 absolute-error pairs vs both H0TT and T14P8.

Under raw POWER SRAD, T14P0 is worse than T14P8. This is retained as an important common-input sensitivity result; do not hide it and do not tune the temperature algorithm to remove it.

## 5. Exact implementation files

Hourly-temperature patch:
`research/dssat_dtr/dssat485/apply_m15_htemp_patch.py`

CERES extreme-day hourly thermal-time coupling:
`research/dssat_dtr/dssat485/apply_m15_extreme_dtt_patch.py`

Four-threshold ablation script:
`research/dssat_dtr/scripts/shihezi_dtrc_fourlevel_ablation.py`

Four-threshold workflow:
`.github/workflows/shihezi-dtrc-fourlevel-ablation.yml`

Latest four-threshold result:
`research/dssat_dtr/data/shihezi_real_case/dtrc_fourlevel_ablation/README_DTRC_FOURLEVEL_ABLATION.md`

Result checkpoint:
`research/dssat_dtr/CHECKPOINT_20260829_2248_DTRC_FOURLEVEL_RESULT.md`

## 6. Three scientific comparison arms

- `M0`: official DSSAT v4.8.5
- `H0TT`: official hourly-temperature path + hourly extreme-day DTT coupling
- `M15TT`: Xinjiang large-DTR correction + the same hourly DTT coupling

Interpretation:
- M0 -> H0TT = value of introducing the hourly/DTT pathway.
- H0TT -> M15TT = value added specifically by the Xinjiang correction.
- M0 -> M15TT = net effect.

## 7. Hard rules for anyone taking over

1. Do not tune DTRc or alpha using crop yield.
2. Do not tune Xinyu66 coefficients to improve M15 yield results.
3. Shared weather, soil, cultivar, irrigation and management inputs must be byte-identical across comparison arms.
4. Every changed DSSAT input must pass model-read/runtime audit.
5. Keep exact upstream DSSAT v4.8.5 source anchors; patch scripts deliberately refuse unknown source layouts.
6. Keep complete-curve physical QA: no below-Tmin/above-Tmax or monotonic-shape violations.
7. Retain unfavorable scenarios in reporting.

## 8. Immediate next experiment

Because 14.0 C is the lowest tested threshold and also the best temperature result, one final lower-bound audit is justified. It should be narrow and mechanism-grounded, not an endless parameter search.

Recommended final boundary set:
- 13.5 C — lower boundary supported by the independent-validation daily-RMSE breakpoint signal
- 13.8 C — intermediate transition check
- 14.0 C — current leader/reference

Optional 13.0 C may be included only as a deliberately aggressive lower-bound/negative-control sensitivity, not as a primary candidate.

Selection remains temperature-only. After the threshold is frozen, rerun the identical crop propagation experiment.

## 9. Five-minute onboarding summary

If a new operator reads only this file, they should understand:
- what DSSAT originally does;
- exactly what M15 changes and what it leaves untouched;
- why Xinjiang DTR is the trigger;
- which source files are patched;
- why 14.0 C is currently leading;
- why 14.0 C is not yet formally final;
- how to compare M0/H0TT/M15TT;
- which rules prevent yield-driven overfitting.
