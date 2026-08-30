# M15-V2 Round 1: post-peak power warp — prespecification

Date: 2026-08-30
Branch: `research/dssat-m15-temp-accuracy-v2`

## Frozen controls

- Official DSSAT HTEMP is unchanged as M0.
- M15-13.5 is the primary frozen control: `DTRc = 13.5 C`, `alpha = 6.407985379809223`.
- M15-13.8 remains a frozen robustness control and is not retuned here.
- No v1 release/package file may be changed.
- Crop observations, yield, phenology, ET, irrigation and fertilizer are prohibited from fitting or selecting the temperature parameter in this round.

## Candidate mechanism

Only the M15 modeled-Tmax-to-sunset segment is changed. M15 first computes the frozen sunset anchor `TS1` exactly as before and the official normalized cooling progress

`R = (TMAX - T_official) / (TMAX - TS0)`, clamped to `[0,1]`.

Round-1 candidate uses

`R_p = R^p`

`T_V2 = TMAX - (TMAX - TS1) * R_p`.

All pre-peak temperatures, the frozen `TS1`, sunset continuity, nighttime `B=2.2` decay and the activation rule `(DTR > 13.5 C and CLOUDS > 0)` remain unchanged.

`p = 1.0` must reproduce frozen M15-13.5 exactly. This is a hard execution check.

## Parameter search

- Physical search interval: `0.50 <= p <= 1.50`.
- Coarse grid: step `0.05`.
- Fine grid: `+/-0.05` around the coarse optimum, step `0.005`, clipped to the physical interval.
- Values below 0.50 are excluded because the near-peak cooling derivative becomes excessively sharp for this power form.

## Calibration and validation hierarchy

1. Reconstruct dense Diwopu station `51463599999` May-Sep hourly observations from NOAA Global Hourly using the already-audited solar-time conversion and quality filters.
2. Use existing NASA POWER daily SRAD to calculate DSSAT-consistent `CLOUDS`.
3. Fit/select `p` on 2000-2016 dense-station data only.
4. Selection objective: mean RMSE across four contiguous calibration blocks for active-day post-peak-to-sunset observations: 2000-2004, 2005-2008, 2009-2012, 2013-2016.
5. A non-unit candidate must improve at least 3/4 calibration blocks versus `p=1`; otherwise freeze `p=1` and classify the mechanism as calibration-unstable.
6. Freeze `p` before reading any 2017-2024 validation score.
7. Evaluate the frozen candidate on dense-station 2017-2024 and target station `51463099999` 2017-2024 without refitting.

## Hard reproducibility checks

At `p=1` on target-station validation, the existing pipeline must reproduce:

- May-Sep `n = 5917` and RMSE `2.796223546 C` for M15-13.5.
- DTR>=15 RMSE `4.634433256 C` for M15-13.5.
- Pointwise `p=1` predictions must equal the frozen M15 function within numerical tolerance.

Failure of any baseline check invalidates this run.

## Independent metrics

Report at minimum:

- hourly RMSE, MAE, bias and R2;
- active post-peak-to-sunset RMSE;
- DTR>=15 RMSE and bias;
- dense-station validation metrics;
- target-station year-by-year stability;
- physical monotonicity, Tmin/Tmax bounds and TS-cap count.

## Round-1 KEEP gate

The candidate enters DSSAT source/crop propagation only if all conditions hold after parameter freeze:

1. dense-station 2017-2024 active post-peak RMSE is no worse than `p=1`;
2. target-station May-Sep RMSE improves by at least `0.03 C` versus frozen M15-13.5;
3. target-station DTR>=15 RMSE is no worse than frozen M15-13.5 by more than `0.01 C`;
4. physical shape violations remain zero;
5. no more than two valid target years have worse May-Sep RMSE than frozen M15-13.5.

If the KEEP gate fails, record `DROP_POSTPEAK_POWER` and proceed to the prespecified nighttime-decay refinement. Crop results do not rescue a temperature candidate that fails this gate.
