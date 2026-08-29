# CHECKPOINT 2026-08-29 20:50 CST — Correct formal yield-reproduction gate to what Guo (2025) actually supports

## Why this checkpoint is needed
Earlier Shihezi reconstruction workflows hard-coded:
- 2019 published M0 yield RRMSE = 6.52%
- 2020 published M0 yield RRMSE = 5.69%

Those values were used as a working reproduction gate. A fresh source audit of the uploaded Guo (2025) thesis does not find 6.52% or 5.69% as explicit body-text values. They may have been inferred/read from Fig. 2-4, but that exact figure-label reading has not yet been independently re-verified.

## Source-confirmed quantitative statements
Guo (2025) text explicitly states for yield simulation:
- yield RRMSE is below 10%;
- W2, W3 and W4 yield ARE are below 5%;
- W1 yield ARE is 15.17% in 2019 and 13.19% in 2020;
- 2019 is the calibration year;
- 2020 did not participate in parameter tuning and is an independent validation year.

The thesis conclusion again states yield RRMSE is controlled below 10% and most mature-yield treatment ARE values are below 5%.

## Methodological correction
Until the exact figure annotation is visually/readably confirmed, the publication-supported M0 reproduction gate should be:

**Primary gate:** 2020 reconstructed M0 yield RRMSE < 10% using defensible source-based inputs.

**Treatment-pattern check:** W2–W4 should be close to observation (published ARE <5%); W1 may remain substantially worse (published 2020 ARE 13.19%).

The previous 5.69% value may remain in historical result files as a working figure-derived reference, but it must not be described as an explicitly text-confirmed published value unless separately verified.

## Consequence
This correction does not make the current V4 reconstruction acceptable: V4 M0 2020 RRMSE = 60.771%, still far outside the source-confirmed <10% range.

The corrected nitrogen diagnostic V2 best tested case (N193_SPLIT RRMSE 16.909%) also remains outside the source-confirmed <10% range.

Therefore all previous scientific decisions that M0 reproduction is inadequate remain unchanged; only the exact numerical gate source is being corrected.

## Current pending work
The HIGHOM diagnostic V2 workflow/run `33251645551` is currently running. It tests whether interpreting Guo Table 2-1 OM numerics as percent OM rather than literal g/kg materially improves the finite-N M0 reproduction. No crop or M15 parameters are being tuned.

## Rules
- No genotype retuning.
- No M15/DTRc/alpha retuning.
- No N/OM target fitting.
- Final real-yield temperature-method comparison requires a defensible M0 with 2020 yield RRMSE <10% and a treatment error pattern compatible with Guo's reported W1 versus W2–W4 behavior.
- Every material result/failure/method change must be checkpointed before continuation.
