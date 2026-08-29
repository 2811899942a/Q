# DSSAT-DTR Xinjiang Research Handoff

Last material checkpoint: 2026-08-29 20:28 CST
Branch: `research/dssat-dtr-matrix`
Study: DSSAT v4.8.5 CERES-Maize hourly-temperature / extreme-day thermal-time improvement

## 1. Frozen scientific method

Do not retune the temperature method or Xinyu66 cultivar coefficients to force crop-output gains.

### M15 hourly-temperature refinement
- DTR threshold: `DTRc = 14.8 C`
- sunset correction coefficient: `alpha = 7.8094`
- if `DTR <= 14.8 C` or `CLOUDS <= 0`, behavior is exactly official HTEMP;
- pre-peak daytime branch unchanged;
- official Tmax anchor unchanged;
- modeled Tmax -> sunset branch is rescaled to a corrected sunset anchor;
- night branch retains official exponential structure.

Independent Urumqi primary-station 2017-2024 validation:
- May-Sep hourly RMSE: 2.9469 -> 2.8241 C (4.17% improvement)
- DTR>=15 C RMSE: 5.1215 -> 4.6783 C (8.65% improvement)
- Bias: +1.2167 -> +0.3784 C
- R2: 0.5559 -> 0.6210
- complete 24-h physical violations: 0/130
- 5/5 high-DTR validation years improved.

M15 is frozen.

## 2. DSSAT v4.8.5 source integration

Frozen upstream:
- `DSSAT/dssat-csm-os` tag `v4.8.5.0`
- `DSSAT/dssat-csm-data` tag `v4.8.5.0`

M15 source integration and real DSSAT compile/run passed. Official `HTEMP` is preserved and a separate correction routine is called after it. Official UFGA8201 six-treatment regression produced valid `Summary.OUT` and `PlantGro.OUT` and confirmed the modified hourly-temperature path is active.

## 3. Crop propagation status before Shihezi

Anningqu controlled potential-growth Stage A:
- 10 scenarios (2021/2022 x five sowing dates)
- M0 vs M15
- WATER=N, NITRO=N
- M15 trigger days were present, but reported HWAM/CWAM/HIAM/LAIX did not change.

Interpretation: the hourly-temperature modification does not automatically alter CERES core crop output under potential-growth settings. Full process/stress pathways matter.

## 4. Shihezi real Xinyu66 case

Target case:
- Shihezi University modern water-saving irrigation experimental station
- 2019 calibration year
- 2020 independent validation year
- cultivar Xinyu66
- treatments W1-W4

Frozen published Xinyu66 coefficients:
- P1=104.7
- P2=1.824
- P5=957.2
- G2=671
- G3=15.82
- PHINT=42.97

Source-supported field inputs recovered:
- longitude 85.9964 E
- latitude 44.3244 N
- elevation 412 m
- sowing 2019-05-03 / 2020-05-05
- Guo text: 25 cm plant spacing, 30/60 cm narrow/wide rows, 4 cm sowing depth, 1.45 m mulch
- W1/W2/W3/W4 irrigation totals 487.5/525/562.5/600 mm
- 10 irrigation events
- Guo soil hydraulic layers recovered
- ecotype `IB0001` is source-supported through the published initial cultivar-coefficient match.

Published original CERES yield RRMSE:
- 2019: ~6.52%
- 2020: ~5.69%

## 5. Three-arm definition

All arms use identical reconstructed crop/soil/management/weather inputs.

- `M0`: official DSSAT v4.8.5 CERES baseline.
- `H0TT`: official HMET/TGRO hourly temperature inserted into CERES existing extreme-day 24-h DTT branch.
- `M15TT`: frozen M15 hourly refinement + the same TGRO-based extreme-day DTT integration.

No arm-specific recalibration is permitted.

## 6. V4 real-yield run — VALID execution, baseline reproduction FAIL

Workflow:
`.github/workflows/shihezi-real-yield-v4.yml`
Run: `33246786517` (success)

All 24 simulations completed: 3 arms x 2 years x 4 treatments.
`Summary.OUT` HWAM parsing was audited against raw rows and is valid.

### 2019
| Arm | RMSE kg/ha | RRMSE % | MAE kg/ha | Bias kg/ha |
|---|---:|---:|---:|---:|
| M0 | 2069.2 | 18.602 | 1644.8 | +1644.8 |
| H0TT | 1944.4 | 17.480 | 1484.8 | +1484.8 |
| M15TT | 2068.8 | 18.598 | 1644.5 | +1644.5 |

### 2020 independent validation
| Arm | RMSE kg/ha | RRMSE % | MAE kg/ha | Bias kg/ha |
|---|---:|---:|---:|---:|
| M0 | 6684.8 | 60.771 | 6603.0 | +6603.0 |
| H0TT | 5985.5 | 54.414 | 5916.2 | +5916.2 |
| M15TT | 6267.0 | 56.973 | 6179.2 | +6179.2 |

2020 provisional contrasts:
- H0TT vs M0 relative RRMSE reduction: 10.461%
- M15TT vs M0 relative reduction: 6.250%
- M15TT vs H0TT: 4.703% worse locally
- maximum arm-induced HWAM shift: 934 kg/ha

These numbers prove crop propagation is material in this real-cultivar reconstruction. They do not prove predictive accuracy improvement because M0 fails the published baseline reproduction gate badly: 60.771% vs 5.69%.

Example raw M0 2020 W1 output confirms the large value is genuine model output: HWAM ~17,591 kg/ha.

## 7. V5 density sensitivity

A same-trial source conflict was tested:
- Guo text-derived equivalent density: 8.89 plants/m2
- Meng same-trial method: 8.25 plants/m2

V5 with 8.25 plants/m2 produced 2020 RRMSE:
- M0 58.945%
- H0TT 52.483%
- M15TT 55.230%

Density changes M0 by only ~1.83 percentage points and is not the dominant error source. Formal Guo reconstruction remains at 8.89 plants/m2 unless stronger source evidence changes the decision.

## 8. Main M0 reproduction gaps recovered

The current V4 weather is provisional NASA POWER-only forcing. Published thesis information indicates:
- growing-season precipitation totals ~96.45 mm (2019), 119.88 mm (2020)
- mean total radiation ~19.8 MJ m-2 d-1

V4 Summary.OUT reports approximately:
- 2019 SRADA 23.3, PRCP 83.3 mm
- 2020 SRADA 24.2, PRCP 103.1 mm

Source-recovered Guo Fig.2-2 temperature series is available under:
`research/dssat_dtr/data/shihezi_real_case/guo_weather_daily_v1/`

Current dominant unresolved common-arm inputs:
1. exact original 2019/2020 CMA + NASA WTH;
2. exact fertilizer schedule and N initialization;
3. exact initial soil-water profile;
4. raw numerical observed yields (current targets digitized from figure, ~+/-100 kg/ha uncertainty).

## 9. Nitrogen diagnostics

Same station / same Xinyu66 later experiment (2021-2022) reports a management clue:
- urea 280 kg/ha at 46% N = 128.8 kg N/ha
- monoammonium phosphate 100 kg/ha
- potassium sulfate 60 kg/ha
- fertigation with irrigation.

This later schedule is diagnostic evidence only, not accepted as the exact 2019/2020 input.

### First N run — invalid rate response

The first finite-N run produced a common ~4.73 t/ha because the treatment row had `MF=0`. The fertilizer block was present but not linked to the treatment. This run is retained only as an engineering failure diagnosis.

### Corrected V2 — VALID sensitivity/root-cause diagnostic

The corrected V2 uses `MF=1`, `NITRO=Y`, `FERTI=R`. DSSAT confirms different applied-N totals:
- N64_SPLIT: NI#M=9, NICM ~54 kg N/ha
- N129_SPLIT: NI#M=9, NICM ~117 kg N/ha
- N193_SPLIT: NI#M=9, NICM ~171 kg N/ha
- N129_BASAL: NI#M=1, NICM ~129 kg N/ha

2020 M0 results:

| Scenario | RMSE kg/ha | RRMSE % | MAE kg/ha | Bias kg/ha | Mean HWAM kg/ha |
|---|---:|---:|---:|---:|---:|
| UNLIMITED | 6684.8 | 60.771 | 6603.0 | +6603.0 | 17603.0 |
| N64_SPLIT | 3818.0 | 34.709 | 3709.2 | -3709.2 | 7290.8 |
| N129_SPLIT | 2737.9 | 24.890 | 2600.2 | -2600.2 | 8399.8 |
| N193_SPLIT | 1860.0 | 16.909 | 1598.2 | -1598.2 | 9401.8 |
| N129_BASAL | 2684.4 | 24.403 | 2513.2 | -2513.2 | 8486.8 |

Best finite-N diagnostic: N193_SPLIT, 16.909% RRMSE versus 60.771% in the unlimited-N reconstruction, a 72.17% relative reduction.

Interpretation: nitrogen representation explains a large portion of the M0 discrepancy. N193_SPLIT remains a diagnostic bracket because exact 2019-2020 fertilizer management has not yet been recovered. The remaining 16.909% still misses the published 5.69% baseline substantially.

## 10. Weather source-gap diagnostics V1-V3

### V1 — withdrawn from attribution

RAIN_MATCH, SRAD_19P8 and WEATHER_BOTH returned identical HWAM and identical `Summary.OUT` SRADA/PRCP as BASE. Requested WTH changes did not demonstrably propagate into DSSAT.

### V2 — engineering gate failure

The workflow used an arbitrary >=300 WTH-row requirement, while the reconstructed WTH contains 184 valid daily records. It stopped before producing a weather response. This failure has no scientific interpretation.

Checkpoint: `CHECKPOINT_20260829_2016_WEATHER_V2_ROWCOUNT_FAILURE.md`.

### V3 — canonical source copy still failed post-run propagation

Run `33251591460` rebuilt the V4 case successfully and audited independent copied WTH files, valid-row counts, hashes and the expected `/DSSAT48/Weather` path. DSSAT then failed the hard post-run gate:

`POST-RUN FAIL: RAIN_MATCH PRCP unchanged for 2019`.

The leading runtime-path hypothesis is that copied installed trees preserve the original CMake installation-prefix path (`/tmp/run_M0`) in DSSATPRO configuration. Thus a copied scenario can still read the canonical BASE weather path.

No V3 weather sensitivity result is accepted.

Checkpoint: `CHECKPOINT_20260829_2028_WEATHER_V3_RUNTIME_PATH_FAILURE.md`.

### V4 correction now triggered

Workflow: `.github/workflows/shihezi-m0-weather-gap-diagnostic-v4.yml`.

V4 keeps one canonical `/tmp/run_M0` installation, audits DSSATPRO, edits `/tmp/run_M0/Weather/SHIH1901.WTH` and `SHIH2001.WTH` in place, verifies hashes immediately before every run, and requires `Summary.OUT` SRADA/PRCP to move in the requested direction. This removes copied-install path ambiguity.

## 11. Public station-weather recovery

A 51356 public-station probe was completed in run `33251318548`.

- ISD station-history metadata returned a 51356/513560 match.
- GSOD `51356099999` daily files for 2019 and 2020 returned HTTP 404.
- GHCN-Daily `CHM00051356.dly` returned HTTP 404.

No daily NOAA/GHCN series was recovered through those identifiers. This does not establish absence from every archive or historical identifier.

Existing POWER May-August audit:
- 2019: mean Tmax 31.485 C, Tmin 18.046 C, rain 93.41 mm, SRAD 22.949 MJ m-2 d-1.
- 2020: mean Tmax 31.651 C, Tmin 18.288 C, rain 118.84 mm, SRAD 23.622 MJ m-2 d-1.

Precipitation magnitude is already close to the thesis-scale values, especially in 2020. Solar radiation remains the clearer magnitude discrepancy.

Checkpoint: `CHECKPOINT_20260829_2012_STATION_51356_PROBE.md`.

## 12. Adjacent same-station fertilizer management source

Wang et al. (2019), Water 11(3):472, DOI `10.3390/w11030472`, describes a 2018 maize experiment at the same Shihezi University water-saving experimental-station system.

Recovered management:
- P2O5 120 kg/ha base fertilizer;
- K2O 90 kg/ha base fertilizer;
- 20% of urea used as base fertilizer;
- subsequent fertilizer applied with irrigation;
- 10 irrigation/fertigation events.

Stage fertigation shares:
- seedling: 1 event / 10%;
- jointing: 3 / 20%;
- tasseling: 3 / 45%;
- filling: 2 / 15%;
- maturity: 1 / 10%.

This provides a defensible adjacent-source timing shape. The full-season urea/N total remains unresolved from that source, so the schedule is diagnostic only.

A same-total timing workflow is now running: `.github/workflows/shihezi-m0-fertilizer-timing-diagnostic.yml`. It compares equal 10-way splitting against 20% basal + same-station 2018 stage allocation at the already-tested nominal N totals 128.8 and 193.2 kg/ha. Total N is held fixed to isolate timing leverage.

Checkpoint: `CHECKPOINT_20260829_2024_SAME_STATION_2018_FERTILIZER_SOURCE.md`.

## 13. Soil organic-matter unit diagnostic

Guo Table 2-1 reports top-layer OM values such as `1.485` with units typed g/kg, while a later same-station Xinyu66 experiment reports topsoil OM around 14.12 g/kg. A diagnostic hypothesis treats the Guo values as percent OM (e.g. 1.485% = 14.85 g/kg) and converts to DSSAT SLOC by OM/1.724.

The first workflow failed during V4-base reconstruction and produced no science. Failure checkpoint: `CHECKPOINT_20260829_2020_SOIL_OM_DIAGNOSTIC_FAILURE.md`.

Corrected workflow `.github/workflows/shihezi-m0-soil-om-diagnostic-v2.yml`, run `33251645551`, is currently running. It audits active SLOC, MF=1 and NICM before interpreting any yield response.

This remains a source-interpretation diagnostic; it cannot enter the formal reconstruction solely because it lowers yield error.

## 14. Immediate queue

1. Finish weather V4 with canonical in-place WTH propagation audit.
2. Finish soil-OM V2 and read numeric RRMSE changes.
3. Finish same-station fertilizer-timing diagnostic and isolate timing effect at fixed total N.
4. Use the three diagnostics to rank the remaining M0 source gaps.
5. Continue recovering exact 2019-2020 fertilizer schedule, initial soil water and weather construction.
6. Only after a source-supported M0 approaches the published 2020 ~5.69% RRMSE, rerun the final M0/H0TT/M15TT three-arm comparison and quantify the true crop-output improvement.

## 15. Hard scientific rules

- Do not retune M15 (`DTRc=14.8 C`, `alpha=7.8094`).
- Do not retune Xinyu66 coefficients against validation yield.
- Do not describe V4 H0TT/M15TT percentage reductions as final real-yield accuracy gains while M0 reproduction fails.
- All common-arm reconstruction changes must be source-supported or explicitly labeled diagnostic.
- After every material result, failure, method switch or major decision, write a GitHub checkpoint and update this handoff before continuing.
- Do not ask the user to run DSSAT locally.
