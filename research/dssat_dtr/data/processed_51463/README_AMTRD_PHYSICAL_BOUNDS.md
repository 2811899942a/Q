# AMTRD HTEMP physical-envelope validation

Frozen M12 parameters: DTRc=14.8 C, AMTRD0=1.200, beta_pre=1.6017, beta_post=0.3384.

- Evaluated May-Sep points: **22720**
- Active correction points: **447**
- Raw predictions below formal Tmin: **5**
- Raw predictions above formal Tmax: **0**
- Correction magnitude P50/P90/P95/P99/max: **1.722 / 8.118 / 11.666 / 20.148 / 43.174 C**

## Independent 2017-2024 high-DTR validation
| Model | RMSE | MAE | Bias | R2 | RMSE improvement |
|---|---:|---:|---:|---:|---:|
| M0 official | 5.1215 | 3.7612 | 1.2167 | 0.5559 | 0 |
| M12 raw | 4.4623 | 3.4425 | 0.3011 | 0.5940 | 12.87% |
| M12 clamped to [Tmin,Tmax] | 4.4536 | 3.4396 | 0.3040 | 0.5952 | 13.04% |

Source implementation should use the clamped form if raw corrections violate the daily physical envelope without reducing independent-validation skill.
