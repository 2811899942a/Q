# M15 trigger-threshold expansion plan

Timestamp: 2026-08-29 CST
Branch: `research/dssat-dtr-matrix`

## Why this checkpoint exists

The user proposed increasing the number of Xinjiang large-DTR days that enter the M15 correction. This is scientifically plausible, but must be tested without tuning to crop yield.

## Current evidence

- Frozen M15 uses `DTRc=14.8 C`, `alpha=7.8094`.
- Urumqi DTR breakpoint diagnostics place the structural transition at about 14.3-15.0 C:
  - daily RMSE breakpoint 14.3 C
  - afternoon bias 14.6 C
  - afternoon-minus-morning bias 14.5 C
  - four-diagnostic mean 14.60 C
- Shihezi crop seasons contain 46 DTR>14.8 C days in both 2019 and 2020, about 31% of analyzed days. DTR>=18 C occurs only 3 and 4 days; DTR>=20 C only 0 and 1 day.
- Extreme-DTR crop ablation shows that >=18 C days reproduce only a small fraction of the full M15 crop response in the SRAD19P8_N_OFF case, implying that the 14.8-18 C large-DTR regime is important for crop propagation.

## Interpretation

If the objective is to increase the number of days entering M15, the DTR trigger must be lowered, not raised. The existing 14.8 C threshold is slightly conservative relative to the empirical breakpoint range; lowering it modestly toward 14.3-14.5 C is scientifically testable. A large reduction to 12-13 C is not currently supported by the breakpoint evidence.

## Hard rule

Do not replace frozen M15 directly and do not select a threshold using crop yield.

## Next sensitivity experiment

Create separate candidate arms while retaining M15 (`14.8 C`) as the frozen reference:
- `M15_T14P8`: current frozen reference
- `M15_T14P5`
- `M15_T14P3`
- optional boundary sensitivity `M15_T14P0`

For each candidate, threshold and sunset coefficient must be evaluated/recalibrated only from hourly-temperature calibration data. Then use untouched independent hourly validation to compare:
1. overall May-Sep RMSE/bias/R2;
2. DTR 13-15, 15-18, 18-20, >=20 C performance;
3. physical-shape violations;
4. number/proportion of days entering the correction.

Only after the temperature-side choice is frozen may the candidate enter the identical Shihezi crop experiment. Crop yield is a downstream validation endpoint, never the threshold-selection objective.

## Current working hypothesis

A modest reduction of the trigger from 14.8 C toward about 14.3-14.5 C may increase coverage of Xinjiang large-DTR transition days while retaining the mechanism-based justification. The expected gain must be demonstrated by temperature validation first.
