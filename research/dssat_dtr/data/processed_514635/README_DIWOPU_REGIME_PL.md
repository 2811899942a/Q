# Dense Diwopu DTR-regime adaptive Parton-Logan test

## Calibration-only regime discovery
- Single station PL parameters: A=1.849, B=0.740, C=0.242.
- Calibration-period RMSE breakpoint after single-PL fitting: **12.7 C**.
- Calibration daily-RMSE slope below/above breakpoint: **-0.0282 / 0.3914 C per C DTR**.

## Regime-specific parameters
| Regime | A | B | C | Implied peak solar hour | Calibration points |
|---|---:|---:|---:|---:|---:|
| Low DTR <12.7 | 1.742 | 0.810 | 0.372 | 14.114 | 49046 |
| High DTR >=12.7 | 2.037 | 0.604 | 0.012 | 14.049 | 12144 |

## Independent 2017-2024 validation
- All May-Sep RMSE: single PL **1.7767 C** -> DTR-regime PL **1.7739 C** (0.16% additional improvement).
- High-DTR RMSE (>=12.7 C): single PL **2.2667 C** -> regime PL **2.2679 C** (-0.05% additional improvement).
- High-DTR bias: **0.0466 -> 0.1689 C**; R2: **0.8867 -> 0.8867**.

Interpretation: if high- and low-DTR optimum coefficients differ materially and the fixed calibration-only regime switch improves independent validation, this supports a parsimonious **DTR-state-adaptive Parton-Logan** formulation. If validation gain is small, fixed A/B/C are not the only structural limitation and a continuous shape parameterization is still needed.
