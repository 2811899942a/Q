# Urumqi local DTR breakpoint diagnosis

Continuous segmented regression was fitted as `y = b0 + b1*DTR + b2*max(0,DTR-c)` over May-Sep days.

- Morning-bias best breakpoint: **15.0 C**
- Afternoon-bias best breakpoint: **14.6 C**
- AM-PM asymmetry-gap best breakpoint: **14.5 C**
- Daily-RMSE best breakpoint: **14.3 C**
- Four-diagnostic mean breakpoint: **14.60 C**
- Cross-diagnostic breakpoint spread: **0.70 C**

## Detailed all-period fits

| Diagnostic | Breakpoint | Slope below | Slope above | SSE reduction vs linear | Delta AIC (seg-linear) |
|---|---:|---:|---:|---:|---:|
| Morning bias | 15.0 | -0.1298 | -0.0905 | 0.03% | 3.27 |
| Afternoon bias | 14.6 | 0.0199 | 1.7337 | 12.33% | -372.92 |
| Afternoon-minus-morning bias | 14.5 | 0.1438 | 1.7874 | 11.98% | -361.32 |
| Daily RMSE | 14.3 | 0.0612 | 1.1047 | 15.16% | -467.32 |

## Stability rule

A local threshold is considered promising if the calibration- and validation-period breakpoints remain within 2 C and the segmented model materially improves SSE/AIC over a single linear relation.

This output is a diagnostic threshold estimate, not yet a physiological crop threshold and not yet a source-code switch value.
