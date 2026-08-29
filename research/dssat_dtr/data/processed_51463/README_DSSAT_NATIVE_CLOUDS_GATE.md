# DSSAT-native CLOUDS-gated HTEMP mechanism test

This test uses the **exact DSSAT v4.8.5.0 SOLAR.for cloudiness definition** and introduces no Kt threshold or power hyperparameter. DTRc remains frozen at **14.8 C**.

- beta_pre = **21.9025 C per C-DTR-excess per unit CLOUDS**
- beta_post = **4.6759 C per C-DTR-excess per unit CLOUDS**
- calibration active points: pre=93, post=91

## Independent validation 2017-2024
| Scope | Official RMSE | Native-CLOUDS RMSE | Improvement | Official Bias | Native Bias | Official R2 | Native R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.7563 | 6.47% | 0.3368 | 0.2369 | 0.8029 | 0.8222 |
| DTR>=15 C | 5.1215 | 4.4332 | 13.44% | 1.2167 | 0.6120 | 0.5559 | 0.6163 |

Reference M10 high-DTR improvement = **13.71%**. Prefer this source-native form only if it retains a comparable advantage without introducing validation leakage.
