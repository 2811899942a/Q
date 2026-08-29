# Dense Diwopu sunset-anchor mechanism diagnosis

- May-Sep dense days with a real observation within 45 min of DSSAT sunset: **3774**.
- High-DTR calibration days (>14.8 C): **106**.
- High-DTR validation days: **59**.
- Calibration-only slope for `TS error = alpha * (DTR-14.8)+ * CLOUDS`: **alpha=7.8094 C per C-DTR-excess per unit CLOUDS**.

## High-DTR sunset-anchor error
| Split | N | Raw Bias | Raw RMSE | Corrected Bias | Corrected RMSE | r(error, DTRxCLOUDS) |
|---|---:|---:|---:|---:|---:|---:|
| Calibration_2000_2016 | 106 | +2.444 | 4.233 | +1.168 | 3.381 | 0.442 |
| Validation_2017_2024 | 59 | +2.387 | 4.536 | +0.914 | 3.725 | 0.429 |
| Validation_LowCloud | 24 | +0.706 | 2.037 | +0.484 | 1.973 | 0.071 |
| Validation_MidCloud | 15 | +0.245 | 1.203 | -0.824 | 1.636 | 0.412 |
| Validation_HighCloud | 20 | +6.012 | 7.391 | +2.733 | 5.853 | 0.156 |

Independent validation RMSE gain from the calibration-only sunset-anchor relation: **17.88%**.

Interpretation rule: changing the DSSAT sunset anchor is justified only if the raw high-DTR sunset bias is materially positive, the DTRxCLOUDS relationship persists in validation, and the frozen calibration slope reduces validation sunset RMSE without inducing a large negative bias.
