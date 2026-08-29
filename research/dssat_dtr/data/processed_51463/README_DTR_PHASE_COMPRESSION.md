# DTR-triggered post-peak phase compression — first structural test

## Locally diagnosed trigger
- DTR breakpoint fixed before this fit: **14.5 C**.
- Only one new structural parameter was calibrated: **gamma = 0.150 per C DTR excess**.
- Calibration: 2000-2016 May-Sep.
- Independent validation: 2017-2024 May-Sep.

## Formula
For `DTR > 14.5 C` and solar time after the original PL temperature peak:

`theta_new = pi/2 + [1 + gamma*(DTR-14.5)] * (theta-pi/2)`

The pre-peak branch remains unchanged. The modified sunset temperature is passed into the existing nighttime exponential branch, so the curve remains continuous at sunset.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|
| M0 DSSAT official | 2.9469 | 5.1215 | 1.2167 | 0.5559 |
| M1 PL-XJ-BAL | 2.8092 | 4.8188 | 0.9440 | 0.5690 |
| M2 DTR-PC | 2.8865 | 4.9105 | 0.6024 | 0.5773 |

M2 RMSE improvement vs official: **2.05%** for all May-Sep and **4.12%** for DTR>=15 C.

## Afternoon 14-18 solar time validation
- Official RMSE / Bias: **4.0106 / 2.3338 C**.
- DTR-PC RMSE / Bias: **3.8437 / 2.2053 C**.

## Decision rule
This M2 is worth advancing only if it materially reduces independent high-DTR and afternoon errors without degrading low-DTR days (which are mathematically unchanged because the trigger is inactive below 14.5 C). It remains a temperature-reconstruction experiment, not yet evidence of improved DSSAT crop yield or phenology.
