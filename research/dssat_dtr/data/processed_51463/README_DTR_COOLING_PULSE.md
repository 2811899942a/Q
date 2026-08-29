# Urumqi DTR-triggered afternoon cooling pulse

- Fixed DTR trigger: **14.5 C**.
- Calibrated lambda: **2.000**.
- Search range lambda 0.000-2.000, step 0.005.
- Optimum at boundary: **YES**.

## Independent validation

| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| M0_DSSAT_OFFICIAL | 2.9469 | 5.1215 | 3.7612 | 1.2167 | 0.5559 |
| M1_PL_XJ_BAL | 2.8092 | 4.8188 | 3.6229 | 0.9440 | 0.5690 |
| M2_PHASE_COMPRESSION | 2.9004 | 4.9614 | 3.6830 | 0.0472 | 0.5747 |
| M3_COOLING_PULSE | 2.8688 | 4.8509 | 3.6372 | 0.8148 | 0.5678 |

- DTR>=15 RMSE improvement vs official: **5.28%**.
- Afternoon 14-18 RMSE/Bias: official **4.0106/2.3338 C**, M3 **3.7775/2.0627 C**.
- Night (20-05) RMSE: official **2.3306 C**, M3 **2.3306 C**. These should be identical by construction.

## Interpretation
M3 is a stronger local-mechanism candidate than phase compression only if it improves high-DTR afternoon errors while leaving night and low-DTR predictions unchanged.
