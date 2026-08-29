# M15 dense-station sunset-anchor transfer to primary Urumqi station

**No M15 parameter was fitted on primary-station validation data.**

- Source mechanism station: dense Diwopu `51463599999`, calibration 2000-2016.
- Frozen sunset coefficient: **alpha=7.8094**.
- Target station: `51463099999`, validation 2017-2024.
- DTR trigger: **>14.8 C**.
- Validation complete-curve physical violations: **0/130**.
- Validation days where corrected TS was capped at Tmin: **10/130**.

## Independent cross-station target validation
| Scope | Official RMSE | M15 RMSE | Improvement | Official Bias | M15 Bias | Official R2 | M15 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.8223 | 4.23% | 0.3368 | 0.1981 | 0.8029 | 0.8188 |
| DTR>=15 C | 5.1215 | 4.6783 | 8.65% | 1.2167 | 0.3777 | 0.5559 | 0.6210 |

Reference: M14 (single-station monotonic warp) = 7.43% high-DTR improvement; M10 statistical upper reference = 13.71%.

Automated decision: **CROSS_STATION_SOURCE_CANDIDATE**.
