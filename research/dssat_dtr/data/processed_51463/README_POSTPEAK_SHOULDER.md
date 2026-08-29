# Urumqi DTR-triggered post-peak shoulder suppression

- Fixed DTRc: **14.5 C**.
- Calibrated lambda: **4.70**.
- Calibrated k: **2.00**.
- Normalized correction peak occurs at q=**0.333** of the peak-to-sunset interval.
- Optimum at search boundary: **NO**.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| Official | 2.9469 | 5.1215 | 3.7612 | 1.2167 | 0.5559 |
| PL-XJ | 2.8092 | 4.8188 | 3.6229 | 0.9440 | 0.5690 |
| PL-XJ + shoulder | 2.7266 | 4.5336 | 3.5525 | -0.2750 | 0.5608 |

- All May-Sep improvement vs official: **7.48%**.
- DTR>=15 improvement vs official: **11.48%**.
- Additional DTR>=15 improvement beyond PL-XJ: **5.92%**.

This candidate is favored over a broad cooling shelf only if independent validation improves while late-afternoon bias is not over-corrected.
