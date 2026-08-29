# M13 monotonic DSSAT-CLOUDS shape-warp HTEMP

The DTR x CLOUDS mechanism is retained, but the physically invalid additive M12 correction is replaced by an endpoint-preserving monotonic power warp.

- DTR trigger: **>14.8 C**
- `p_pre = 1 + k_pre*(DTR-DTRc)*CLOUDS`, **k_pre=10.0000**
- `p_post = 1 + k_post*(DTR-DTRc)*CLOUDS`, **k_post=10.0000**
- upper-bound hits: pre=True, post=True
- validation full-curve physical violations: **0/130 high-DTR days**

## Independent validation 2017-2024
| Scope | Official RMSE | M13 RMSE | Improvement | Official Bias | M13 Bias | Official R2 | M13 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.8883 | 1.99% | 0.3368 | 0.3056 | 0.8029 | 0.8086 |
| DTR>=15 C | 5.1215 | 4.9176 | 3.98% | 1.2167 | 1.0295 | 0.5559 | 0.5701 |

Reference statistical prototypes: M10=13.71% and M12=13.44% high-DTR RMSE improvement, but M12 is physically invalid as a direct source formula.

Automated decision: **REVIEW_REQUIRED**.
