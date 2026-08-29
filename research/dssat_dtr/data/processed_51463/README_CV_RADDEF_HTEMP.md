# Urumqi cross-validated radiative-deficit-gated HTEMP

- DTR trigger: **>14.8 C** (calibration-only breakpoint)
- Kt cutoff scale selected by 2000-2016 leave-one-year-out CV: **Kt0=0.900**
- CV pooled high-DTR RMSE at selected Kt0: **5.0208 C**
- `Rdef=max(0,Kt0-Kt)/0.1`
- beta_pre = **2.3436 C per C-DTR-excess per 0.1-Kt-deficit**
- beta_post = **0.4970 C per C-DTR-excess per 0.1-Kt-deficit**

For Kt>=Kt0 the radiation gate is exactly zero, so high-clearness high-DTR days receive no shoulder cooling. Kt0 is treated as a cross-validated taper scale, not a universal physical threshold.

## Independent validation 2017-2024
| Scope | Official RMSE | M10 RMSE | Improvement | Official Bias | M10 Bias | Official R2 | M10 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.7526 | 6.59% | 0.3368 | 0.2173 | 0.8029 | 0.8218 |
| DTR>=15 C | 5.1215 | 4.4196 | 13.71% | 1.2167 | 0.4936 | 0.5559 | 0.6107 |

This is the preferred structure if it keeps the M9 low/mid-Kt gains, removes the high-Kt degradation, and improves or maintains the 12.84% M9 high-DTR gain.
