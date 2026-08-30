# M15-V2 Round 3: bounded nighttime-decay B — prespecification

Date: 2026-08-30
Branch: `research/dssat-m15-temp-accuracy-v2`

## Frozen incoming temperature model

Round 1 remains the current temperature winner after Round 2 failed its independent promotion gate:

- `DTRc = 13.5 C`
- `alpha = 6.407985379809223`
- peak-to-sunset warp `R_p = sqrt(R)` (`p=0.5`)
- nighttime decay remains official `B=2.2`

No crop result is used in this round.

## Candidate mechanism

Only the active-regime nighttime exponential coefficient is changed from `B=2.2` to a single constant `Bnight`.

For `DTR > 13.5 C` and `CLOUDS > 0`, after sunset / before modeled Tmin:

`EB = exp(-Bnight)`

`TMINI1 = (TMIN - TS1*EB)/(1-EB)`

`T = TMINI1 + (TS1-TMINI1)*exp(-Bnight*t/HDECAY)`

This retains the frozen corrected sunset anchor `TS1`, reaches the daily Tmin at the same modeled Tmin time, keeps the same `HDECAY`, and changes only nighttime curvature. Pre-peak official HTEMP and the frozen `p=0.5` peak-to-sunset branch remain unchanged.

`Bnight=2.2` must exactly reproduce Round-1 `p=0.5` pointwise.

## Parameter search

- Physical search interval: `1.0 <= Bnight <= 3.5`.
- Coarse grid: step 0.10.
- Fine grid: +/-0.10 around coarse optimum, step 0.01, clipped to the interval.
- Calibration source: dense Diwopu `51463599999`, May-Sep 2000-2016 only.
- Selection observations: active-regime nighttime points (`hour > sunset` or `hour < modeled Tmin time`).
- Objective: mean nighttime RMSE across four contiguous blocks: 2000-2004, 2005-2008, 2009-2012, 2013-2016.
- A non-2.2 candidate must improve at least 3/4 blocks and overall calibration active-night RMSE; otherwise retain 2.2.
- Freeze `Bnight` before computing any 2017-2024 validation score.

## Independent validation

After freeze, compare Round-1 `p=0.5, B=2.2` and the candidate on:

- dense Diwopu 2017-2024: May-Sep, active-night, DTR>=15;
- target station 514630: May-Sep, DTR>=15;
- target year-by-year RMSE;
- physical monotonicity and Tmin/Tmax bounds.

Hard baseline reproduction must recover the committed Round-1 p=0.5 target RMSE values exactly within numerical tolerance.

## KEEP gate

Promote the nighttime candidate only if all conditions hold:

1. non-2.2 `Bnight` improves at least 3/4 calibration blocks;
2. dense independent active-night RMSE is no worse than B=2.2;
3. target May-Sep RMSE improves by at least 0.01 C versus Round-1 p=0.5;
4. target DTR>=15 RMSE is no worse by more than 0.01 C;
5. physical shape violations remain zero;
6. no more than two valid target years have worse May-Sep RMSE than Round-1 p=0.5.

If the gate fails, retain `p=0.5, B=2.2` and move to the prespecified low-dimensional CLOUDS-response refinement. Crop output cannot rescue a failed temperature candidate.
