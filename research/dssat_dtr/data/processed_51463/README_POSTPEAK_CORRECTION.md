# Urumqi threshold-triggered post-peak correction

## Formula

For DTR <= 14.5 C, original DSSAT HTEMP is unchanged.
For DTR > 14.5 C and only between the DSSAT daytime peak and sunset:

`T_new = T_PL - alpha*(DTR-14.5)*4*u*(1-u)`

where `u=(t-tpeak)/(sunset-tpeak)`. The correction is exactly zero at peak and sunset.

## Calibration

- Period: 2000-2016 May-Sep
- One fitted parameter only: alpha
- Selected alpha: **1.500**

## Independent validation 2017-2024

| Scope | Official RMSE | New RMSE | Improvement | Official Bias | New Bias |
|---|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.8757 | 2.42% | 0.3368 | 0.2844 |
| DTR>=15 C | 5.1215 | 4.8744 | 4.82% | 1.2167 | 0.9059 |

## Interpretation

This is a deliberately minimal mechanism test. A meaningful independent-validation improvement would support the hypothesis that excessive post-peak thermal persistence is a real component of Urumqi HTEMP error. If improvement is weak, the mechanism must be revised before any Fortran source modification.
