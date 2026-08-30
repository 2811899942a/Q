# M15-V2 Round 4: nonlinear CLOUDS exponent — prespecification

Date: 2026-08-30
Branch: `research/dssat-m15-temp-accuracy-v2`

## Frozen incoming structure

- `DTRc = 13.5 C`
- post-peak `p = 0.5`
- nighttime `Bnight = 1.05`
- current sunset correction is linear in CLOUDS with `gamma=1` and `alpha=6.407985379809223`.

Crop output is prohibited from selection.

## Candidate

Replace only the sunset-correction amplitude relation by

`DTS = alpha_gamma * max(0, DTR-13.5) * CLOUDS^gamma`

with `gamma > 0`.

Everything else is frozen: activation rule, official pre-peak curve, corrected-sunset lower bound at Tmin, p=0.5 post-peak progression and Bnight=1.05 night decay.

`gamma=1` with calibration-refit alpha must reproduce the current linear CLOUDS coefficient and Round-3 temperature predictions within numerical tolerance.

## Leakage-resistant gamma selection

Calibration data are dense-station sunset observations from 2000-2016 only. Four contiguous blocks are fixed:

- 2000-2004
- 2005-2008
- 2009-2012
- 2013-2016

For each candidate gamma and each held-out block:

1. fit `alpha_gamma = sum(x*y)/sum(x^2)` using the other three blocks only, where `x=max(0,DTR-13.5)*CLOUDS^gamma` and `y=official sunset error`;
2. evaluate corrected sunset RMSE in the held-out block;
3. average the four held-out RMSE values as the gamma objective.

Search:

- gamma interval 0.50-2.00;
- coarse step 0.10;
- fine step 0.01 within +/-0.10 of the coarse optimum;
- non-unit gamma must improve at least 3/4 held-out blocks versus gamma=1.

After gamma is selected, fit one final alpha on all 2000-2016 calibration sunset observations and freeze `(gamma, alpha)` before any 2017-2024 evaluation.

## Independent validation

Compare current Round-3 `(gamma=1, alpha=6.407985..., p=.5, B=1.05)` against the frozen Round-4 candidate on:

- dense 2017-2024 sunset RMSE/bias;
- dense 2017-2024 May-Sep hourly RMSE, active-regime RMSE and DTR>=15;
- target 514630 May-Sep and DTR>=15;
- target year-by-year stability;
- physical shape/Tmin/Tmax QA.

## Promotion gate

Promote Round 4 only if all conditions hold:

1. non-unit gamma improves >=3/4 held-out calibration blocks;
2. independent dense sunset RMSE is no worse than gamma=1;
3. independent dense full May-Sep hourly RMSE is no worse than Round 3;
4. target May-Sep RMSE improves by >=0.01 C versus Round 3;
5. target DTR>=15 RMSE degrades by no more than 0.01 C;
6. physical shape violations are zero;
7. no more than two valid target years worsen versus Round 3.

If the gate fails, retain Round 3 (`gamma=1, p=.5, B=1.05`) and do not use crop output to rescue Round 4.
