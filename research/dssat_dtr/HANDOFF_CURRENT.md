# DSSAT-DTR Urumqi Research Handoff

Last checkpoint: 2026-08-29 12:55 CST
Branch: `research/dssat-dtr-matrix`
Study station: NOAA `51463099999` / GHCN `CHM00051463`, Urumqi

## Current task

Move the statistically established Urumqi HTEMP mechanism into a reproducible DSSAT source-level experiment. The user has formally chosen **DSSAT v4.8.5.0** as the sole source/data baseline. No local legacy DSSAT project is required at this stage; use official open-source DSSAT and public Urumqi crop/weather data.

## Frozen DSSAT v4.8.5.0 baseline

Source repository: `DSSAT/dssat-csm-os`
- tag: `v4.8.5.0`
- frozen source commit: `0b91373806786b600d89ccfcfff78fa2f82cb26b`

Data repository: `DSSAT/dssat-csm-data`
- tag: `v4.8.5.0`
- frozen data commit: `79cb5db71bbca186add92a6a9695866a09c8b51d`

Formal software regression case:
- `Maize/UFGA8201.MZX`
- weather: `Weather/UFGA8201.WTH`
- 6 maize treatments
- executable: `dscsm048`

Baseline lock file:
`research/dssat_dtr/dssat485/BASELINE_LOCK.md`

## M0 software regression status

The exact frozen DSSAT v4.8.5.0 source successfully compiled in GitHub Actions on Ubuntu 24.04 with GNU Fortran 13.3.0 and CMake. The official `UFGA8201.MZX` experiment also executed and printed all six treatment results.

First workflow run was marked failed only because the workflow additionally required `Overview.OUT`, which the run did not generate. `Summary.OUT` and `PlantGro.OUT` existed and passed. This was a test-harness criterion error, not a DSSAT model failure.

The workflow has now been corrected so that:
- `Summary.OUT` and `PlantGro.OUT` are the hard acceptance outputs;
- all generated `.OUT` files are inventoried and hashed;
- optional outputs such as `Overview.OUT` are copied only if they exist.

Second full M0 run is currently executing. Do not declare formal M0 END-TO-END PASS until this same corrected workflow completes successfully and commits the frozen output snapshot.

## Established Urumqi temperature mechanism

Weather/observation base:
- NOAA ISD `51463099999`, 2000-2024: 72,177 real sub-daily temperatures.
- GHCN-Daily `CHM00051463`: formal daily Tmax/Tmin/DTR.
- Original HTEMP benchmark: 55,756 matched points over 7,036 days.
- 2017-2024 May-Sep official HTEMP RMSE: 2.9469 C.
- 2017-2024 May-Sep DTR>=15 C official HTEMP RMSE: 5.1215 C.

Formal calibration-only DTR trigger:
`DTRc = 14.8 C`

Mechanism:
- below the threshold, official HTEMP is retained;
- morning cold bias rises gradually but does not show a strong structural breakpoint;
- above ~14-15 C DTR, afternoon warm bias / hot-shoulder persistence grows sharply;
- radiation state strongly modulates the magnitude of this high-DTR error.

Main-station high-DTR validation radiation strata previously showed afternoon Bias approximately:
- low radiation: +10.14 C
- middle radiation: +4.69 C
- high radiation: +0.84 C

## M10 statistical reference prototype

M10 uses an external/internal-computable clearness proxy `Kt=SRAD/Ra` and a continuous radiation-deficit gate.

Frozen independent validation (2017-2024, DTR>=15 C):
- Official RMSE: 5.1215 C
- M10 RMSE: 4.4196 C
- improvement: 13.71%
- Bias: +1.2167 -> +0.4936 C
- R2: 0.5559 -> 0.6107

Robustness:
- improvement in 5/5 validation years containing high-DTR observations;
- day-block bootstrap 95% CI for RMSE improvement: 10.76%-16.54%;
- probability of positive RMSE improvement: 100%.

M10 remains the statistical performance reference but is no longer the preferred source implementation because DSSAT already exposes a simpler native radiation variable.

## New DSSAT-native finding: CLOUDS can replace Kt

DSSAT v4.8.5.0 `Weather/SOLAR.for` already computes:

`SCLEAR = 0.77 * S0D`

and

`CLOUDS = clamp(1 - SRAD/SCLEAR, 0, 1)`

where `S0D` is the internally computed daily extraterrestrial irradiation. `HMET` already receives `CLOUDS`, `SRAD`, `XLAT`, `DEC`, `ISINB`, and `S0N`; only `HTEMP` currently ignores radiation state.

A source-native mechanism test, M12, retained:
- the frozen DTR trigger `DTRc=14.8 C`;
- the same normalized pre-peak and post-peak hot-shoulder bases;
- only two amplitudes fitted on 2000-2016;
- no new Kt threshold, no new weather variable, and no validation leakage.

M12 fitted coefficients:
- `beta_pre = 21.9025 C per C-DTR-excess per unit CLOUDS`
- `beta_post = 4.6759 C per C-DTR-excess per unit CLOUDS`

M12 independent validation 2017-2024:
- May-Sep RMSE: 2.9469 -> 2.7563 C = 6.47% improvement
- DTR>=15 RMSE: 5.1215 -> 4.4332 C = **13.44% improvement**
- high-DTR Bias: +1.2167 -> +0.6120 C
- high-DTR R2: 0.5559 -> 0.6163

M12 retains essentially all M10 performance while using an existing DSSAT variable.

DTR-bin RMSE:
- 15-<18 C: 4.8348 -> 4.2753 C (~11.6%)
- 18-<20 C: 6.2900 -> 4.9198 C (~21.8%)
- >=20 C: 7.6018 -> 6.1418 C (~19.2%; sparse extreme group)

Radiation/cloud strata on high-DTR validation days:
- LowCloud: 2.7820 -> 2.7650 C (essentially unchanged)
- MidCloud: 4.7324 -> 4.2457 C
- HighCloud: 7.0775 -> 5.7833 C

Key hours:
- 14 h RMSE: 4.0302 -> 3.4102 C
- 17 h RMSE: 3.9514 -> 3.3607 C
- night/late-evening values are unchanged by construction.

## Current decision

Promote **M12 DSSAT-native CLOUDS-gated HTEMP** as the preferred source-level candidate. Keep M10 as the statistical reference. The 0.27 percentage-point loss in high-DTR RMSE improvement (13.71% -> 13.44%) is outweighed by cleaner source integration, no new weather input, fewer derived quantities, and slightly higher validation R2.

## Immediate next steps

1. Complete corrected official v4.8.5.0 M0 end-to-end workflow and freeze output hashes.
2. After M0 PASS, patch only the v4.8.5.0 Weather temperature pathway:
   - pass existing `CLOUDS` into `HTEMP` or apply the correction immediately after original HTEMP within `HMET`;
   - preserve official HTEMP exactly when `DTR<=14.8 C`;
   - apply the two anchored hot-shoulder corrections only for high-DTR daylight periods.
3. Compile the modified source in the same GitHub Actions environment.
4. Run source-level invariants and the official `UFGA8201.MZX` regression case. Florida is a software non-regression test, not Urumqi scientific validation.
5. Rebuild a Urumqi maize experiment from public data (priority: Anningqu 2021-2022) and public weather/SRAD. No user local run is required unless a later platform-specific deployment is needed.
6. Compare official v4.8.5.0 versus modified HTEMP for thermal exposure, phenology, biomass/LAI where available, and yield.

## Stop conditions

Do not resume broad temperature-formula searching. Stop and ask the user only if:
- a public-data gap prevents a defensible Anningqu DSSAT reconstruction;
- source integration changes unexpectedly affect non-high-DTR conditions;
- crop propagation requires a major modeling choice rather than a technical implementation choice.
