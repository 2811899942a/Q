# CHECKPOINT 2026-08-29 20:05 CST — Shihezi M0 source-gap re-audit

## Current question

The Shihezi Xinyu66 V4 three-arm run propagates the hourly-temperature changes into final HWAM, but the reconstructed official M0 baseline fails the published 2020 yield reproduction gate (60.771% RRMSE versus about 5.69%). Before judging H0TT/M15TT accuracy, common-arm input gaps must be isolated.

## 1. Corrected finite-N diagnostic is valid

The first finite-N diagnostic was invalid because the treatment row had `MF=0`. The corrected V2 explicitly uses `MF=1`, `NITRO=Y`, and `FERTI=R`.

DSSAT audit confirms different applied-N totals are actually read:

- N64_SPLIT: NI#M=9, NICM about 54 kg N/ha
- N129_SPLIT: NI#M=9, NICM about 117 kg N/ha
- N193_SPLIT: NI#M=9, NICM about 171 kg N/ha
- N129_BASAL: NI#M=1, NICM about 129 kg N/ha

2020 M0 diagnostic metrics:

| Scenario | RMSE kg/ha | RRMSE % | MAE kg/ha | Bias kg/ha | Mean HWAM kg/ha |
|---|---:|---:|---:|---:|---:|
| UNLIMITED | 6684.8 | 60.771 | 6603.0 | +6603.0 | 17603.0 |
| N64_SPLIT | 3818.0 | 34.709 | 3709.2 | -3709.2 | 7290.8 |
| N129_SPLIT | 2737.9 | 24.890 | 2600.2 | -2600.2 | 8399.8 |
| N193_SPLIT | 1860.0 | 16.909 | 1598.2 | -1598.2 | 9401.8 |
| N129_BASAL | 2684.4 | 24.403 | 2513.2 | -2513.2 | 8486.8 |

Best finite-N diagnostic is N193_SPLIT: RRMSE 16.909%, a 72.17% relative reduction from the current unlimited-N M0 reconstruction.

### Scientific interpretation

Nitrogen representation has enough leverage to explain a large fraction of the M0 yield mismatch. N193_SPLIT is only a sensitivity bracket; it is not accepted as the true 2019–2020 management because the exact fertilizer schedule has not yet been recovered from the source experiment.

The remaining 16.909% is still far above the published 2020 ~5.69% baseline, so a final three-arm accuracy claim remains blocked.

## 2. Weather source-gap diagnostic V1 is engineering-invalid for attribution

The existing weather diagnostic intended to test source-supported magnitude changes:

- growing-season precipitation toward about 96.45/119.88 mm (2019/2020)
- mean SRAD toward about 19.8 MJ m-2 d-1

However, every weather scenario returned exactly the same DSSAT weather summaries as BASE:

- 2019 SRADA 23.30, PRCP 83.30
- 2020 SRADA 24.20, PRCP 103.10

and exactly the same HWAM/RRMSE.

Because the post-run `Summary.OUT` weather diagnostics did not change, this run does not establish that rainfall or radiation have zero crop effect. The attempted WTH modifications failed to propagate into the active DSSAT run path or were otherwise bypassed.

Therefore:

**RAIN_MATCH, SRAD_19P8 and WEATHER_BOTH V1 are withdrawn from scientific attribution.**

## 3. Next action

Run a weather diagnostic V2 with hard pre/post audit:

1. create independent physical scenario roots;
2. edit the exact active `/DSSAT48/Weather/SHIH1901.WTH` and `SHIH2001.WTH` after linking the scenario root;
3. save WTH hashes and direct parsed SRAD mean / RAIN total before each simulation;
4. run M0;
5. require `Summary.OUT` SRADA/PRCP to change consistently with the edited WTH;
6. workflow must fail if a requested weather scenario is numerically identical to BASE after the input audit;
7. only a passing V2 can be used to quantify the weather contribution.

In parallel, continue source recovery for the same 2019–2020 Meng/Guo field trial, focusing on fertilizer schedule and initial soil water.

## 4. Frozen rules

- M15 remains frozen: DTRc=14.8 C; alpha=7.8094.
- Xinyu66 genotype remains frozen.
- No input value may be chosen by minimizing validation yield error.
- Source-supported common-arm recovery is allowed.
- Diagnostic brackets must remain labeled diagnostic.
- Final real-yield accuracy comparison remains blocked until M0 approaches the published baseline.
