# DSSAT M15 temperature-accuracy V2 prespecification

Date: 2026-08-30
Branch: `research/dssat-m15-temp-accuracy-v2`

## Frozen baselines

The completed M15-13.5 and M15-13.8 artifacts and their scientific interpretation are immutable baselines.

- Primary baseline: DTRc=13.5 C, alpha=6.407985379809223
- Robustness baseline: DTRc=13.8 C, alpha=6.749813473189908
- Final lower-bound audit: run 33259349242
- Freeze checkpoint: ef34289f50d889e15de9df1d0a0323c21b36f20c

No V2 experiment may overwrite, silently refit, or relabel these baselines.

## New scientific question

Determine whether additional improvement in independently validated hourly-temperature reconstruction produces consistent improvement in CERES-Maize thermal-time, phenology, and yield accuracy.

The relationship is to be tested empirically rather than assumed to be strictly monotonic, because crop response depends on the timing and physiological relevance of the temperature error as well as on radiation, water, nitrogen, cultivar and management inputs.

## Important existing observation

Current frozen evidence already shows that aggregate temperature RMSE and crop RRMSE do not rank the two variants identically:

- M15-13.5 independent May-Sep temperature RMSE = 2.7962 C; SRAD19P8_N_OFF ALL8 crop RRMSE = 25.497%.
- M15-13.8 independent May-Sep temperature RMSE = 2.8015 C; SRAD19P8_N_OFF ALL8 crop RRMSE = 24.012%.

Therefore the next stage should improve temperature reconstruction itself and then test which temperature-error components propagate to crop response.

## V2 optimization principle

Do not continue a blind downward DTRc search. Keep the frozen threshold variants as controls and investigate shape accuracy inside the activated regime.

Candidate extensions should be added one mechanism at a time, with low degrees of freedom and explicit physical bounds. Priority order:

1. Peak-to-sunset cooling-shape refinement while retaining the observed sunset-anchor mechanism.
2. Nighttime decay refinement with bounded parameterization around the official Parton-Logan B=2.2 structure.
3. Nonlinear but low-dimensional CLOUDS response if calibration diagnostics support it.
4. Smooth transition near DTRc only if hard-threshold discontinuity is shown to create measurable error.

Complex neural or high-dimensional residual corrections are out of scope until these physically interpretable extensions are exhausted.

## Temperature-only model selection

All new parameters must be fitted using the existing temperature calibration chain only. Crop yield, phenology, ET and irrigation observations are prohibited from parameter fitting or temperature-model selection.

Primary independent temperature metrics:

- hourly RMSE / MAE / bias / R2;
- DTR>=15 C RMSE and bias;
- sunset and nighttime RMSE;
- year-by-year stability;
- complete-curve physical-shape violations;
- Tmin/Tmax bound violations and cap frequency.

Crop-relevant temperature diagnostics, still independent of crop yield, should also be reported:

- daily thermal-time error under the CERES temperature clipping rules;
- degree-hour error above heat thresholds;
- timing error of high-temperature exposure;
- phase-specific temperature error where independently observed phenology permits stage assignment.

## Validation hierarchy

1. Fit only on the frozen calibration period/station.
2. Use blocked-year internal calibration diagnostics to control overfitting.
3. Freeze parameters.
4. Evaluate untouched target-station available observations within 2017-2024.
5. Pass physical-shape QA.
6. Only after temperature-side selection, propagate candidates through identical CERES-Maize crop inputs.

## Crop propagation test

For every temperature candidate that passes the independent temperature gate, run the same crop/soil/management/weather cases through:

- official/reference pathway;
- frozen M15-13.5;
- frozen M15-13.8;
- new V2 candidate.

Report HWAM, ADAT, MDAT, ET and stress diagnostics where available. Shared crop inputs must be byte-identical across model arms.

The key V2 research result is the empirical mapping between improvements in different temperature-error components and improvements in crop outputs. This will establish which aspects of hourly-temperature accuracy actually matter for yield prediction.

## Stop / acceptance rule

A V2 candidate is scientifically useful only when it:

- improves independent temperature accuracy beyond the frozen baselines by a reproducible amount;
- does not worsen high-DTR behavior or physical QA;
- remains stable across years;
- adds limited, interpretable parameter freedom;
- and subsequently shows equal or improved crop propagation without using crop data during temperature fitting.

If a candidate improves aggregate temperature RMSE but degrades crop propagation, retain that result as evidence that temperature-error timing/structure matters more than aggregate RMSE alone.
