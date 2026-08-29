# DSSAT-DTR Urumqi Research Handoff

Last checkpoint: 2026-08-29
Branch: `research/dssat-dtr-matrix`
Study station: NOAA 51463099999 / GHCN CHM00051463, Urumqi

## Current task

Develop a Urumqi-specific DSSAT HTEMP improvement from local residual structure rather than copying an existing temperature model. The current mechanism being tested is a DTR-threshold-triggered narrowing of the overly broad daytime hot shoulder in the original DSSAT Parton-Logan reconstruction.

## Confirmed data and baseline results

- NOAA ISD / Global Hourly 51463099999, 2000-2024 processed successfully.
- 72,177 real sub-daily temperature observations available; typical frequency ~8 observations/day.
- GHCN-Daily CHM00051463 provides formal daily Tmax/Tmin and DTR.
- Original DSSAT HTEMP was reproduced from `Weather/SOLAR.for::DAYLEN` and `Weather/HMET.for::HTEMP` using A=2.0, B=2.2, C=1.0.
- Original baseline matched 55,756 observation-model points over 7,036 days.
- May-Sep original RMSE ≈ 2.58-2.95 C depending on period split.
- Error grows strongly with DTR; DTR >=15 C is the robust high-DTR group.

## Local mechanism findings

1. DTR error is threshold-like rather than simply linear.
2. Best change points in May-Sep:
   - Morning bias: 15.0 C
   - Afternoon bias: 14.6 C
   - Afternoon-minus-morning bias: 14.5 C
   - Daily RMSE: 14.3 C
   - Four-diagnostic mean: 14.60 C
3. Calibration/validation breakpoint differences are all <=1.2 C, indicating temporal stability.
4. Morning cold bias increases gradually with DTR, but no strong structural breakpoint is supported there.
5. The strongest structural failure occurs in the afternoon / high-temperature shoulder: above ~14.5 C DTR, afternoon warm bias and daily RMSE rise sharply.
6. Therefore the current local hypothesis is: **DTR-triggered excessive daytime hot-shoulder persistence**, especially around the afternoon branch.

## Tested modifications

### PL-XJ fixed A/B/C regional calibration
- Helps only modestly (~5% RMSE improvement under high DTR).
- Residual high-DTR error remains large.
- Conclusion: fixed parameter regionalization is insufficient.

### One-sided post-peak correction
Formula:
`T_new = T_PL - alpha*(DTR-14.5)*4*u*(1-u)`
for DTR>14.5 C between modeled peak and sunset.

- Analytic alpha later estimated at ~2.85.
- Independent validation DTR>=15 C:
  - official RMSE 5.1215 C
  - corrected RMSE 4.8629 C
  - improvement 5.05%
- Useful but cannot correct the 14:00 hot shoulder because it starts too late.

### Dynamic A test
For DTR>14.5 C:
`A_dynamic = max(0, 2 - gamma*(DTR-14.5))`
with gamma ≈0.575 h per excess DTR degree.

- Independent validation DTR>=15 C RMSE 4.9249 C, improvement 3.84%.
- Bias reduced strongly, but dynamic A alone is weaker than shoulder correction.
- Combining dynamic A + post-peak correction gives RMSE 4.8558 C but causes negative overall high-DTR bias (-0.50 C), suggesting over-correction.

### Two-sided hot-shoulder narrowing (latest result)
For DTR>14.5 C, keep original DSSAT Tmax anchor unchanged and narrow both sides of the hot shoulder:
- pre-peak correction between solar noon and modeled Tmax;
- post-peak correction between modeled Tmax and sunset;
- correction is zero at solar noon, modeled Tmax, and sunset.

Fitted on 2000-2016 May-Sep:
- alpha_pre = 13.333
- alpha_post = 2.850

Independent validation 2017-2024, DTR>=15 C:
- Official RMSE = 5.1215 C
- Two-sided RMSE = 4.6567 C
- RMSE improvement = 9.07%
- MAE: 3.7612 -> 3.5922 C
- Bias: +1.2167 -> -0.0954 C
- R2: 0.5559 -> 0.5485

Key hourly effect:
- 14:00 RMSE: 4.0302 -> 3.6742 C; Bias +2.4090 -> +1.4102 C
- 17:00 RMSE: 3.9514 -> 3.4640 C; Bias +2.2324 -> +1.4100 C
- 15:00 and 18:00 sparse samples remain poorly corrected because the chosen anchor geometry limits correction exactly near modeled Tmax/sunset.

## Current interpretation

The two-sided hot-shoulder concept is currently the strongest locally derived structural modification. It improves high-DTR independent validation more than fixed A/B/C, dynamic A, or one-sided post-peak correction. However, alpha_pre=13.333 is very large and R2 does not improve, which means the current noon-to-peak basis is still too rigid / poorly scaled. This version is a mechanism test, not yet the final source-code formula.

The next model should preserve the key insight while improving mathematical structure:
- retain DTR trigger near 14.5 C;
- retain Tmax as an anchor;
- avoid a huge alpha_pre caused by a very short pre-peak basis interval;
- fit a smoother width/shape parameter controlling the hot-shoulder duration rather than directly subtracting temperature with an oversized coefficient;
- compare against original DSSAT using 2000-2016 calibration and 2017-2024 independent validation;
- report DTR bins and key solar-time errors.

## Immediate next step

Build and test a **shape/width-based hot-shoulder model** in which DTR excess changes the curvature or normalized width around Tmax rather than adding a large empirical temperature subtraction. Preserve original DSSAT for DTR<=14.5 C. Do not modify Fortran source until the statistical prototype passes independent validation and avoids systematic over-correction.
