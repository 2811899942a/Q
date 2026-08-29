# Refined Urumqi DTR-triggered post-peak phase compression

- Fixed local DTR trigger: **14.5 C**.
- Search range: **gamma 0.000-0.800 per C**, step 0.002.
- Calibrated gamma: **0.280 per C DTR excess**.
- Optimum at search boundary: **NO**.
- Calibration: 2000-2016 May-Sep; independent validation: 2017-2024 May-Sep.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| M0 DSSAT official | 2.9469 | 5.1215 | 3.7612 | 1.2167 | 0.5559 |
| M1 PL-XJ-BAL | 2.8092 | 4.8188 | 3.6229 | 0.9440 | 0.5690 |
| M2 DTR-PC refined | 2.9004 | 4.9614 | 3.6830 | 0.0472 | 0.5747 |

- M2 all-May-Sep RMSE improvement vs official: **1.58%**.
- M2 DTR>=15 RMSE improvement vs official: **3.13%**.
- Afternoon 14-18 official RMSE/Bias: **4.0106/2.3338 C**.
- Afternoon 14-18 M2 RMSE/Bias: **3.7733/2.0643 C**.

## Interpretation
If the optimum is interior and validation improves, the one-parameter phase-compression mechanism has empirical support. If the optimum remains at the expanded boundary or high-DTR errors plateau at a large value, the phase warp is too restrictive and the next model should introduce a distinct post-peak cooling-shape term rather than further increasing gamma.
