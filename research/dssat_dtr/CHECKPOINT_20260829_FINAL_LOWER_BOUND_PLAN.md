# Final lower-bound DTRc audit prespecification

Timestamp: 2026-08-29 CST
Branch: `research/dssat-dtr-matrix`

## Reason

The prespecified 14.0 / 14.3 / 14.5 / 14.8 C ablation ranked 14.0 C best on independent 2017-2024 hourly-temperature validation, and 14.0 C was the lowest tested boundary. Therefore one final lower-bound audit is required before declaring the threshold final.

## Candidate set

Primary candidates:
- 13.5 C
- 13.8 C
- 14.0 C current leader/reference

Optional aggressive lower-bound negative control:
- 13.0 C

Do not continue below 13.0 C without new mechanism evidence.

## Selection rule

Threshold and alpha selection remain temperature-only. Crop yield is prohibited as a fitting or selection objective.

For each DTRc:
1. fit alpha using only the existing temperature calibration chain;
2. test untouched 2017-2024 independent hourly validation;
3. report May-Sep RMSE/MAE/bias/R2;
4. report DTR strata around 13-15, 15-18, 18-20, >=20 C;
5. report active days, TS caps and complete-curve physical violations;
6. inspect year-by-year robustness.

Only after a final temperature-side threshold is frozen may it propagate to the identical Shihezi crop comparison.

## Stop rule

This is the final threshold-boundary search. Stop if performance plateaus/worsens below 14.0 C or if physical/bias behavior degrades. The project must not descend thresholds indefinitely to maximize crop or temperature metrics.
