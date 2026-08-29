# Urumqi saturated DTR post-peak shoulder

- Fixed DTRc: **14.5 C**; fixed shoulder k=**2.0** (peak at one-third of peak-to-sunset interval).
- Calibrated lambda: **4.70**.
- Calibrated saturation eta: **0.00 per C**.
- Effective DTR excess: `E/(1+eta*E)`.
- Asymptotic effective excess: **infinite (no saturation)**.
- Optimum at search boundary: **YES**.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| Official | 2.9469 | 5.1215 | 3.7612 | 1.2167 | 0.5559 |
| PL-XJ | 2.8092 | 4.8188 | 3.6229 | 0.9440 | 0.5690 |
| Linear shoulder | 2.7266 | 4.5336 | 3.5525 | -0.2750 | 0.5608 |
| Saturated shoulder | 2.7266 | 4.5336 | 3.5525 | -0.2750 | 0.5608 |

- May-Sep improvement vs official: **7.48%**.
- DTR>=15 improvement vs official: **11.48%**.
- Additional DTR>=15 improvement beyond PL-XJ: **5.92%**.
- Additional DTR>=15 improvement beyond linear shoulder: **0.00%**.

Saturation is retained only if eta is interior and it improves independent high-DTR performance, especially the 18-20 and >=20 bins, without sacrificing the well-supported 15-18 bin.
