# Original DSSAT HTEMP baseline — Urumqi 51463

## Data and alignment

- Daily Tmax/Tmin: NOAA GHCN-Daily `CHM00051463`.
- Sub-daily observations: NOAA ISD `51463099999`.
- Observation timestamps converted from CST (UTC+8) to **local apparent solar time** using longitude 87.6167 E before comparison.
- DSSAT `DAYLEN` and `HTEMP` equations are reproduced from the official open-source code.
- Parton-Logan parameters kept at official DSSAT defaults: **A=2.0, B=2.2, C=1.0**.
- ISD suspect/erroneous temperature QC codes excluded: ['2', '3', '6', '7'].
- Matched prediction-observation points: **55,756**.
- ISD records excluded by suspect/erroneous QC: **42**.
- Source QC flag counts before filtering: `1:72135, 2:42`.

## Core metrics

| Scope | N points | N days | RMSE C | MAE C | MBE C | R2 |
|---|---:|---:|---:|---:|---:|---:|
| All | 55756 | 7036 | 2.6852 | 1.7606 | 0.2655 | 0.9662 |
| May-Sep | 22720 | 2867 | 2.5808 | 1.5881 | 0.4195 | 0.8391 |
| DTR >=15 C | 3346 | 426 | 5.5527 | 4.0152 | 0.8296 | 0.8388 |
| May-Sep DTR >=15 C | 1664 | 210 | 5.3844 | 3.7193 | 1.3562 | 0.5429 |

## Does HTEMP error increase with DTR?

Daily RMSE versus formal GHCN DTR:

- All seasons Pearson r = **0.4166**; Spearman rho = **0.2514**; OLS slope = **0.2017 C RMSE per 1 C DTR**.
- May-Sep Pearson r = **0.3524**; Spearman rho = **0.2155**; OLS slope = **0.2238 C RMSE per 1 C DTR**.
- Automated first-pass verdict: **DTR_ERROR_SIGNAL_SUPPORTED**.

The verdict is only a diagnostic gate. A source-code modification should be pursued after inspecting DTR-bin errors, time-of-day errors, and independent-year calibration/validation, rather than from the correlation alone.

## DSSAT source reproduction

`Weather/SOLAR.for::DAYLEN`

- `DEC = -23.45*COS(2*PI*(DOY+10)/365)`
- `DAYL = 12 + 24*ASIN(TAN(DEC)*TAN(XLAT))/PI`
- `SNUP = 12 - DAYL/2`
- `SNDN = 12 + DAYL/2`

`Weather/HMET.for::HTEMP`

- Parton & Logan (1981)
- fixed `A=2.0, B=2.2, C=1.0`
- daytime sine curve + nighttime exponential decay

## Interpretation rule

The strongest support for the proposed DSSAT-DTR study would be a reproducible rise in RMSE/MAE with formal DTR, concentrated in identifiable solar-time periods (for example afternoon peak timing or nighttime cooling), and repeated within May-Sep. If that pattern is absent, the source-code innovation hypothesis must be narrowed before modifying DSSAT.
