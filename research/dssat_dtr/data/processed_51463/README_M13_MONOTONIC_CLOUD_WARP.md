# M13 monotonic DSSAT-CLOUDS shape-warp HTEMP

The DTR x CLOUDS mechanism is retained, but the physically invalid additive M12 correction is replaced by an endpoint-preserving monotonic power warp.

- DTR trigger: **>14.8 C**
- `p_pre = 1 + k_pre*(DTR-DTRc)*CLOUDS`, **k_pre=20.0000**
- `p_post = 1 + k_post*(DTR-DTRc)*CLOUDS`, **k_post=16.4600**
- upper-bound hits: pre=True, post=False
- validation full-curve physical violations: **0/130 high-DTR days**

## Independent validation 2017-2024
| Scope | Official RMSE | M13 RMSE | Improvement | Official Bias | M13 Bias | Official R2 | M13 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.8836 | 2.15% | 0.3368 | 0.3009 | 0.8029 | 0.8089 |
| DTR>=15 C | 5.1215 | 4.9022 | 4.28% | 1.2167 | 1.0022 | 0.5559 | 0.5698 |

Reference statistical prototypes: M10=13.71% and M12=13.44% high-DTR RMSE improvement, but M12 is physically invalid as a direct source formula.

Automated decision: **REVIEW_REQUIRED**.
