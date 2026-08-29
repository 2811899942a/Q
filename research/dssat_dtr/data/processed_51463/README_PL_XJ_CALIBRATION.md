# PL-XJ regional calibration — Urumqi 51463

## Split
- Calibration: **2000-2016**, May-Sep, 16,803 observation points; DTR>=15 C: 689 points.
- Independent validation: **2017-2024**, May-Sep, 5,917 points; DTR>=15 C: 975 points.
- Official DSSAT parameters: A=2.0, B=2.2, C=1.0.

## One-at-a-time sensitivity
- A: OAT RMSE span all=0.610 C, high-DTR=0.275 C; best one-at-a-time value all=1.5, high=1.0
- B: OAT RMSE span all=0.179 C, high-DTR=0.140 C; best one-at-a-time value all=2.0, high=2.0
- C: OAT RMSE span all=0.350 C, high-DTR=0.139 C; best one-at-a-time value all=0.75, high=0.75

## Joint-grid optima
- PL-XJ-ALL: A=1.0, B=0.75, C=1.25
- PL-XJ-HIGH: A=0.0, B=0.5, C=2.25
- **PL-XJ-BAL (recommended diagnostic regionalisation): A=0.5, B=0.5, C=1.75**

## Independent validation — recommended PL-XJ-BAL
| Scope | Official RMSE | PL-XJ-BAL RMSE | RMSE improvement |
|---|---:|---:|---:|
| May-Sep | 2.9469 C | 2.8092 C | 4.67% |
| May-Sep DTR>=15 C | 5.1215 C | 4.8188 C | 5.91% |

Official May-Sep MAE/MBE/R2: 1.9135 / 0.3368 / 0.8029.
PL-XJ-BAL May-Sep MAE/MBE/R2: 1.9188 / 0.1358 / 0.8081.

Official high-DTR MAE/MBE/R2: 3.7612 / 1.2167 / 0.5559.
PL-XJ-BAL high-DTR MAE/MBE/R2: 3.6229 / 0.944 / 0.569.

## Decision logic
- If independent validation improves substantially with only A/B/C regionalisation, a significant component of Urumqi error is **parameter-transfer / regionalisation error** in the original Parton-Logan implementation.
- If high-DTR residuals remain large after PL-XJ calibration, the remaining signal supports testing a **structural modification** (for example phase-corrected or cross-day temperature reconstruction) rather than endlessly tuning A/B/C.
- This calibration is not yet a crop-model validation and must not be described as improved maize yield simulation.
