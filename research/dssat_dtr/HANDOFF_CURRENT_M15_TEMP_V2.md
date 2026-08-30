# HANDOFF CURRENT — DSSAT M15 Temperature Accuracy V2

Last updated: 2026-08-30 10:43 CST
Branch: `research/dssat-m15-temp-accuracy-v2`

## 1. Current objective
Use the existing frozen DSSAT package and existing experimental inputs as the only baseline. Do not search for additional external datasets or attempt perfect reproduction. Verify only that required inputs are complete and correctly read, then use a strict control-variable design to test temperature-algorithm changes.

Final evaluation has two primary dimensions only:
1. hourly temperature accuracy — primary metric RMSE (C);
2. crop yield accuracy — primary metric RRMSE (%).

## 2. Immutable baselines
- Official DSSAT 4.8.5 temperature pathway: temperature RMSE 2.946891175 C; crop RRMSE 26.9147158% under frozen SRAD19P8_N_OFF ALL8 diagnostic.
- M15-13.5: DTRc=13.5 C, alpha=6.407985379809223; temperature RMSE 2.796223546 C; crop RRMSE 25.4973651%.
- M15-13.8: DTRc=13.8 C, alpha=6.749813473189908; temperature RMSE 2.801548624 C; crop RRMSE 24.0122042%.
- Final lower-bound audit workflow run: 33259349242, SUCCESS.
- Freeze checkpoint commit: ef34289f50d889e15de9df1d0a0323c21b36f20c.
- Project deployment decision commit: 07ec04abb355f46f76c5a70be1d025ad5ae8ad18.

## 3. Experimental boundary
Keep weather daily inputs, soil, cultivar, sowing, irrigation, fertilizer/N_OFF treatment, initial conditions, crop observations, years/treatments and all non-temperature CERES-Maize code fixed.

Only the hourly temperature algorithm may vary.

Do not improve results by changing the frozen DSSAT input chain.

## 4. Minimum pre-run gate
Gate A: all required frozen inputs exist and the fixed cases run completely.
Gate B: DSSAT actually reads the intended files/treatments/dates and the new temperature code path is executed.

After A/B pass, start simulation. No further data collection is required.

## 5. Candidate workflow
Use M15-13.5 as the main structural starting point. Modify one temperature structure at a time when possible, then test combinations only after single-factor effects are known.

For every arm record at least:
- temperature RMSE, MAE, Bias, R2;
- crop yield RRMSE, RMSE, MAE, Bias;
- exact algorithm structure and parameters;
- commit SHA and, if applicable, workflow run ID;
- PASS/FAIL/KEEP/DROP decision.

Prefer candidates that improve both primary metrics. Preserve Pareto tradeoffs and all negative results.

## 6. GitHub checkpoint rule
Any meaningful algorithm structure, parameterization, successful result, failure, keep/drop decision or new best result must be committed immediately.

Historical checkpoints: `CHECKPOINT_YYYYMMDD_HHMM_*.md`.
This file is the rolling latest handoff and must be updated after important progress.

Key current protocol checkpoint:
`CHECKPOINT_20260830_1027_CONTROL_VARIABLE_PROTOCOL.md`
commit `b4dca895d4c78fa6e02c8d0b13e34d1b37b55c0f`.

Older V2 prespecification:
`CHECKPOINT_20260830_TEMP_ACCURACY_V2_PRESPEC.md`
commit `ed3f084fb4139b355593d5bf403c40da54baf071`.
Where the older prespecification is more elaborate than the latest user-approved protocol, the 10:27 control-variable checkpoint governs.

## 7. Teacher-facing optimization-effect briefing finalized
A teacher-facing report has been finalized before starting new V2 optimization experiments. It covers:
- original DSSAT HTEMP / CERES extreme-DTT pathway versus M15 Xinjiang high-DTR pathway;
- Shihezi thesis reference framework and the frame-level reproduction/control-variable boundary;
- three-line tables for temperature accuracy and crop-yield accuracy;
- 13.0/13.5/13.8/14.0/14.8 threshold comparison and the exact selection logic for 13.5/13.8;
- innovation claims and exact Weather/HMET.for, MZ_CERES.for, MZ_PHENOL.for modification points;
- reproducibility locks and next-step control-variable experiment rule.

GitHub text version:
`research/dssat_dtr/TEACHER_BRIEF_20260830_M15_XINJIANG_TEMP_OPTIMIZATION.md`
commit `6a8e0ee451759dae3dd3416c88c1d4f14d82fd13`.

The formatted DOCX was generated and visually QA-checked page-by-page (8 pages) in the ChatGPT artifact environment. No baseline algorithm/data package was modified to create this briefing.

## 8. Immediate next action
Build the first low-dimensional temperature-shape control-variable candidates from frozen M15-13.5, evaluate them on the same frozen temperature validation chain, then propagate passing candidates through the identical frozen crop cases and append results to a unified temperature-RMSE versus yield-RRMSE matrix.
