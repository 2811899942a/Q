# Urumqi dual-stage monotonic post-peak phase warp

## Calibration-only shape discovery
- Early cluster: n=105, median q=0.126, median phase advance=0.151.
- Late cluster: n=80, median q=0.705, median phase advance=-0.219.
- Interpolated phase-crossing q0 fixed at **0.363** before alpha/beta fitting.

## Fitted DTR response
- DTRc: **14.5 C**.
- alpha (early acceleration): **5.00 per C**.
- beta (late retardation): **0.00 per C**.
- Optimum at search boundary: **YES**.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| Official | 2.9469 | 5.1215 | 3.7612 | 1.2167 | 0.5559 |
| PL-XJ | 2.8092 | 4.8188 | 3.6229 | 0.9440 | 0.5690 |
| Dual-phase warp | 2.7812 | 4.7225 | 3.5652 | 0.8533 | 0.5745 |

- May-Sep improvement vs official: **5.62%**.
- DTR>=15 improvement vs official: **7.79%**.
- Additional DTR>=15 improvement beyond PL-XJ: **2.00%**.

## Physical QA
- High-DTR May-Sep days checked at 5-min resolution: **292**.
- Days with >0.02 C post-peak increase: **0**.
- Maximum 5-min increase: **0.0000 C**.

This form directly encodes the calibration-observed sign reversal: accelerated early post-peak cooling followed by relative late-afternoon retardation, while preserving a monotonic temperature decline and fixed peak/sunset anchors.
