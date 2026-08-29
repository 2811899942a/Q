# CHECKPOINT 2026-08-29 19:38 CST — Shihezi real-yield validation V4

## Purpose
Preserve the current scientific and engineering state before continuing the Shihezi real-yield validation of the Xinjiang large-DTR DSSAT temperature method.

## Frozen method
Three arms are compared with identical crop, soil, management and weather reconstruction inputs:
- M0: official DSSAT/CERES-Maize baseline.
- H0TT: official HMET/TGRO hourly temperature used in the existing CERES extreme-temperature DTT branch; no M15 regional correction.
- M15TT: M15 high-DTR hourly-temperature correction plus TGRO-based extreme-day DTT coupling.

Cultivar coefficients are frozen to Guo (2025) Xinyu66:
- P1 = 104.7
- P2 = 1.824
- P5 = 957.2
- G2 = 671
- G3 = 15.82
- PHINT = 42.97

No arm-specific re-calibration is permitted.

## Real case
Shihezi University modern water-saving irrigation experimental station, 2019–2020, Xinyu66, four irrigation treatments W1–W4.
- 2019: published calibration year.
- 2020: treated as the independent validation year.
- Observed yield targets currently digitized from Guo (2025) figure, uncertainty approximately +/-100 kg/ha.
- Published original CERES-Maize yield RRMSE: 2019 = 6.52%, 2020 = 5.69%.

## V4 execution status
GitHub Actions run 33246786517 completed successfully.
All three DSSAT arms and all 24 simulations (3 arms x 2 years x 4 treatments) ran successfully. Summary.OUT parsing was audited and HWAM is confirmed to be correctly read, so the large yield values are not a parser artifact.

## V4 formal results
2019:
- M0: RMSE 2069.2 kg/ha; RRMSE 18.602%; MAE 1644.8; Bias +1644.8.
- H0TT: RMSE 1944.4; RRMSE 17.480%; MAE 1484.8; Bias +1484.8.
- M15TT: RMSE 2068.8; RRMSE 18.598%; MAE 1644.5; Bias +1644.5.

2020 independent validation:
- M0: RMSE 6684.8 kg/ha; RRMSE 60.771%; MAE 6603.0; Bias +6603.0.
- H0TT: RMSE 5985.5; RRMSE 54.414%; MAE 5916.2; Bias +5916.2.
- M15TT: RMSE 6267.0; RRMSE 56.973%; MAE 6179.2; Bias +6179.2.

Relative 2020 changes:
- H0TT vs M0: RRMSE improves by 10.461% relative.
- M15TT vs M0: RRMSE improves by 6.250% relative.
- M15 local contribution relative to H0TT: -4.703% (worse than H0TT in this reconstruction).
- Maximum arm-induced HWAM shift: 934 kg/ha, well above the ~100 kg/ha digitization uncertainty threshold.

## Mandatory scientific decision
The M0 reproduction gate FAILS badly:
- reconstructed 2020 M0 RRMSE = 60.771%
- published 2020 M0 RRMSE = 5.69%

Therefore NO claim of improved real-yield predictive accuracy is currently allowed.
The present result proves only that the hourly thermal-time modifications propagate strongly enough to alter Xinyu66 yield in a real-case reconstruction.

## Parser audit
The parser is no longer the suspected source of the large error. Example M0 2020 W1 Summary.OUT explicitly reports:
- CWAM = 28439 kg/ha
- HWAM = 17591 kg/ha
- IR#M = 9
- IRCM = 439 mm
- PRCM = 105 mm
- ETCM = 510 mm
- LAIX = 4.6
Thus the 17.6 t/ha simulated yield is a real model output from the reconstructed input, not a field-shift parsing error.

## Current reconstruction caveats likely responsible for M0 mismatch
The current run is NOT a publication-grade reproduction because several original inputs are missing or approximated:
1. Weather uses provisional NASA POWER daily reconstruction rather than the exact original CMA + NASA weather series used by Guo.
2. Initial soil water is set to DUL identically because the exact measured initial profile has not yet been recovered.
3. Nitrogen is disabled because the exact fertilizer schedule/soil N initialization has not yet been reconstructed.
4. Plant density and some management details were derived from textual information rather than imported from the authors' original DSSAT experiment file.
5. Observed yields are digitized from a figure rather than taken from a raw table.

## Root-cause direction
The failure is a strong systematic positive yield bias, especially in 2020. This points to reconstructed forcing/management/stress differences rather than the temperature parser.
Priority diagnostic order:
1. Recover exact fertilizer schedule and determine whether N stress was active in the original model.
2. Recover measured initial soil water / initial-condition treatment.
3. Recover exact 2019–2020 station weather used in the paper, especially Tmax/Tmin/SRAD/RAIN.
4. Verify planting population, planting depth, row spacing and irrigation-event count/amount against the original thesis tables.
5. Only after M0 approaches the published 5.69% 2020 RRMSE is it scientifically valid to compare M0/H0TT/M15TT accuracy.

## Do not do
- Do not retune M15, DTRc=14.8 C, alpha=7.8094, or Xinyu66 cultivar coefficients against the yield target.
- Do not present the current 6.25% M15TT relative RRMSE decrease as evidence of real-yield improvement because the M0 reproduction gate failed.
- Do not return to proxy cultivar tests unless needed for source mechanics.

## Next action
Continue reconstructing the original Shihezi experiment from Guo (2025), Liang et al. (2022), Meng Yu (2021), and available station data. The immediate goal is to identify the input(s) causing M0 2020 HWAM ~17.6 t/ha instead of the published near-observed performance. Once corrected, rerun the same frozen three arms.

## Continuity rule requested by user
From this checkpoint onward, after every material result, material failure, method switch, or major decision, write a new GitHub checkpoint before continuing computation so a conversation interruption cannot erase state.
