# M20 source bridge: M19 hourly correction -> CERES-Maize DTT

M0 = official DSSAT 4.8.5; M19 = weather-side hourly correction only; M20 = M19 plus neutral-delta DTT bridge.

| Weather | Model | Changed scenarios | Mean yield delta vs M0 (kg/ha) | Max abs yield delta | Mean anthesis delta (d) | Mean maturity delta (d) |
|---|---|---:|---:|---:|---:|---:|
| NATURAL | M19 | 0/10 | 0.00 | 0.00 | 0.00 | 0.00 |
| NATURAL | M20 | 10/10 | -0.50 | 4.00 | 0.00 | 0.00 |
| STRESS_DTR4 | M19 | 0/10 | 0.00 | 0.00 | 0.00 | 0.00 |
| STRESS_DTR4 | M20 | 10/10 | -9.80 | 224.00 | 0.00 | 0.20 |

Interpretation gate: M19=0 change confirms the original interface gap. M20>0 changed scenarios establishes source-level propagation through DTT. STRESS_DTR4 is a controlled causal stress test and is not an observed-climate validation.
