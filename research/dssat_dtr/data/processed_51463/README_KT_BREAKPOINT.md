# Main 51463 high-DTR Kt breakpoint diagnosis

Only DTR >= 14.8 C May-Sep days are used. The formal Kt threshold must come from 2000-2016 calibration only.

## Calibration-only breakpoints

| Response | Kt breakpoint | slope below | slope above | SSE reduction vs linear | Delta AIC | linear zero crossing |
|---|---:|---:|---:|---:|---:|---:|
| Daily RMSE | 0.725 | -17.034 | 17.498 | 11.66% | -9.39 | 0.832 |
| Afternoon RMSE | 0.710 | -28.790 | 3.927 | 6.94% | -3.76 | 0.755 |
| Afternoon Bias | 0.705 | -29.163 | -0.807 | 6.11% | -2.81 | 0.745 |

## Validation-only stability diagnostic

- Afternoon-bias breakpoint: **0.530** Kt
- Daily-RMSE breakpoint: **0.515** Kt

The validation breakpoints are reported only to assess temporal stability; they are not allowed to set the model trigger.
