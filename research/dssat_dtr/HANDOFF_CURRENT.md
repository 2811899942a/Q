# DSSAT-DTR Xinjiang Research Handoff

Last material checkpoint: 2026-08-29 20:45 CST
Branch: `research/dssat-dtr-matrix`
Study: DSSAT v4.8.5 CERES-Maize hourly-temperature / extreme-day thermal-time improvement

## 1. Frozen scientific method

M15 is frozen and must not be retuned to fit crop yield.

- DTR threshold `DTRc = 14.8 C`
- sunset correction `alpha = 7.8094`
- `DTR <= 14.8 C` or `CLOUDS <= 0`: official HTEMP exactly
- pre-peak daytime branch unchanged
- official Tmax anchor unchanged
- post-peak to sunset branch corrected
- official night exponential structure retained

Independent Urumqi 2017-2024 validation:
- May-Sep hourly RMSE 2.9469 -> 2.8241 C (4.17% reduction)
- DTR>=15 C RMSE 5.1215 -> 4.6783 C (8.65% reduction)
- Bias +1.2167 -> +0.3784 C
- R2 0.5559 -> 0.6210
- physical violations 0/130 complete 24-h days
- 5/5 high-DTR validation years improved

DSSAT upstream frozen at official v4.8.5.0.

## 2. Frozen Shihezi Xinyu66 real case

- Shihezi University modern water-saving irrigation experimental station
- Xinyu66 maize
- 2019 calibration; 2020 independent validation
- W1-W4 irrigation treatments
- location ~85.9964 E, 44.3244 N, elevation 412 m
- sowing 2019-05-03 / 2020-05-05
- 25 cm plant spacing; 30/60 cm narrow/wide rows; 4 cm sowing depth; 1.45 m mulch
- formal density 8.89 plants/m2
- irrigation totals 487.5 / 525 / 562.5 / 600 mm
- 10 irrigation events
- Guo hydraulic soil profile
- ecotype IB0001

Frozen Xinyu66 coefficients:
- P1=104.7
- P2=1.824
- P5=957.2
- G2=671
- G3=15.82
- PHINT=42.97

Published original CERES yield RRMSE target:
- 2019 ~6.52%
- 2020 ~5.69%

## 3. Three-arm definitions

- M0: official DSSAT v4.8.5 CERES baseline
- H0TT: official HMET/TGRO hourly temperature coupled into CERES extreme-day 24-h DTT
- M15TT: frozen M15 hourly temperature + the same DTT pathway

No arm-specific calibration.

## 4. Real-yield V4 propagation result

Workflow `.github/workflows/shihezi-real-yield-v4.yml`, run `33246786517` PASS.

2019 RRMSE:
- M0 18.602%
- H0TT 17.480%
- M15TT 18.598%

2020 RRMSE:
- M0 60.771%
- H0TT 54.414%
- M15TT 56.973%

Provisional 2020 contrasts:
- H0TT relative RRMSE reduction vs M0 10.461%
- M15TT relative RRMSE reduction vs M0 6.250%
- maximum arm-induced HWAM shift 934 kg/ha

This proves hourly-temperature/DTT changes can propagate materially to yield. Final predictive-accuracy claims remain blocked by the common M0 reconstruction gap.

## 5. Small / negligible common-input levers already closed

### Density
8.25 vs formal 8.89 plants/m2 changes 2020 M0 RRMSE only ~1.83 percentage points. Keep 8.89.

### Fertilizer timing shape
Same-station adjacent 2018 source (Wang et al. 2019, Water 11(3):472, DOI 10.3390/w11030472) gives 20% urea basal and stage shares 10/20/45/15/10% across 10 fertigation events.
At fixed N total, timing changes RRMSE by only about +/-0.2 percentage points. Timing is low priority.

### Reported precipitation magnitude
Weather V4 source-scale rain adjustment changes 2020 RRMSE by only +0.225 percentage points in this highly irrigated case. Low priority.

## 6. Nitrogen availability — major lever, exact source still unresolved

Corrected finite-N V2 uses MF=1, NITRO=Y, FERTI=R and DSSAT NICM audit.

2020 M0:
- UNLIMITED: RRMSE 60.771%, mean HWAM 17603 kg/ha
- N64_SPLIT (~54 kg N/ha read): 34.709%, 7290.8
- N129_SPLIT (~117 kg N/ha read): 24.890%, 8399.8
- N193_SPLIT (~171 kg N/ha read): 16.909%, 9401.8
- N129_BASAL (~129 kg N/ha read): 24.403%, 8486.8

N total / N availability is a very large lever. N129/N193 remain diagnostic brackets because exact 2019-2020 fertilizer amount and initial mineral-N profile are not yet recovered.

## 7. Solar radiation — major lever

Weather V4 workflow `.github/workflows/shihezi-m0-weather-gap-diagnostic-v4.yml`, run `33251804055` PASS with canonical in-place WTH edits and post-run SRADA/PRCP audit.

2020 N-disabled M0:
- BASE: RRMSE 60.771%, HWAM 17603, SRADA 24.20
- SRAD~19.8: RRMSE 33.500%, HWAM 14532.5, SRADA 19.80

2019:
- BASE 18.602%
- SRAD~19.9 11.738%

The thesis-scale radiation description (~19.8 MJ m-2 d-1) has major crop-output leverage.

## 8. Soil organic carbon — runtime path repaired, material under finite N

Guo Table 2-1 prints OM values such as 1.485 g/kg, while a later same-station Xinyu66 measurement reports topsoil OM around 14.12 g/kg. HIGHOM is a conditional interpretation: 1.485% OM = 14.85 g/kg OM, converted to OC using OM/1.724.

Earlier LOWOM/HIGHOM tests were invalid because copied DSSAT installs kept the canonical `/tmp/run_M0/Soil/` path and custom whitespace left model-read SLOC=-99.

Canonical SLOC V4:
- workflow `.github/workflows/shihezi-soil-sloc-canonical-v4.yml`
- run `33252514758` PASS
- canonical soil edited in place
- fixed-column .SOL formatting
- INFO.OUT model-read organic C gate PASS

2020 W2, N129:
- LOWOM HWAM 4659 kg/ha; NUCM 94; NMINC 5
- HIGHOM HWAM 6829 kg/ha; NUCM 123; NMINC 49
- HWAM change +2170 kg/ha

Soil OC is a material N-cycle/yield lever once actually read. HIGHOM remains diagnostic until the original OM unit is resolved.

## 9. SRAD x N V3 — valid but superseded as preferred baseline diagnostic by corrected soil OC

Workflow `.github/workflows/shihezi-m0-srad-n-factorial-v3.yml`, run `33252675747` PASS.

Selected results:

|Scenario|2019 RRMSE %|2020 RRMSE %|
|---|---:|---:|
|BASE_UNLIMITED|18.602|60.771|
|SRAD19P8_UNLIMITED|11.738|33.500|
|BASE_N129|24.136|25.853|
|BASE_N193|15.976|18.407|
|SRAD19P8_N129|21.624|18.988|
|SRAD19P8_N193|18.643|14.017|

The 2020 14.017% value shows strong interaction between source-scale radiation and finite N. It was produced with the old soil state before explicit SLOC was correctly propagated, so it must not be treated as the preferred reconstruction after the soil input chain was repaired.

## 10. Corrected OC x SRAD x N matrix — current decisive diagnostic

Workflow `.github/workflows/shihezi-m0-oc-srad-n-matrix.yml`, run `33252751967` PASS.
All scenarios use model-read fixed-column SLOC, audited SRADA and audited NICM.

|Scenario|2019 RRMSE %|2020 RRMSE %|
|---|---:|---:|
|LOWOM_BASESRAD_N129|53.199|59.330|
|LOWOM_BASESRAD_N193|39.908|46.092|
|LOWOM_SRAD19P8_N129|49.229|50.601|
|LOWOM_SRAD19P8_N193|37.010|42.054|
|HIGHOM_BASESRAD_N129|36.571|38.768|
|HIGHOM_BASESRAD_N193|27.113|30.141|
|HIGHOM_SRAD19P8_N129|32.563|33.031|
|HIGHOM_SRAD19P8_N193|26.215|27.828|

Current lowest diagnostic:
- 2019 HIGHOM_SRAD19P8_N193 = 26.215%
- 2020 HIGHOM_SRAD19P8_N193 = 27.828%

### Critical interpretation

The former 2020 14.017% SRADxN result depended on a soil state in which explicit organic carbon was not correctly propagated. Once the soil input chain is repaired and SLOC is actually read, the best current three-factor diagnostic is 27.828% in 2020 and 26.215% in 2019.

Therefore the remaining M0 gap cannot be closed by simply combining the current OC interpretation, thesis-scale radiation and the N129/N193 fertilizer brackets.

The dominant unresolved inputs now point to:
1. exact fertilizer amount plus **initial mineral N profile**;
2. exact soil OM interpretation and its interaction with N mineralization;
3. initial soil-water profile at simulation start;
4. exact observed/NASA weather construction beyond the mean-radiation magnitude.

No missing value may be selected by yield fit.

## 11. Public weather/source recovery status

51356 probe:
- ISD station history found metadata
- direct GSOD 51356099999 2019/2020 and GHCN CHM00051356 daily retrievals returned 404
- no daily NOAA/GHCN series recovered through those exact IDs

POWER May-Aug:
- 2019 Tmax 31.485, Tmin 18.046, rain 93.41 mm, SRAD 22.949
- 2020 Tmax 31.651, Tmin 18.288, rain 118.84 mm, SRAD 23.622

Continue source recovery; do not fabricate station observations.

## 12. Immediate execution queue

1. Inspect the current V4 `*INITIAL CONDITIONS` and confirm DSSAT v4.8.5 SNH4/SNO3 units and model-read values using official examples/source.
2. Search the same Shihezi experimental-station literature / Meng-Guo source chain for pre-sowing mineral N or nitrate/ammonium measurements from 2019-2020.
3. If an exact value is unavailable, run an explicitly diagnostic initial-mineral-N sensitivity range under the corrected fixed-column soil, SRAD~19.8 and finite-N brackets; use it only to quantify required leverage, never to choose a final value by yield fit.
4. Recover or diagnose the initial soil-water profile; current reconstruction is essentially field capacity and requires source verification.
5. Only after a source-supported M0 approaches the published 2019/2020 baseline should M0/H0TT/M15TT be rerun for the final independent yield-accuracy comparison.

## 13. Hard rules

- Never retune M15 (`DTRc=14.8`, `alpha=7.8094`) to fit yield.
- Never retune Xinyu66 coefficients against validation yield.
- Never select missing common inputs by minimizing 2020 yield error.
- Adjacent-source values stay diagnostic until same-trial support exists.
- Every material result, failure, root cause, method switch and major decision goes to `research/dssat-dtr-matrix` and this handoff.
- Do not ask the user to run DSSAT locally.
