# DSSAT hourly temperature source audit

Updated: 2026-08-29

## Scope

This checkpoint audits the official DSSAT source path used to generate hourly air temperature before crop-output A/B validation.

Official repositories used:

- https://github.com/DSSAT/dssat-csm-os
- https://github.com/DSSAT/dssat-csm-data

Reference source file:

- `Weather/HMET.for`

Reference experiment files:

- `Maize/UFGA8201.MZX`
- `Maize/UFGA8201.MZA`

## 1. What HMET actually does

`HMET` loops through 24 within-day time steps and calls:

```fortran
CALL HTEMP(
 & DAYL, HS, SNDN, SNUP, TMAX, TMIN,
 & TAIRHR(H))
```

It then computes:

- `TAVG`: mean of the 24 hourly `TAIRHR` values;
- `TDAY`: mean of hourly `TAIRHR` during daylight;
- `TGRO(H) = TAIRHR(H)`.

Thus the reconstructed hourly series enters DSSAT as an explicit within-day temperature trajectory rather than only a reporting variable.

## 2. What HTEMP actually does

The official source documents `HTEMP` as the Parton and Logan (1981) hourly-temperature method.

Fixed parameters in the current source are:

```fortran
A = 2.0
B = 2.2
C = 1.0
```

Key timing equations are:

```text
MIN = SNUP + C
MAX = MIN + DAYL / 2 + A
```

Daylight temperature uses a sine function between the daily minimum and maximum:

```text
TAIRHR = TMIN + (TMAX - TMIN) * sin(...)
```

Night temperature uses exponential cooling from sunset toward the next minimum, controlled mainly by `B` and the available night length.

Direct `HTEMP` inputs are:

- `DAYL` — day length;
- `HS` — hour/time step;
- `SNDN` — sunset time;
- `SNUP` — sunrise time;
- `TMAX` — daily maximum temperature;
- `TMIN` — daily minimum temperature.

`SRAD` is used elsewhere in `HMET` for hourly radiation/PAR calculations and is not a direct input of `HTEMP`.

`DTR = TMAX - TMIN` is a derived diagnostic used by the proposed extreme-temperature screening logic. It is not an additional DSSAT weather-file input variable.

## 3. Important correction for the validation design

The official `HTEMP` routine itself contains no branch that says “use observed hourly temperatures when upper/lower limits are reasonable and regenerate a sine curve only when they are unreasonable.” `HTEMP` reconstructs the within-day curve from daily `TMAX/TMIN` plus astronomical timing every day.

Therefore any threshold/screening branch used in the research modification must be treated as an explicit custom extension and isolated from the original DSSAT 4.8.5 baseline.

This is critical for attribution:

```text
A = original DSSAT 4.8.5 HTEMP behavior
B = same 4.8.5 model + the finalized custom temperature correction
```

No crop, soil, management, cultivar, irrigation, fertilization, or daily weather inputs may change between A and B.

## 4. UFGA8201 validation targets recovered from official data

The official `UFGA8201.MZX` experiment contains six irrigation x nitrogen treatments. Official observations in `UFGA8201.MZA` provide the following endpoint targets:

| TRT | Treatment | HWAM observed (kg/ha) | ADAT | MDAT |
|---:|---|---:|---:|---:|
| 1 | RAINFED LOW NITROGEN | 2929 | 1982132 | 1982185 |
| 2 | RAINFED HIGH NITROGEN | 3130 | 1982132 | 1982185 |
| 3 | IRRIGATED LOW NITROGEN | 6850 | 1982132 | 1982185 |
| 4 | IRRIGATED HIGH NITROGEN | 11881 | 1982132 | 1982185 |
| 5 | VEG STRESS LOW NITROGEN | 6375 | 1982132 | 1982185 |
| 6 | VEG STRESS HIGH NITROGEN | 9344 | 1982132 | 1982185 |

These values are now frozen as the endpoint ground truth for the A/B crop-output validation.

## 5. Current validation chain

The final evidence chain is fixed as:

```text
custom trigger days
-> hourly TAIRHR change
-> temperature exposure during crop-sensitive stages
-> anthesis/maturity response
-> HWAM response
-> error relative to official UFGA8201 observations
```

Primary crop-output metric: HWAM RMSE across all six treatments.

Secondary metrics:

- HWAM MAE and bias;
- Willmott d;
- treatment-level absolute error;
- ADAT and MDAT day error;
- percentage reduction in RMSE from baseline to modified model.

## 6. Next checkpoint

1. Obtain/run the original 4.8.5 UFGA8201 baseline and preserve its `Summary.OUT`/`PlantGro.OUT`.
2. Restore the exact finalized custom temperature algorithm from the previous work product.
3. Run the modified executable with identical experiment inputs.
4. Automatically compare A and B against the frozen observations above.
5. Upload all numeric comparison tables and update the handoff MD immediately.
