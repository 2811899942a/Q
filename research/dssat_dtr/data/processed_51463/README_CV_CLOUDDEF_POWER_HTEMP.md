# Urumqi CV nonlinear radiative-deficit HTEMP

- DTR trigger: **>14.8 C**
- Gate: `G=(max(0,1-Kt)/0.4)^p`
- Power selected by 2000-2016 leave-one-year-out CV: **p=0.50**
- CV pooled high-DTR RMSE: **4.8873 C**
- beta_pre = **11.2576**; beta_post = **2.3686**

No Kt cutoff is introduced. As Kt approaches 1, the correction decays continuously toward zero.

## Independent validation 2017-2024
| Scope | Official RMSE | M11 RMSE | Improvement | Official Bias | M11 Bias | Official R2 | M11 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.7736 | 5.88% | 0.3368 | 0.1713 | 0.8029 | 0.8176 |
| DTR>=15 C | 5.1215 | 4.4989 | 12.16% | 1.2167 | 0.2153 | 0.5559 | 0.5854 |

Compare against M10 (13.71% high-DTR improvement) and inspect Kt strata before retention.
