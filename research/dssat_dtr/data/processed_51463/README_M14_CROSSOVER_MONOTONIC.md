# M14 robust calibration-crossover monotonic CLOUDS HTEMP

- Formal DTR trigger: **>14.8 C**
- Calibration-only median-residual crossover H0: **10.455 solar hour**
- Robust crossing bracket: hour bins 8 (median Bias -0.839 C) -> 11 (median Bias 0.728 C)
- k_pre = **20.0000**, k_post = **16.4550**
- upper-bound hits: pre=True, post=False
- validation full-curve physical violations: **0/130**

## Independent validation 2017-2024
| Scope | Official RMSE | M14 RMSE | Improvement | Official Bias | M14 Bias | Official R2 | M14 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.8376 | 3.71% | 0.3368 | 0.2575 | 0.8029 | 0.8126 |
| DTR>=15 C | 5.1215 | 4.7408 | 7.43% | 1.2167 | 0.7443 | 0.5559 | 0.5756 |

Reference: M13 physically valid but only 4.28% high-DTR improvement; M10 statistical reference 13.71%.

Automated decision: **REVIEW_REQUIRED**.
