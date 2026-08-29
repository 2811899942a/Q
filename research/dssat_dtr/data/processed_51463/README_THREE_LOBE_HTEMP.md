# Urumqi calibration-only three-lobe DTR-adaptive HTEMP

- Trigger: **DTR > 14.8 C** (calibration period only)
- Morning warming coefficient: **beta_m=0.0000 C/C-excess**
- Late pre-peak shoulder cooling coefficient: **beta_p=3.9907 C/C-excess**
- Post-peak persistence cooling coefficient: **beta_f=3.0784 C/C-excess**

All three terms vanish at physical branch anchors; low-DTR weather is unchanged.

## Independent validation 2017-2024

| Scope | Official RMSE | M7 RMSE | Improvement | Official Bias | M7 Bias | Official R2 | M7 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.8573 | 3.04% | 0.3368 | 0.0862 | 0.8029 | 0.8063 |
| DTR>=15 C | 5.1215 | 4.8070 | 6.14% | 1.2167 | -0.2996 | 0.5559 | 0.5342 |

Retain only if it improves on the 9.07% exploratory two-sided shoulder benchmark with stable, interpretable coefficients.
