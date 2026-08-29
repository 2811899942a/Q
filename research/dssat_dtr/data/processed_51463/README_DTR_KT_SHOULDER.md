# Urumqi DTR-triggered Kt-modulated hot-shoulder HTEMP

- Formal DTR trigger: **>14.8 C**, calibration-only
- Kt = SRAD/Ra; calibration mean Kt = **0.5771**
- Pre-peak amplitude: `excess*(10.3664 + -15.1687*(Kt-Ktmean))`
- Post-peak amplitude: `excess*(2.1614 + 0.4729*(Kt-Ktmean))`
- Calibration active points: pre=95, post=93

## Independent validation 2017-2024
| Scope | Official RMSE | M9 RMSE | Improvement | Official Bias | M9 Bias | Official R2 | M9 R2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| May-Sep | 2.9469 | 2.7643 | 6.20% | 0.3368 | 0.1847 | 0.8029 | 0.8191 |
| DTR>=15 C | 5.1215 | 4.4638 | 12.84% | 1.2167 | 0.2961 | 0.5559 | 0.5936 |

Benchmark to beat: exploratory DTR-only two-sided shoulder = 9.07% high-DTR RMSE improvement. A strong result should exceed this while keeping DTR<=14.8 exactly unchanged.
