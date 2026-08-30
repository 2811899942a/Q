# M15-V2 Round 2: finite-slope post-peak warp — prespecification

Date: 2026-08-30
Branch: `research/dssat-m15-temp-accuracy-v2`

This prespecification is committed before reading Round-1 crop-propagation output. Crop results cannot influence this temperature experiment.

## Motivation fixed from Round-1 temperature evidence

Round 1 selected the physical lower bound `p=0.5` for `R^p`. It improved all four calibration blocks and independently improved target May-Sep RMSE from 2.796223546 to about 2.7631 C, with zero physical violations. Hitting the lower bound indicates a reproducible need for faster early post-peak cooling, while extending `p<0.5` would further sharpen the derivative near `R=0` and is excluded.

## Candidate family

Keep frozen M15-13.5 sunset correction unchanged:

- `DTRc = 13.5 C`
- `alpha = 6.407985379809223`
- activation `(DTR > DTRc and CLOUDS > 0)`
- pre-peak official HTEMP unchanged
- corrected sunset anchor `TS1` unchanged
- nighttime `B=2.2` unchanged

Only modeled-Tmax-to-sunset normalized progress changes from `R` to

`R_k = R + k * R * (1 - R)`

and

`T = TMAX - (TMAX - TS1) * R_k`.

Properties for `0 <= k <= 1`:

- exact endpoints: `R_k(0)=0`, `R_k(1)=1`;
- finite derivative: `dR_k/dR = 1 + k(1-2R)`;
- monotonic nondecreasing because the minimum derivative is `1-k >= 0`;
- `k=0` exactly reproduces frozen M15-13.5;
- `k=1` gives at most 2x initial normalized cooling slope and zero endpoint slope, avoiding the singular near-peak derivative of `sqrt(R)`.

## Parameter selection

- Search interval: `0 <= k <= 1`.
- Coarse grid step 0.05.
- Fine grid +/-0.05 around the coarse optimum, step 0.005.
- Calibration source: Diwopu `51463599999`, May-Sep, 2000-2016 only.
- Objective: mean active post-peak RMSE across the same four contiguous blocks used in Round 1: 2000-2004, 2005-2008, 2009-2012, 2013-2016.
- A nonzero k must improve at least 3/4 blocks versus k=0, otherwise freeze k=0.
- k is frozen before any 2017-2024 score is computed.

## Independent validation hierarchy

Evaluate after freeze on:

1. Diwopu dense 2017-2024 May-Sep / active post-peak / DTR>=15.
2. Target station `51463099999` available 2017-2024 May-Sep / DTR>=15.
3. Target year-by-year stability.
4. Physical shape and Tmin/Tmax bounds.

Hard k=0 reproduction must recover M15-13.5 target May-Sep RMSE 2.796223546 C and DTR>=15 RMSE 4.634433256 C.

## Incremental KEEP gate versus Round-1 p=0.5

Round 2 is promoted over Round-1 `p=0.5` only if all hold:

1. nonzero k is stable in at least 3/4 calibration blocks;
2. dense 2017-2024 active-postpeak RMSE is no worse than Round-1 p=0.5;
3. target May-Sep RMSE improves by at least 0.01 C versus Round-1 p=0.5;
4. target DTR>=15 RMSE is no worse than Round-1 p=0.5 by more than 0.01 C;
5. physical shape violations remain zero;
6. no more than two target years have worse May-Sep RMSE than Round-1 p=0.5.

If this gate fails, retain Round-1 `p=0.5` as the current temperature winner and move to a separately bounded nighttime-decay experiment. No crop result can rescue a Round-2 candidate that fails the temperature gate.
