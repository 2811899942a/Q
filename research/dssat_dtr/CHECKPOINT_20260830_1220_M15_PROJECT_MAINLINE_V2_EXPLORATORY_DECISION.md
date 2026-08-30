# Project decision — retain frozen M15 as production mainline; demote V2 to exploratory evidence

Time: 2026-08-30 12:20 CST
Branch: `research/dssat-m15-temp-accuracy-v2`

## Decision
For the Xinjiang/Urumqi DSSAT research project, the formal production/deployment temperature algorithm remains the frozen M15 family rather than promoting the current V2 refinement to the project mainline.

Production arms remain:
- Primary: M15-13.5, DTRc=13.5 C, alpha=6.407985379809223.
- Robustness/sensitivity: M15-13.8, DTRc=13.8 C, alpha=6.749813473189908.

The V2 candidate (`DTRc=13.5 C`, `alpha=6.407985...`, post-peak `p=0.5`, `Bnight=1.05`) is retained as an exploratory/ablation result and must not overwrite or replace the frozen M15 package.

## Why M15 remains the project mainline
1. M15 already has a completed threshold audit, frozen calibration/validation chain, source-level implementation audit, physical-shape QA and project deployment package.
2. M15 is structurally simpler and easier to interpret: it introduces a high-DTR activation threshold plus a sunset-anchor correction while preserving most of the official Parton-Logan curve.
3. The current V2 improves independent target-station temperature RMSE from M15-13.5 2.7962 C to 2.7247 C, but this is an incremental refinement of curve shape rather than a new project-level mechanism.
4. Crop improvement relative to M15-13.8 is negligible in magnitude: ALL8 RRMSE 24.012204% (M15-13.8) versus 23.983874% (V2), only 0.028330 percentage points better.
5. V2 crop validation is currently demonstrated only through the frozen CERES-Maize Shihezi control-variable case. It does not yet justify stronger cross-crop or Xinjiang-wide deployment claims.
6. Therefore the additional V2 complexity is not justified for the formal project mainline at the present evidence level.

## Scientific use of V2 results
V2 results are still valuable and must be preserved because they show:
- post-peak shape refinement can reduce hourly-temperature RMSE without changing yield;
- nighttime decay refinement can alter CERES thermal-time/phenology and improve yield relative to M15-13.5;
- aggregate hourly-temperature RMSE alone is not sufficient to predict crop-yield improvement;
- the physiological timing/location of temperature error matters.

These results can be used as mechanistic ablation/sensitivity evidence, discussion material, or future-method extension, but not as the current production model.

## Formal comparison retained
Frozen baselines:
- Official DSSAT: temperature RMSE 2.946891175 C; crop RRMSE 26.9147158%.
- M15-13.5: 2.796223546 C; 25.4973651%.
- M15-13.8: 2.801548624 C; 24.0122042%.
- V2 exploratory best: 2.7247 C; 23.983874%.

For formal project reporting, emphasize the robust and already frozen improvement from official DSSAT to M15. V2 may appear only as an exploratory extension unless new evidence is deliberately added later.

## Operational rule
Do not continue V2 parameter searching as the current project priority. Do not modify the frozen M15 release/package. Future project simulations should use M15-13.5 as primary and M15-13.8 as robustness/sensitivity unless a new explicit decision supersedes this checkpoint.
