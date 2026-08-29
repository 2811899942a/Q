# DSSAT-DTR Urumqi Research Handoff

Last checkpoint: 2026-08-29 13:07 CST
Branch: `research/dssat-dtr-matrix`
Study: Urumqi DSSAT v4.8.5.0 HTEMP improvement

## Frozen software baseline — PASS

Formal source/data baseline is fixed:
- `DSSAT/dssat-csm-os` tag `v4.8.5.0`, commit `0b91373806786b600d89ccfcfff78fa2f82cb26b`
- `DSSAT/dssat-csm-data` tag `v4.8.5.0`, commit `79cb5db71bbca186add92a6a9695866a09c8b51d`
- official regression case `Maize/UFGA8201.MZX`, 6 treatments, executable `dscsm048`

Corrected GitHub Actions completed the full chain successfully: exact checkout -> compile/install -> matching data -> real UFGA8201 run -> `Summary.OUT` + `PlantGro.OUT` acceptance -> hashes/snapshot committed.
Frozen baseline: `research/dssat_dtr/data/dssat485_m0_official/`.

## Confirmed local mechanism

Primary station: NOAA `51463099999` + GHCN `CHM00051463`.
Formal calibration-only trigger: `DTRc=14.8 C`.

Evidence:
- below this regime official HTEMP performs much better;
- above ~14-15 C, afternoon/hot-shoulder warm bias rises sharply;
- radiation/cloudiness strongly modulates error severity;
- DSSAT v4.8.5.0 already computes native `CLOUDS=clamp(1-SRAD/SCLEAR,0,1)` and passes it to `HMET`, so no new weather variable is needed.

## Statistical reference M10

Independent 2017-2024 DTR>=15 C:
- official RMSE 5.1215 C
- M10 RMSE 4.4196 C
- improvement 13.71%
- Bias +1.2167 -> +0.4936 C
- R2 0.5559 -> 0.6107
- 5/5 validation years improved
- day-block bootstrap improvement 95% CI 10.76%-16.54%.

M10 remains a statistical reference only.

## M12 native-CLOUDS additive prototype — mechanism retained, formula rejected

M12 replaced Kt with native DSSAT CLOUDS and retained nearly all performance:
- high-DTR RMSE 5.1215 -> 4.4332 C = 13.44% improvement
- R2 0.5559 -> 0.6163.

But full 24-hour shape QA found severe physical violations:
- 113/130 validation high-DTR days non-monotonic on the rising branch
- 52/130 non-monotonic on falling branch
- 37/130 below daily Tmin
- maximum Tmin undershoot >51 C.

Decision: retain `DTR x CLOUDS` mechanism; NEVER implement M12 additive subtraction directly in Fortran.

## M13 monotonic power warp — physically valid but weak

Endpoint-preserving transform `q_new=q^p`, with `p=1+k*(DTR-DTRc)*CLOUDS`, starting at solar noon.

Result:
- k_pre=20.0, hit search upper boundary
- k_post=16.46
- 0/130 validation physical violations
- high-DTR RMSE 5.1215 -> 4.9022 C = 4.28% improvement.

Decision: reject as final source candidate. Starting the pre-peak deformation at solar noon is too late and the pre branch remains under-flexible.

## Calibration-only high-DTR hourly residual profile

2000-2016 May-Sep DTR>14.8 C, primary station:
- ~08.85 solar h: mean Bias +0.538 C but median Bias -0.839 C
- ~11.85 h: mean +3.892 C, median +0.728 C
- ~14.85 h: mean +5.016 C
- ~17.85 h: mean +4.533 C
- ~20.85 h: mean +1.384 C
- ~23.85 h: mean -1.135 C.

Because the sparse 8.85-h bin mean is outlier-sensitive, the robust calibration median residual changes sign between 8.85 and 11.85 h.

## M14 robust crossover monotonic warp — improved but still insufficient

Calibration-only median-residual crossover:
`H0 = 10.455 solar hour`.

M14 applies the same monotonic power warp from H0 -> modeled Tmax and Tmax -> sunset.

Independent 2017-2024:
- 0/130 physical violations
- May-Sep RMSE 2.9469 -> 2.8376 C = 3.71%
- high-DTR RMSE 5.1215 -> 4.7408 C = 7.43%
- high-DTR Bias +1.2167 -> +0.7443 C
- R2 0.5559 -> 0.5756
- k_pre=20.0 still hits upper bound; k_post=16.455.

Decision: M14 is evidence that earlier deformation helps, but it does not meet the source-candidate criterion and the power-warp family should not be tuned further.

## Dense Urumqi Diwopu evidence

Second station `51463599999` is still within Urumqi and provides dense real-hour observations:
- 8,806 days with >=20 solar-hour observations
- 3,790 May-Sep days.

Dense station official HTEMP RMSE breakpoint:
- all years 12.7 C
- calibration 2000-2016 12.8 C
- validation 2017-2024 13.4 C.

Tmax timing does NOT show a strong general high-DTR shift (median around 14.9 solar h for DTR>=14.5 in calibration), so dynamic Tmax timing is not the main mechanism.

Dense validation 14.5-18 C DTR Bias grows through the afternoon:
- 12 h +0.690 C
- 14 h +0.898 C
- 15 h +1.225 C
- 17 h +1.478 C
- 18 h +1.793 C
- 19 h +2.018 C.

This points to excessive post-peak / late-afternoon thermal persistence and possibly an overly warm DSSAT sunset-temperature anchor `TS`.

## Current calculation

A dedicated dense-station sunset-anchor diagnostic is running now:
`diagnose_dense_sunset_anchor_514635.py`
workflow: `dense-sunset-anchor-514635.yml`.

It compares official `T_PL(SNDN)` with the real observation nearest sunset and fits, on dense-station calibration years only:
`sunset_error = alpha * max(0,DTR-14.8) * CLOUDS`.
Then 2017-2024 dense years are untouched validation.

Decision rule:
- change DSSAT sunset anchor only if raw high-DTR sunset bias is materially positive;
- DTR x CLOUDS relationship persists independently;
- frozen calibration alpha reduces validation sunset RMSE without large negative bias.

If supported, next prototype will adjust the sunset anchor and construct a monotonic peak-to-sunset curve around it; if not supported, keep original sunset anchor and pursue a different bounded monotonic post-peak shape.

## User-input conditions

Do not ask the user to run DSSAT locally. Continue with GitHub/public data. Stop for user input only if a public-data gap blocks a defensible Anningqu 2021-2022 maize reconstruction or a genuinely major modeling decision is reached.
