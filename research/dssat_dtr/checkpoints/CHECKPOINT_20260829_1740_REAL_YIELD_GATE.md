# DSSAT-DTR checkpoint — Shihezi real-yield validation gate

Time: 2026-08-29 17:40 CST
Branch: `research/dssat-dtr-matrix`

## Goal
Test whether the frozen hourly-temperature / extreme-day thermal-time method improves real maize yield prediction, using Guo Lipeng (2025) Shihezi field data rather than the earlier proxy cultivar.

## Frozen real-case evidence
- Site: Shihezi University Modern Water-saving Irrigation Key Experimental Station.
- 2019 = cultivar calibration year; 2020 = independent validation year.
- Cultivar: Xinyu 66.
- Frozen coefficients: P1=104.7, P2=1.824, P5=957.2, G2=671, G3=15.82, PHINT=42.97.
- Four irrigation treatments W1-W4 and 2019/2020 irrigation schedules are taken from Guo (2025), not retuned.
- Guo reports original CERES-Maize yield RRMSE about 6.52% (2019) and 5.69% (2020); W2-W4 yield ARE <5%, W1 ARE 15.17%/13.19%.

## Causal arms
- M0: official CERES extreme-day sine-hour DTT.
- H0TT: official HMET `TGRO` routed into the existing CERES extreme-day DTT integration.
- M15TT: frozen Xinjiang M15 hourly correction + the same TGRO-DTT routing.
- No arm-specific cultivar or crop-output calibration is allowed.

## Reconstruction limitations
The thesis does not publish the exact original DSSAT project, exact CMA+NASA WTH, fertilizer schedule, initial soil water/N, or raw yield table. V1 therefore uses:
- Guo soil/profile and irrigation directly;
- NASA POWER daily weather at the field coordinate as a provisional reconstruction;
- nitrogen disabled identically for all arms rather than inventing fertilizer;
- initial soil water = DUL identically for all arms;
- plant density 8.89 plants/m2 derived from Guo planting geometry;
- observed yields digitized from Fig. 2-4A with approximately +/-100 kg/ha resolution.

## Hard scientific gate
2020 is the primary independent validation year. The reconstructed M0 must first reproduce the published 5.69% yield RRMSE to within 3 percentage points. If this gate fails, no real-yield accuracy improvement claim is allowed even if H0TT/M15TT numerically move closer to the digitized bars.

## Execution status
- First workflow `Shihezi Real Yield V1` compiled all DSSAT arms but failed before simulation because a custom `.MZX` treatment row violated DSSAT fixed-column `IPEXP` formatting and the experiment stem was only 7 characters. This is an input engineering failure, not a scientific result.
- Correct treatment-row format was recovered from the already successful Anningqu builder (`IPEXP FORMAT 55`) and experiment stems are now 8 characters (`SHIHYYTT`).
- Corrected workflow: `.github/workflows/shihezi-real-yield-v2.yml`.
- Active run at checkpoint: `33246010726`.

## Next action
Wait for V2 completion, then report 2020 W1-W4 observed vs M0/H0TT/M15TT, RMSE/RRMSE/MAE/Bias, M0 reproduction gate, and whether any apparent improvement exceeds the ~100 kg/ha digitization-resolution threshold. If M0 reproduction fails, do not tune M15 to yield; identify the missing original inputs as the publication-grade validation bottleneck.
