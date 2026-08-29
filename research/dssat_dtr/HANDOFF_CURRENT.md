# DSSAT-DTR Urumqi Research Handoff

Last checkpoint: 2026-08-29 15:44 CST
Branch: `research/dssat-dtr-matrix`
Study: Urumqi DSSAT v4.8.5.0 HTEMP improvement

## 1. Frozen DSSAT v4.8.5.0 baseline — END-TO-END PASS

Formal source/data baseline:
- `DSSAT/dssat-csm-os`, tag `v4.8.5.0`, commit `0b91373806786b600d89ccfcfff78fa2f82cb26b`
- `DSSAT/dssat-csm-data`, tag `v4.8.5.0`, commit `79cb5db71bbca186add92a6a9695866a09c8b51d`
- official regression experiment `Maize/UFGA8201.MZX`, 6 treatments, executable `dscsm048`

Untouched M0 completed: exact checkout -> compile/install -> matching official data -> real UFGA8201 execution -> `Summary.OUT`/`PlantGro.OUT` acceptance -> output hashes -> repository snapshot.
Frozen M0 outputs: `research/dssat_dtr/data/dssat485_m0_official/`.

## 2. Confirmed Urumqi mechanism

Primary sparse station: NOAA `51463099999` + GHCN `CHM00051463`.
Second dense station: NOAA `51463599999` (Diwopu), also within Urumqi.

Formal primary calibration-only failure threshold:
`DTRc = 14.8 C`.

Observed mechanism:
- below this regime official HTEMP performs much better;
- above ~14-15 C DTR, late-afternoon / sunset warm persistence error increases sharply;
- solar radiation / cloud state strongly modulates error magnitude;
- dynamic Tmax timing is not the main general mechanism;
- DSSAT v4.8.5.0 already computes `CLOUDS = clamp(1 - SRAD/SCLEAR,0,1)` in `SOLAR.for` and passes it to `HMET`, so no new WTH variable is required.

## 3. Statistical upper reference M10

Primary-station independent 2017-2024, DTR>=15 C:
- official RMSE 5.1215 C
- M10 RMSE 4.4196 C
- improvement 13.71%
- Bias +1.2167 -> +0.4936 C
- R2 0.5559 -> 0.6107
- 5/5 validation years improved
- day-block bootstrap improvement 95% CI 10.76%-16.54%.

M10 is a statistical reference only; its direct implementation is not the chosen source formula.

## 4. Rejected / intermediate forms

### M12 native-CLOUDS additive shoulder
High-DTR RMSE improved 13.44%, but full-curve QA failed severely: 113/130 rising non-monotonic, 52/130 falling non-monotonic, 37/130 below Tmin, max Tmin undershoot >51 C. Mechanism retained; additive formula permanently rejected.

### M13 monotonic power warp
0 physical violations; high-DTR improvement only 4.28%; k_pre hit upper bound. Rejected.

### M14 robust crossover monotonic warp
Calibration median-residual crossover H0=10.455 solar hour. 0 physical violations; high-DTR improvement 7.43%; k_pre still hit upper bound. Rejected as final family; do not continue tuning power-warp form.

## 5. Dense-station sunset-anchor mechanism — STRONGLY SUPPORTED

Dense Diwopu `51463599999`:
- 8,806 days with >=20 observed solar hours
- 3,790 May-Sep dense days
- HTEMP RMSE breakpoint replicated around 12.8 C calibration / 13.4 C validation.

Dense validation DTR 14.5-18 C warm bias grows through afternoon, reaching about +2.02 C at 19 solar h.

Dedicated sunset-anchor test compared official `T_PL(SNDN)` with the real observation within 45 min of sunset.

Dense calibration 2000-2016 fitted:
`delta_TS = alpha * max(0,DTR-14.8) * CLOUDS`
with
`alpha = 7.8094`.

Dense independent 2017-2024 high-DTR sunset validation:
- N=59 days
- raw sunset Bias +2.389 C
- raw RMSE 4.536 C
- corrected Bias +1.023 C
- corrected RMSE 3.725 C
- RMSE improvement 17.88%
- r(sunset error, DTR x CLOUDS)=0.429.

This directly supports an overly warm official sunset anchor under high-DTR cloudy/radiatively weak conditions.

## 6. M15 — PREFERRED SCIENTIFIC/SOURCE FORM

M15 freezes `alpha=7.8094` from dense Diwopu 2000-2016 and transfers it WITHOUT REFITTING to primary station `51463099999` 2017-2024.

Formula logic:
- DTR<=14.8 C or CLOUDS<=0: exact official HTEMP.
- official Tmax anchor unchanged.
- `TS1 = max(TMIN, TS0 - 7.8094*(DTR-14.8)*CLOUDS)`.
- modeled Tmax -> sunset: preserve official normalized cooling progress but rescale endpoint to TS1.
- night: retain official B=2.2 exponential structure, re-anchored to TS1 and TMIN.
- pre-peak daytime branch unchanged.

Primary cross-station independent validation 2017-2024:
- May-Sep RMSE 2.9469 -> 2.8241 C = 4.17%
- DTR>=15 RMSE 5.1215 -> 4.6783 C = 8.65%
- Bias +1.2167 -> +0.3784 C
- R2 0.5559 -> 0.6210
- complete 24-h physical violations: 0/130
- high-DTR years: 5/5 improved.

DTR bins:
- 15-<18: 4.8348 -> 4.4542 C
- 18-<20: 6.2900 -> 5.5425 C
- >=20: 7.6018 -> 6.7444 C (sparse extreme group).

Key hours:
- 17 h 3.951 -> 3.351 C
- 18 h 4.547 -> 2.922 C
- 20 h 2.509 -> 2.137 C.

M15 has less pointwise gain than M10 but substantially stronger evidence structure: second-station mechanism/parameter calibration -> first-station temporal validation, exact physical shape, and clean source implementation.

## 7. M16 sensitivity — NOT ADOPTED

Dense-station LOYO CV added a CLOUDS hinge and selected c0=0.020, alpha=8.4973.
Primary high-DTR improvement 8.86% versus M15 8.65%.
Only +0.21 percentage points while adding a near-zero threshold. Rejected for parsimony; keep as sensitivity analysis only.

## 8. M15 source integration into DSSAT v4.8.5.0 — FULL PASS

Files:
- `research/dssat_dtr/dssat485/apply_m15_htemp_patch.py`
- `research/dssat_dtr/dssat485/build_m15_fortran_unit.py`
- `.github/workflows/dssat485-m15-source.yml`

Successful formal workflow run: `33235735664`.

The deterministic patch:
- operates only on exact frozen v4.8.5.0 source anchors;
- handles legacy `HMET.for` text losslessly with Latin-1;
- leaves official `HTEMP` subroutine unchanged;
- adds a separate `HTEMP_DTRCLOUD` called immediately after official `HTEMP`.

Acceptance chain — all PASS:
1. exact v4.8.5 source/data checkout;
2. deterministic source patch;
3. source-extracted real Fortran unit test;
4. low-DTR exact no-change test;
5. high-DTR + CLOUDS=0 exact no-change test;
6. high-DTR cloudy bounded/late-cooling test;
7. full DSSAT CMake compile/install;
8. official `UFGA8201.MZX` six-treatment real execution;
9. `Summary.OUT` and `PlantGro.OUT` generated;
10. source/output snapshots and M0-vs-M15 diffs committed.

Frozen M15 source snapshot:
`research/dssat_dtr/data/dssat485_m15_source/`

UFGA8201 M15 outputs are not byte-identical to M0. Phenological dates shown in Summary remain unchanged in the regression case, while small biomass/yield/water/N differences confirm that the new temperature pathway is actually active. Florida is software propagation QA, not Urumqi scientific validation.

## 9. Anningqu Stage A controlled crop propagation — FULL SOFTWARE PASS, ZERO CORE RESPONSE

Formal workflow: `.github/workflows/anningqu-stageA-final.yml`, run `33240724580`.
After correcting DSSAT v4.8.5 fixed-width experiment and soil formats, all 20 real simulations PASS:
- 10 public Anningqu scenarios = 2021/2022 x five sowing dates;
- each scenario run with frozen M0 and M15;
- identical WTH/soil/management/cultivar within each pair;
- official proxy maize cultivar IB0035;
- `WATER=N`, `NITRO=N` to isolate the potential-growth temperature pathway.

Final Stage A output:
`research/dssat_dtr/data/anningqu/stageA_propagation/anningqu_stageA_m0_m15.csv`

Critical result:
- scenarios with any M0-M15 reported core crop-output change: **0/10**;
- HWAM, CWAM, HIAM and LAIX are identical for all ten paired scenarios;
- parsed ADAT/MDAT fields are also unchanged, although date-column parsing itself needs cleanup before publication use.

Independent thermal-activation check showed that M15 was not simply inactive:
- 2021 crop windows: roughly 7-15 M15 trigger days per scenario; maximum hourly correction about 3.93 C;
- 2022 crop windows: about 1 trigger day per scenario; maximum correction about 0.56 C.

Scientific interpretation:
**Under CERES-Maize potential-growth settings with water and N stress disabled, the M15-modified hourly HTEMP pathway does not propagate into the reported core phenology / biomass / grain-yield outputs.** This is an important negative mechanistic result and prevents falsely claiming crop improvement from the weather-layer gain alone. It does NOT invalidate M15's demonstrated hourly-temperature improvement.

The official Florida regression previously showed small M0-M15 biomass/yield/water/N differences under its full process configuration, indicating that the modified hourly-temperature path can affect other DSSAT process chains.

## 10. Current decision rule — DO NOT INVENT M17

Do not continue empirical temperature-formula tuning. M15 remains frozen.

Immediate next work:
1. audit DSSAT v4.8.5 source call chain from `HMET -> TAIRHR/TGRO` into CERES-Maize, soil water, ET, soil temperature, N and stress modules;
2. identify exactly which process(es) consume the M15-modified hourly temperatures;
3. only if the source audit supports it, run Anningqu Stage A2 with water/N process pathways enabled using one defensible common management setup for M0 and M15;
4. seek a clear process response (ET / soil water / stress / biomass / yield) that scales with 2021 strong activation and remains near-neutral in 2022 weak activation;
5. only after a propagation pathway is proven, compare with Tang 2024 observations. Crop accuracy is valid only if `|M15-observed| < |M0-observed|`; output change alone is not evidence of improvement.

## User-input / stop conditions

Do NOT ask the user to run DSSAT locally. Continue with GitHub and public data. Stop for user input only if:
- public sources cannot provide/reconstruct a defensible key Anningqu input;
- cultivar calibration requires a major choice among scientifically different strategies;
- M15 causes an unexpected source-level or crop-level behavior that requires a research-direction decision.
