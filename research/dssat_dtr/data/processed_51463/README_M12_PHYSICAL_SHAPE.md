# M12 physical-shape diagnostic

No parameter was refitted. The frozen M12 coefficients were applied to complete 24-hour curves on a 0.05-h grid.

## Validation checkpoint correction magnitudes (2017-2024, DTR>=15 C)
- active observed checkpoints: **245**
- all-branch correction P50/P90/P95/P99/max: **1.05 / 6.61 / 9.43 / 16.34 / 18.53 C**
- pre-peak correction P95/max: **9.83 / 18.53 C**
- post-peak correction P95/max: **8.17 / 14.50 C**

## Full-curve physical checks
| Period | High-DTR days | Rise non-monotonic | Fall non-monotonic | Curve below daily Tmin | Max rise reversal per 0.05h | Max fall reversal per 0.05h | Max Tmin undershoot |
|---|---:|---:|---:|---:|---:|---:|---:|
| Calibration 2000-2016 | 95 | 67 | 26 | 23 | 10.039 | 1.483 | 131.905 C |
| Validation 2017-2024 | 130 | 113 | 52 | 37 | 4.575 | 0.733 | 51.369 C |

Automated verdict: **PHYSICAL_SHAPE_VIOLATIONS_PRESENT**.

If violations are present, M12 remains valid as mechanism/statistical evidence but the source implementation must use a monotonic shape transformation rather than direct additive shoulder subtraction.
