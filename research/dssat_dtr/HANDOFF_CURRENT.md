# DSSAT-DTR Xinjiang Research Handoff

Last material checkpoint: 2026-08-29 20:33 CST
Branch: `research/dssat-dtr-matrix`
Study: DSSAT v4.8.5 CERES-Maize hourly-temperature / extreme-day thermal-time improvement

## 1. Frozen scientific method

M15 is frozen. Do not retune it to force crop-output gains.

- `DTRc = 14.8 C`
- `alpha = 7.8094`
- `DTR <= 14.8 C` or `CLOUDS <= 0`: official HTEMP retained exactly
- pre-peak daytime branch retained
- official Tmax anchor retained
- post-peak -> sunset branch corrected
- official night exponential structure retained

Independent Urumqi 2017-2024 validation:
- May-Sep hourly RMSE: 2.9469 -> 2.8241 C (4.17% reduction)
- DTR>=15 C RMSE: 5.1215 -> 4.6783 C (8.65% reduction)
- Bias: +1.2167 -> +0.3784 C
- R2: 0.5559 -> 0.6210
- physical violations: 0/130 complete 24-h days
- 5/5 high-DTR validation years improved

DSSAT upstream frozen at official v4.8.5.0.

## 2. Frozen real-crop case

Site: Shihezi University modern water-saving irrigation experimental station.
Crop: Xinyu66 maize.
Years: 2019 calibration, 2020 independent validation.
Treatments: W1-W4.

Frozen Xinyu66 coefficients:
- P1=104.7
- P2=1.824
- P5=957.2
- G2=671
- G3=15.82
- PHINT=42.97

Recovered common inputs:
- location ~85.9964 E, 44.3244 N, elevation 412 m
- sowing 2019-05-03 / 2020-05-05
- 25 cm plant spacing; 30/60 cm narrow/wide rows; 4 cm sowing depth; 1.45 m mulch
- formal Guo-derived density 8.89 plants/m2
- W1-W4 irrigation totals 487.5/525/562.5/600 mm
- 10 irrigation events
- Guo hydraulic soil profile recovered
- ecotype `IB0001`

Published original CERES yield RRMSE target:
- 2019 ~6.52%
- 2020 ~5.69%

Final three-arm predictive comparison is blocked until a source-supported M0 reconstruction approaches the published baseline.

## 3. Three-arm definitions

- `M0`: official DSSAT v4.8.5 CERES baseline
- `H0TT`: official HMET/TGRO hourly temperature coupled into the CERES extreme-day 24-h DTT pathway
- `M15TT`: frozen M15 hourly temperature + the same TGRO-based extreme-day DTT pathway

No arm-specific calibration is allowed.

## 4. Real-yield V4 — valid propagation, baseline reproduction gap remains

Workflow: `.github/workflows/shihezi-real-yield-v4.yml`
Run: `33246786517` PASS.
All 24 runs completed (3 arms x 2 years x 4 treatments). `Summary.OUT` HWAM parsing was audited against raw fixed-column rows.

### 2019
|Arm|RMSE kg/ha|RRMSE %|MAE kg/ha|Bias kg/ha|
|---|---:|---:|---:|---:|
|M0|2069.2|18.602|1644.8|+1644.8|
|H0TT|1944.4|17.480|1484.8|+1484.8|
|M15TT|2068.8|18.598|1644.5|+1644.5|

### 2020 independent validation
|Arm|RMSE kg/ha|RRMSE %|MAE kg/ha|Bias kg/ha|
|---|---:|---:|---:|---:|
|M0|6684.8|60.771|6603.0|+6603.0|
|H0TT|5985.5|54.414|5916.2|+5916.2|
|M15TT|6267.0|56.973|6179.2|+6179.2|

Provisional 2020 contrasts:
- H0TT vs M0 relative RRMSE reduction = 10.461%
- M15TT vs M0 relative RRMSE reduction = 6.250%
- M15TT is 4.703% worse than H0TT locally
- maximum arm-induced HWAM shift = 934 kg/ha

Interpretation: hourly-temperature/DTT modifications can materially propagate to crop yield. These percentages remain provisional while the common M0 reconstruction is being recovered.

## 5. Density sensitivity — small lever

Same-trial source conflict tested: 8.89 vs 8.25 plants/m2.
At 8.25 plants/m2, 2020 RRMSE:
- M0 58.945%
- H0TT 52.483%
- M15TT 55.230%

Density changes M0 by only ~1.83 percentage points. Keep formal Guo-derived 8.89 plants/m2.

## 6. Nitrogen root-cause diagnostic — very large lever

First finite-N run was engineering-invalid because treatment `MF=0` left fertilizer unselected.

Corrected V2 uses `MF=1`, `NITRO=Y`, `FERTI=R`; `NICM` audit confirms fertilizer entered DSSAT:
- N64_SPLIT ~54 kg N/ha
- N129_SPLIT ~117 kg N/ha
- N193_SPLIT ~171 kg N/ha
- N129_BASAL ~129 kg N/ha

2020 M0:
|Scenario|RRMSE %|Mean HWAM kg/ha|Bias kg/ha|
|---|---:|---:|---:|
|UNLIMITED|60.771|17603.0|+6603.0|
|N64_SPLIT|34.709|7290.8|-3709.2|
|N129_SPLIT|24.890|8399.8|-2600.2|
|N193_SPLIT|16.909|9401.8|-1598.2|
|N129_BASAL|24.403|8486.8|-2513.2|

N193_SPLIT reduces RRMSE by 72.17% relative to current unlimited-N M0. It remains a diagnostic bracket because the exact 2019-2020 fertilizer total and initial mineral-N profile remain unresolved.

## 7. Same-station fertilizer timing diagnostic — negligible lever

Adjacent same-station source: Wang et al. 2019, Water 11(3):472, DOI `10.3390/w11030472`.
Recovered 2018 management:
- P2O5 120 kg/ha base
- K2O 90 kg/ha base
- 20% of urea as base fertilizer
- remaining fertilizer with irrigation
- 10 irrigation/fertigation events
- stage shares seedling/jointing/tasseling/filling/maturity = 10/20/45/15/10%

At fixed nominal N total, equal-10 timing vs this adjacent-source timing:
- N~129: RRMSE 24.890 -> 25.086 (+0.196 pp); mean HWAM -6.5 kg/ha
- N~193: RRMSE 16.909 -> 16.721 (-0.189 pp); mean HWAM +15.0 kg/ha

Conclusion: timing shape has negligible leverage compared with total N. Exact 2019-2020 fertilizer amount/initial N is higher priority.

## 8. Weather source-gap diagnostics — solar radiation is a major lever

Current V4 forcing is provisional NASA POWER-only.
Published thesis-scale magnitudes indicate approximately:
- precipitation 2019 96.45 mm, 2020 119.88 mm over the reported growing-season period
- mean total radiation ~19.8 MJ m-2 d-1

Early weather diagnostics V1-V3 were engineering-invalid because edited copied WTH files did not propagate into the active installed DSSAT path. Their crop responses are withdrawn.

### Weather V4 — VALID active-path audit

Workflow: `.github/workflows/shihezi-m0-weather-gap-diagnostic-v4.yml`
Run `33251804055` PASS.
Canonical `/tmp/run_M0/Weather` files were edited in place and hashes audited immediately before execution; `Summary.OUT` SRADA/PRCP moved in the requested direction.

2020 M0 with nitrogen disabled:
|Scenario|RRMSE %|Mean HWAM kg/ha|Summary SRADA|Summary PRCP mm|
|---|---:|---:|---:|---:|
|BASE|60.771|17603.0|24.20|103.10|
|RAIN_MATCH|60.996|17626.8|24.20|119.40|
|SRAD_19P8|33.500|14532.5|19.80|105.30|
|WEATHER_BOTH|33.591|14543.0|19.80|122.00|

2020 effects relative to BASE:
- source-scale rain adjustment: RRMSE +0.225 pp; HWAM +23.8 kg/ha
- SRAD to ~19.8: RRMSE -27.270 pp; HWAM -3070.5 kg/ha
- both: RRMSE -27.180 pp

2019 similarly improves from 18.602% to 11.738% when SRADA is reduced to ~19.9.

Conclusion: the radiation discrepancy is a major source-gap lever; the modest rain magnitude discrepancy has negligible leverage in this highly irrigated case.

## 9. Public station-weather recovery

Run `33251318548`:
- ISD station-history returned a 51356/513560 metadata match
- GSOD `51356099999` daily 2019/2020 -> 404
- GHCN `CHM00051356.dly` -> 404

No daily series recovered through these exact identifiers. Do not fabricate a station series.

POWER May-Aug audit:
- 2019: Tmax 31.485 C, Tmin 18.046 C, rain 93.41 mm, SRAD 22.949
- 2020: Tmax 31.651 C, Tmin 18.288 C, rain 118.84 mm, SRAD 23.622

Rain magnitude is already close to thesis totals, especially in 2020. Radiation is the clearer forcing discrepancy.

## 10. Soil organic-carbon audit — canonical V4 PASS and material response

Guo Table 2-1 prints OM such as `1.485 g/kg`; later same-station Xinyu66 work reports topsoil OM ~14.12 g/kg. A diagnostic HIGHOM hypothesis tests `1.485% = 14.85 g/kg`, converted to organic C using OM/1.724.

Earlier LOWOM/HIGHOM runs were masked by two engineering issues: copied DSSAT installations retained the canonical `/tmp/run_M0/Soil/` path, and the custom whitespace layout left model-read `SLOC=-99`.

Canonical V4 fixed both issues:
- workflow `.github/workflows/shihezi-soil-sloc-canonical-v4.yml`
- run `33252514758` PASS
- canonical `/tmp/run_M0/Soil/SH.SOL` edited in place
- fixed-column DSSAT soil format
- INFO.OUT model-read organic C audited before interpretation

2020 W2 with the existing N129 bracket:

|Metric|LOWOM|HIGHOM|Change|
|---|---:|---:|---:|
|HWAM kg/ha|4659|6829|+2170|
|NI#M|9|9|0|
|NICM kg N/ha|117|117|0|
|NUCM kg N/ha|94|123|+29|
|NLCM kg N/ha|7|6|-1|
|NMINC kg N/ha|5|49|+44|

Model-read gate:
- LOWOM intended SLOC `[0.0861,0.0818,0.0733,0.0758,0.0593]`; INFO reads approximately 0.09/0.08/0.07/0.06% C after layer subdivision.
- HIGHOM intended SLOC `[0.8614,0.8179,0.7332,0.7581,0.5928]`; INFO reads approximately 0.86/0.82/0.73/0.76/0.59% C.

Conclusion: organic carbon is a material finite-N crop-output lever once it reaches DSSAT correctly. HIGHOM remains a conditional source-interpretation hypothesis and cannot be promoted by yield fit alone.

Checkpoint: `CHECKPOINT_20260829_2033_SLOC_CANONICAL_V4_PASS.md`.

## 11. SRAD x N factorial status

V1 failed because its irrigation parser expected the YYDDD date in the first token while V4 irrigation rows use factor level + date.
V2 failed before science because an indentation-specific wrapper anchor did not match the extracted script.

Both failures are recorded and contain no scientific result.

V3 is now triggered at `.github/workflows/shihezi-m0-srad-n-factorial-v3.yml`. It reuses the V1 scientific matrix and replaces only the single failed irrigation-date inference with the exact frozen V4 2019/2020 date lists. No crop/scientific parameter changes are introduced.

## 12. Remaining source gaps ranked

Current evidence ranks the M0 reconstruction gaps/levers:

1. **N availability / fertilizer + initial mineral N** — very large effect.
2. **Solar radiation forcing** — very large effect.
3. **Soil organic carbon / original OM unit** — now proven material under finite N; exact source interpretation remains unresolved.
4. **Initial soil-water profile** — unresolved; current initialization is essentially field capacity and needs source verification.
5. **Plant density** — small effect.
6. **Fertilizer timing shape at fixed N** — negligible effect.
7. **Reported precipitation magnitude difference** — negligible effect for this highly irrigated case.

## 13. Immediate execution queue

1. Finish SRAD x N factorial V3 for 2019/2020 W1-W4.
2. Extend the now-valid fixed-column LOWOM/HIGHOM audit from W2 to W1-W4 and quantify RRMSE.
3. Run a compact source-gap matrix combining correctly read soil OC with source-scale SRAD and finite-N brackets; retain all values as diagnostics unless exact same-trial support exists.
4. Continue source recovery from the same 2019-2020 experiment for exact fertilizer total, initial mineral N, initial soil water, soil OM unit and observed/NASA weather construction.
5. Once a source-supported M0 approaches the published 2020 RRMSE ~5.69%, rerun M0/H0TT/M15TT under identical recovered common inputs.
6. Final output must quantify the crop-yield improvement or state that the improvement is not robust.

## 14. Hard rules

- Never retune M15 (`DTRc=14.8`, `alpha=7.8094`) to fit yield.
- Never retune Xinyu66 genotype to fit the 2020 validation yield.
- Never select missing common inputs by minimizing 2020 yield error.
- Adjacent-source values remain diagnostic until exact same-trial support is found.
- Every material result, failure, root cause, method switch, and major decision must be committed to `research/dssat-dtr-matrix` and reflected in this handoff.
- Do not ask the user to run DSSAT locally.
