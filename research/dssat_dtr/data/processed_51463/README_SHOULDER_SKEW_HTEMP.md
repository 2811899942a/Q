# Urumqi DTR-triggered shoulder-contraction and skew HTEMP

- Calibration-only trigger: **DTR > 14.8 C**
- Shoulder-width coefficient: **beta_width=10.8776**
- Asymmetry/skew coefficient: **beta_skew=-0.1089**

The two deformation bases are zero at Tmin-time, modeled Tmax, and sunset, so the daily anchors remain unchanged.

## Independent validation 2017-2024

| Scope | Official RMSE | M8 RMSE | Improvement | Official Bias | M8 Bias | Official R2 | M8 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.9792 | -1.09% | 0.3368 | 0.2364 | 0.8029 | 0.7977 |
| DTR>=15 C | 5.1215 | 5.2338 | -2.19% | 1.2167 | 0.6093 | 0.5559 | 0.5274 |

This model is retained only if it clearly improves validation performance and keeps parameter magnitudes interpretable.
