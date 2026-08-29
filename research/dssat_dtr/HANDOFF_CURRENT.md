# DSSAT-DTR Urumqi Research Handoff

Last checkpoint: 2026-08-29 12:59 CST
Branch: `research/dssat-dtr-matrix`
Study station: NOAA `51463099999` / GHCN `CHM00051463`, Urumqi

## Current objective

Develop a Urumqi-specific improvement to DSSAT v4.8.5.0 `HTEMP`, derived from local residual mechanisms rather than copying an existing temperature model. Use official open-source DSSAT plus public Urumqi crop/weather data; no user local DSSAT run is currently required.

## Frozen software baseline — PASS

Formal source baseline:
- `DSSAT/dssat-csm-os`
- tag `v4.8.5.0`
- commit `0b91373806786b600d89ccfcfff78fa2f82cb26b`

Formal data baseline:
- `DSSAT/dssat-csm-data`
- tag `v4.8.5.0`
- commit `79cb5db71bbca186add92a6a9695866a09c8b51d`

Official regression case:
- `Maize/UFGA8201.MZX`
- weather `Weather/UFGA8201.WTH`
- executable `dscsm048`
- 6 maize treatments

The corrected GitHub Actions workflow has now passed the complete chain:
**exact source checkout -> compile/install -> matching official data -> UFGA8201 real execution -> `Summary.OUT`/`PlantGro.OUT` validation -> output inventory/hash -> repository snapshot**.

Frozen M0 snapshot:
`research/dssat_dtr/data/dssat485_m0_official/`

## Confirmed Urumqi mechanism

Formal calibration-only trigger:
`DTRc = 14.8 C`

Observed mechanism:
- below the threshold, official HTEMP is retained;
- morning cold bias increases gradually with DTR but has no strong breakpoint;
- once DTR reaches ~14-15 C, afternoon warm bias / hot-temperature persistence grows sharply;
- radiation state strongly modulates this high-DTR error.

Main-station validation previously showed high-DTR afternoon bias of roughly:
- low radiation: +10.14 C
- medium radiation: +4.69 C
- high radiation: +0.84 C

Thus the working mechanism is:
**DTR identifies the failure regime; radiation/cloudiness controls failure severity.**

## Statistical reference M10

M10 (`DTR + Kt` radiative-deficit gate) remains the performance reference.

Independent 2017-2024, DTR>=15 C:
- official RMSE 5.1215 C
- M10 RMSE 4.4196 C
- improvement 13.71%
- Bias +1.2167 -> +0.4936 C
- R2 0.5559 -> 0.6107

Robustness:
- improved 5/5 validation years containing high-DTR observations;
- paired day-block bootstrap improvement 95% CI = 10.76%-16.54%.

## DSSAT-native CLOUDS mechanism — retained

DSSAT v4.8.5.0 `SOLAR.for` already calculates:
`CLOUDS = clamp(1 - SRAD/SCLEAR, 0, 1)`

`HMET` already receives `CLOUDS`; therefore the radiation mechanism can be implemented without adding a new weather input or Kt calculation.

M12 used this native `CLOUDS` with the DTR trigger and obtained independent high-DTR RMSE:
`5.1215 -> 4.4332 C`, improvement **13.44%**, R2 `0.5559 -> 0.6163`.

DTR bins all improved:
- 15-<18 C: 4.8348 -> 4.2753 C
- 18-<20 C: 6.2900 -> 4.9198 C
- >=20 C: 7.6018 -> 6.1418 C (sparse extreme group)

This confirms that **DSSAT-native CLOUDS can replace the external Kt mechanism**.

## Critical correction: M12 additive formula is rejected for source code

A full 24-hour physical-shape test was run before Fortran modification. Although M12 has good pointwise RMSE, the direct additive shoulder subtraction is physically invalid.

Validation 2017-2024 high-DTR days:
- 130 days checked on a 0.05-h grid;
- rise non-monotonic on 113 days;
- fall non-monotonic on 52 days;
- below-daily-Tmin violations on 37 days;
- maximum Tmin undershoot >51 C;
- active-point correction P95 ~9.43 C, maximum ~18.53 C.

Therefore:
- **retain the DTR x CLOUDS mechanism**;
- **reject the M12 additive mathematical form**;
- do NOT write M12 directly into `HMET.for`.

## Current model under test: M13 monotonic CLOUDS shape warp

M13 keeps the same local mechanism but changes the mathematics to preserve physical shape.

Rules:
- DTR<=14.8 C: official HTEMP exactly;
- pre-peak segment: solar noon -> modeled Tmax;
- post-peak segment: modeled Tmax -> sunset;
- all segment endpoint temperatures remain exact anchors;
- normalized official segment temperature `q` is transformed by `q_new=q^p`;
- `p = 1 + k*(DTR-DTRc)*CLOUDS`, with k>=0;
- this construction guarantees monotonic rise/fall and prevents segment overshoot.

Only `k_pre` and `k_post` are fitted on 2000-2016; 2017-2024 remains independent validation.

M13 GitHub Actions run is currently in progress.

## Immediate next step

1. Read M13 independent validation and physical-shape results.
2. Retain M13 only if it has zero physical-shape violations and a meaningful high-DTR advantage; do not chase M10/M12 RMSE at the expense of physical validity.
3. If M13 passes, implement it in the frozen DSSAT v4.8.5.0 Weather pathway using existing `CLOUDS`.
4. Compile the patched source in the same environment and run the official UFGA8201 regression.
5. Then reconstruct the public Anningqu 2021-2022 maize experiment for Urumqi crop-response validation.

## Stop / ask-user conditions

Only stop for user input if:
- public Anningqu data lack a parameter that cannot be defensibly reconstructed;
- source-level M13 unexpectedly changes low-DTR conditions;
- crop-response propagation raises a major modeling choice rather than an implementation issue.
