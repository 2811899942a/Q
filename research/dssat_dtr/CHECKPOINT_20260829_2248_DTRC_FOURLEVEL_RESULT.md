# DTRc four-level ablation result checkpoint

Timestamp: 2026-08-29 CST
Branch: `research/dssat-dtr-matrix`
Workflow run: `33257971548` (success)

## Prespecified thresholds
- T14P0: DTRc = 14.0 C
- T14P3: DTRc = 14.3 C
- T14P5: DTRc = 14.5 C
- T14P8: DTRc = 14.8 C (previous frozen reference)

Thresholds were specified before the run. Crop yield was not used to fit DTRc or alpha.

## Temperature-side result
Threshold-specific alpha was fitted only from dense-station 2000-2016 temperature data, then evaluated on independent primary-station 2017-2024 hourly temperature data.

| Arm | DTRc | alpha | validation active days | May-Sep RMSE C | DTR>=15 RMSE C | May-Sep bias C | R2 | shape violations |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| T14P0 | 14.0 | 6.8051 | 180 | 2.8053 | 4.6391 | +0.1545 | 0.8207 | 0 |
| T14P3 | 14.3 | 7.3094 | 157 | 2.8104 | 4.6469 | +0.1685 | 0.8202 | 0 |
| T14P5 | 14.5 | 7.5925 | 146 | 2.8141 | 4.6556 | +0.1791 | 0.8198 | 0 |
| T14P8 | 14.8 | 7.8094 | 130 | 2.8223 | 4.6783 | +0.1981 | 0.8188 | 0 |

The pure-trigger fixed-alpha ablation also ranks 14.0 C best, so the gain is not an artifact of alpha refitting.

Compared with T14P8, T14P0 lowers independent May-Sep RMSE by about 0.60% and DTR>=15 RMSE by about 0.84%, while increasing active validation days from 130 to 180. Relative to official M0, T14P0 May-Sep RMSE improves about 4.80%; high-DTR RMSE improves about 9.42% using the established official DTR>=15 reference.

## Shihezi coverage
- 2019 active days: 66 (14.0), 56 (14.3), 52 (14.5), 46 (14.8)
- 2020 active days: 67 (14.0), 61 (14.3), 56 (14.5), 47 (14.8)
Thus T14P0 covers about 43-44% of the reconstructed crop season versus about 30-31% for T14P8.

## Crop propagation
### RAW_N_OFF
T14P8 remains best among the four M15 thresholds (ALL8 RRMSE 42.268%); T14P0 = 44.799%. This raw-weather crop baseline is known to be strongly high-biased and is not an input-reproduction success case.

### SRAD19P8_N_OFF
- H0TT: 26.915% ALL8 RRMSE
- T14P8: 25.038% (+6.97% improvement vs H0TT)
- T14P0: 24.288% (+9.76% improvement vs H0TT)
T14P0 is 0.750 percentage points lower than T14P8 (about 2.99% relative reduction), with 6/8 absolute-error wins versus both H0TT and T14P8.

## Decision
Temperature-side selection is clear: T14P0 is the strongest candidate among the prespecified thresholds and remains physically valid (0 shape violations). Do not select the threshold from crop yield. Crop evidence is supportive under the thesis-scale SRAD19.8 reconstruction but input uncertainty remains, especially exact 2019-2020 SRAD/N.

Next: treat T14P0 as the leading temperature candidate and run a focused robustness audit (year-by-year independent temperature performance, DTR strata around 13-15 C, activation/cap diagnostics, and identical crop comparison) before replacing the previous T14P8 frozen reference.
