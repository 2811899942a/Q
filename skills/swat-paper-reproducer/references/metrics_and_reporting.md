# Metrics and Reporting

## Metrics

Use the same formulas consistently:

- `R2`: squared Pearson correlation between observed and simulated flow.
- `NSE`: `1 - sum((sim - obs)^2) / sum((obs - mean(obs))^2)`.
- `PBIAS`: `100 * sum(obs - sim) / sum(obs)`. Positive PBIAS means the model underestimates flow.
- `KGE`: `1 - sqrt((r-1)^2 + (alpha-1)^2 + (beta-1)^2)` with `alpha = std(sim)/std(obs)` and `beta = mean(sim)/mean(obs)`.
- `RMSE`: root mean square error.
- `MAE`: mean absolute error.

## Output Tables

For each evaluation stage, create a paired table with:

```text
date, year, month, reach, area_km2, q_sim_m3s, q_obs_m3s
```

## Plots

Generate at least:

1. Time-series plot of observed vs simulated monthly flow.
2. Scatter plot of observed vs simulated flow with a 1:1 line and metrics annotation.

## Report Structure

Use this concise stage report:

```text
Model version:
Input changes:
Outlet reach and area:
Period:
Record count:
Metrics:
Main diagnosis:
Next action:
```

## Interpretation Language

- “Workflow run” means SWAT executed and output files exist.
- “Hydrologically meaningful baseline” means real precipitation/temperature are used and metrics are plausible.
- “Calibrated result” means SWAT-CUP produced a complete iteration and best parameters were applied or reported.
- “Validated result” means best calibration parameters were applied to an independent validation period.
