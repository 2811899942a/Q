# DSSAT-DTR Xinjiang Research Handoff

Last material checkpoint: 2026-08-29 21:10 CST
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

DSSAT upstream is frozen at official v4.8.5.0.

## 2. Real crop case

- Shihezi University modern water-saving irrigation experimental station
- Xinyu66 maize
- 2019 calibration year; 2020 independent validation year
- W1-W4 irrigation treatments
- location about 85.9964 E, 44.3244 N, elevation 412 m
- sowing 2019-05-03 / 2020-05-05
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

Published original CERES yield RRMSE reference:
- 2019 about 6.52%
- 2020 about 5.69%

## 3. Three temperature arms

- `M0`: official DSSAT v4.8.5 CERES baseline
- `H0TT`: official HMET/TGRO hourly temperature coupled into CERES extreme-day 24-h DTT
- `M15TT`: frozen M15 hourly temperature + the same DTT pathway

No arm-specific calibration is allowed.

## 4. Current methodological rule — clarified 2026-08-29 21:10 CST

The final experiment is a strict control-variable experiment, but the common input set must first be demonstrated to be accurate/reasonable and to be read correctly by DSSAT.

The correct sequence is:

1. Recover and verify the common inputs from the Shihezi/Meng/Guo source chain.
2. Correct engineering input problems such as fixed-column misalignment, wrong runtime paths, or variables that never reach DSSAT.
3. Diagnose the two major common-input discrepancies already identified — solar radiation and N availability — and cross them to determine whether a physically/source-supported reconstruction moves M0 substantially toward the published 2020 RRMSE of about 5.69%.
4. Treat 5.69% as a reproduction sanity reference, not as a numerical optimization target. Do not choose missing inputs solely because they minimize yield error.
5. Once the shared crop/soil/management/weather inputs are source-supported, reasonable and model-read audited, freeze them completely.
6. Run M0 / H0TT / M15TT with the exact same frozen inputs. The only intended difference among the three arms is the temperature-processing pathway.

Therefore:

- `M0` does not have to reproduce 5.69% perfectly.
- A large unexplained M0 discrepancy still requires input/source checking before the final control experiment.
- The final temperature-effect attribution is valid only after common inputs are frozen and identical across all arms.

## 5. Why the baseline input audit was necessary

Initial real-yield V4 successfully propagated temperature-arm changes into HWAM but M0 reproduced 2020 poorly:
- M0 60.771%
- H0TT 54.414%
- M15TT 56.973%

This showed that crop propagation exists, while the common reconstructed input set still had large unresolved errors.

Several engineering/input issues were then discovered:
- fertilizer factor initially had `MF=0`, so intended fertilizer was not selected;
- copied DSSAT installations retained canonical runtime paths, causing edited Weather/Soil files to be bypassed;
- custom soil fixed-column formatting left SLOC unread or as -99 in model-read input;
- an initial-mineral-N sensitivity rewrite also produced fixed-column misalignment and was withdrawn.

These are input-chain correctness problems and must be fixed before final temperature attribution.

## 6. Major common-input dimension 1 — solar radiation

Audited weather V4 edited the canonical active WTH and required Summary.OUT SRADA/PRCP to move.

2020 M0, nitrogen disabled:
- BASE: RRMSE 60.771%, HWAM 17603 kg/ha, SRADA 24.20
- SRAD about 19.8: RRMSE 33.500%, HWAM 14532.5 kg/ha, SRADA 19.80

2019:
- BASE 18.602%
- SRAD about 19.9 -> 11.738%

The thesis-scale radiation description around 19.8 MJ m-2 d-1 is therefore a major, source-supported common-input discrepancy.

POWER Tmax/Tmin comparison against Guo Fig. 2-2 has shown generally small mean biases and about 1-2 C RMSE, so daily Tmax/Tmin forcing is currently lower priority than SRAD.

## 7. Major common-input dimension 2 — N availability / fertilizer / initial mineral N

Corrected finite-N V2 uses MF=1, NITRO=Y, FERTI=R and DSSAT NICM audit.

2020 M0:
- UNLIMITED: RRMSE 60.771%, mean HWAM 17603 kg/ha
- N64_SPLIT, about 54 kg N/ha actually read: 34.709%
- N129_SPLIT, about 117 kg N/ha actually read: 24.890%
- N193_SPLIT, about 171 kg N/ha actually read: 16.909%
- N129_BASAL, about 129 kg N/ha actually read: 24.403%

Thus N availability is the other major common-input dimension.

Exact 2019-2020 fertilizer amount and pre-sowing mineral-N profile remain unresolved, so N129/N193 are diagnostic brackets and cannot be promoted to formal inputs by yield fit alone.

## 8. SRAD x N cross-diagnostic

A valid audited cross-factorial was completed before the explicit SLOC correction:

| Scenario | 2019 RRMSE % | 2020 RRMSE % |
|---|---:|---:|
| BASE_UNLIMITED | 18.602 | 60.771 |
| SRAD19P8_UNLIMITED | 11.738 | 33.500 |
| BASE_N129 | 24.136 | 25.853 |
| BASE_N193 | 15.976 | 18.407 |
| SRAD19P8_N129 | 21.624 | 18.988 |
| SRAD19P8_N193 | 18.643 | 14.017 |

The 2020 `SRAD19P8_N193 = 14.017%` result showed that crossing the two identified dimensions explained a large fraction of the original 60.771% error and moved strongly toward the published 5.69% reference.

This 14.017% value is retained as an important diagnostic signal, but it is not the final accepted baseline because the soil organic-carbon input chain was later found to be incorrect.

## 9. Soil organic carbon — input correctness issue discovered after the two-factor cross

The custom soil file initially did not propagate SLOC correctly into DSSAT. Canonical fixed-column SLOC V4 repaired that path.

2020 W2, N129:
- LOWOM HWAM 4659 kg/ha
- HIGHOM HWAM 6829 kg/ha
- NUCM 94 -> 123
- NMINC 5 -> 49

Thus soil OC materially affects N cycling/yield once actually read.

A later OC x SRAD x N matrix gave:

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

The best corrected three-factor diagnostic was 27.828% in 2020. This does not invalidate the original SRAD/N diagnosis; it shows that soil OM interpretation and initial N state interact strongly and must be resolved before freezing the common input set.

The HIGHOM interpretation remains conditional because the original Guo OM unit is not yet fully resolved.

## 10. Small or low-priority common-input levers

- density 8.25 vs 8.89 plants/m2: about 1.83 percentage-point M0 change
- fertilizer timing shape at fixed N: about +/-0.2 percentage points
- reported rain-magnitude correction: about +0.225 percentage points in 2020

These are not current priorities.

## 11. Current unresolved inputs before final control-variable run

Highest priority:
1. exact 2019-2020 fertilizer total / form and pre-sowing mineral-N profile;
2. exact interpretation of Guo soil OM and a model-read correct soil profile;
3. initial soil-water profile at simulation start;
4. exact observed + NASA weather construction, particularly solar radiation.

Already substantially verified:
- sowing dates
- irrigation treatments and totals
- Xinyu66 six genotype coefficients
- IB0001 template chain
- daily Tmax/Tmin reasonableness against Guo Fig. 2-2
- M15 temperature algorithm

## 12. Immediate execution plan

1. Finish the corrected fixed-column initial mineral-N model-read audit. Withdraw any sensitivity run that fails the DSSAT48.INP/INFO.OUT read gate.
2. Recover exact or same-trial-supported 2019-2020 N management / initial mineral N. If unavailable, keep a physically plausible diagnostic range only to quantify leverage.
3. Resolve soil OM unit/source interpretation and retain only the model-read-correct soil profile.
4. Recover/verify initial soil water instead of assuming an arbitrary value.
5. Re-run the SRAD x N (and, if source-supported, soil/initial-state) cross using only defensible common inputs.
6. Compare the resulting M0 with the published 2019 ~6.52% / 2020 ~5.69% as a sanity check. Strong convergence is evidence that the reconstructed inputs are credible; exact numerical equality is not required.
7. Freeze the accepted common input set.
8. Run final M0 / H0TT / M15TT with identical inputs and quantify temperature-only effects on hourly temperature, phenology and final yield.

## 13. Hard rules

- Never retune M15 (`DTRc=14.8`, `alpha=7.8094`) to fit yield.
- Never retune Xinyu66 coefficients against 2020 yield.
- Never select missing common inputs solely by minimizing 2020 yield error.
- Do not accept a changed input until DSSAT model-read output proves that the value actually entered the simulation.
- The published 5.69% is a reproduction reference/sanity target, not a free parameter-optimization objective.
- Final causal attribution requires identical common inputs across M0/H0TT/M15TT; only the temperature-processing pathway may differ.
- Every material result, failure, root cause, method switch and major decision goes to `research/dssat-dtr-matrix` and this handoff.
