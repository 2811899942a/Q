# DSSAT-native AMTRD-gated HTEMP prototype

This replaces the external FAO-style Kt used in M10 with the atmospheric transmission ratio already implied by DSSAT v4.8.5 `SOLAR.for` geometry. No new weather variable is required beyond existing SRAD.

- Frozen DTR trigger: **>14.8 C**
- AMTRD cutoff scale selected only by 2000-2016 leave-one-year-out CV: **1.200**
- CV pooled high-DTR RMSE: **4.9283 C**
- beta_pre: **1.6017**
- beta_post: **0.3384**

## Independent validation 2017-2024
| Scope | Official RMSE | M12 RMSE | Improvement | Official Bias | M12 Bias | Official R2 | M12 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.7639 | 6.21% | 0.3368 | 0.1855 | 0.8029 | 0.8192 |
| DTR>=15 C | 5.1215 | 4.4623 | 12.87% | 1.2167 | 0.3011 | 0.5559 | 0.5940 |

Reference M10 high-DTR improvement = **13.71%**. Promote M12 to source implementation if it retains most of that gain while using only DSSAT-native solar quantities.
