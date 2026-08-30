# M15-V2 Round 5: nighttime-B lower-bound extension audit — prespecification

Date: 2026-08-30
Branch: `research/dssat-m15-temp-accuracy-v2`

## Rationale fixed before execution

Round 3 selected `Bnight=1.05` from the prespecified interval 1.0-3.5, close to the imposed lower boundary. The selected model independently improved dense nighttime RMSE, target May-Sep RMSE, target DTR>=15 RMSE, all six valid target years, and downstream Shihezi crop RRMSE.

The present audit tests whether the previous lower bound constrained the optimum. No crop data or crop output are used for fitting or selection.

## Frozen structure

- `DTRc = 13.5 C`
- `alpha = 6.407985379809223`
- post-peak `p=0.5`
- CLOUDS exponent `gamma=1`
- only active-regime nighttime `Bnight` changes.

The exact sunset anchor, pre-peak official HTEMP, post-peak sqrt(R) warp and activation rule remain frozen.

## Search interval

- audit interval: `0.50 <= Bnight <= 1.10`;
- coarse step: 0.05;
- fine step: 0.005 within +/-0.05 of the coarse optimum;
- `Bnight=1.05` is the Round-3 baseline and must reproduce its committed predictions exactly.

For any `Bnight>0`, the same endpoint-constrained exponential form is retained:

`TMINI1 = (TMIN - TS1*exp(-B))/(1-exp(-B))`

`T = TMINI1 + (TS1-TMINI1)*exp(-B*t/HDECAY)`.

Physical shape/Tmin/Tmax QA remains mandatory.

## Calibration-only selection

Use dense Diwopu active-regime nighttime observations, May-Sep 2000-2016 only.

Four fixed contiguous blocks:
- 2000-2004
- 2005-2008
- 2009-2012
- 2013-2016

Objective: mean block RMSE. A candidate must improve at least 3/4 blocks versus B=1.05 and reduce overall calibration active-night RMSE. Freeze B before any 2017-2024 metric is computed.

## Independent promotion gate versus Round 3 B=1.05

Promote only if all conditions hold:

1. candidate differs from 1.05 and improves >=3/4 calibration blocks;
2. dense 2017-2024 active-night RMSE is no worse than B=1.05;
3. target May-Sep RMSE improves by >=0.01 C;
4. target DTR>=15 RMSE degrades by <=0.01 C;
5. physical shape violations remain zero;
6. no more than two valid target years worsen.

If the selected candidate equals the new lower boundary `B=0.50`, classify as `LOWER_BOUND_NOT_CLOSED` even if it passes the promotion metrics; do not treat 0.50 as a final parameter without a further lower-bound audit.

If an interior candidate passes, classify `PROMOTE_INTERIOR_B`. Otherwise retain Round 3 B=1.05.
