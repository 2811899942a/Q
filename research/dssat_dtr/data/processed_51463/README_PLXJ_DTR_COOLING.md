# PL-XJ + DTR-triggered post-peak cooling

- Fixed DTRc: **14.5 C**.
- Calibrated lambda: **2.50**.
- Calibrated p: **0.05**.
- Optimum at search boundary: **YES**.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| Official DSSAT | 2.9469 | 5.1215 | 3.7612 | 1.2167 | 0.5559 |
| PL-XJ | 2.8092 | 4.8188 | 3.6229 | 0.9440 | 0.5690 |
| PL-XJ + DTR cooling | 2.7238 | 4.5224 | 3.5503 | -0.3101 | 0.5647 |

- All May-Sep improvement vs official: **7.57%**; additional improvement vs PL-XJ: **3.04%**.
- DTR>=15 improvement vs official: **11.70%**; additional improvement vs PL-XJ: **6.15%**.

Interpretation: a positive independent gain beyond PL-XJ supports a two-layer Urumqi formulation: regional baseline parameters for ordinary conditions plus a DTR-threshold structural correction for post-peak cooling. If the added gain is negligible, retain PL-XJ as the practical baseline and continue mechanism discovery before source-code modification.
