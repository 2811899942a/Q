# Urumqi DTR-triggered signed-skew HTEMP

- Formal trigger from calibration only: **DTR > 14.8 C**
- `beta_rise = 1.5515 C/C-excess`
- `beta_fall = 3.0784 C/C-excess`
- Calibration affected points: rise=336, fall=93

The rising correction is sign-changing by construction: positive in early warming, negative in late warming, and zero at Tmin, the mid-rise crossing, and Tmax. The falling correction is negative in the interior and zero at Tmax and sunset.

## Independent validation 2017-2024

| Scope | Official RMSE | M6 RMSE | Improvement | Official Bias | M6 Bias | Official R2 | M6 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.8413 | 3.58% | 0.3368 | 0.2492 | 0.8029 | 0.8111 |
| DTR>=15 C | 5.1215 | 4.7480 | 7.29% | 1.2167 | 0.6869 | 0.5559 | 0.5644 |

Decision: retain only if validation improvement is competitive with the previous 9.07% exploratory shoulder model while coefficients remain interpretable and no low-DTR weather is changed.
