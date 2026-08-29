# Urumqi calibration-only DTR asymmetric-curvature HTEMP

## Formal threshold

- DTR trigger = **14.8 C**, taken only from the 2000-2016 calibration-period AM-PM asymmetry breakpoint.
- 2017-2024 was not used to determine the threshold or curvature parameters.

## Fitted curvature response

- `k_rise = 0.000`
- `k_fall = 0.600`
- calibration affected points: rising=336, falling=93

For DTR>DTRc, rising and falling normalized temperature fractions are transformed by DTR-dependent powers. Tmin, modeled Tmax and modeled sunset temperature remain exact anchors.

## Independent validation 2017-2024

| Scope | Official RMSE | M5 RMSE | Improvement | Official Bias | M5 Bias | Official R2 | M5 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.9066 | 1.37% | 0.3368 | 0.3125 | 0.8029 | 0.8066 |
| DTR>=15 C | 5.1215 | 4.9802 | 2.76% | 1.2167 | 1.0698 | 0.5559 | 0.5642 |
| DTR<14.8 C | 2.2526 | 2.2526 | 0.00% by construction | 0.1583 | 0.1583 | 0.8764 | 0.8764 |

## Decision criterion

This structural form is preferred over additive shoulder subtraction only if it matches or exceeds the ~9% high-DTR RMSE improvement while avoiding very large empirical coefficients and preserving anchor continuity.
