# DSSAT-DTR Urumqi Research Handoff

Last checkpoint: 2026-08-29 12:22 CST
Branch: `research/dssat-dtr-matrix`
Study station: NOAA `51463099999` / GHCN `CHM00051463`, Urumqi

## Current task

Develop a Urumqi-specific DSSAT `HTEMP` improvement from local residual structure. The work has moved beyond pure DTR-only curve geometry: the main-station residuals now show that **solar radiation strongly modulates the high-DTR failure regime**. The current priority is to replace the external NASA clear-sky ratio with a DSSAT-internal astronomical clearness index computed from existing `SRAD + latitude + DOY`, then build a DTR-triggered radiation-modulated correction.

## Confirmed baseline

- NOAA ISD 51463099999, 2000-2024: 72,177 real sub-daily temperature observations.
- GHCN-Daily CHM00051463 supplies formal Tmax/Tmin/DTR.
- Original DSSAT `DAYLEN + HTEMP` reproduced with official `A=2.0, B=2.2, C=1.0`.
- 55,756 observation-model pairs over 7,036 days.
- Original HTEMP high-DTR (`DTR>=15 C`) error is large; 2017-2024 May-Sep RMSE = **5.1215 C**.

## Formal local DTR threshold

Exploratory full-period breakpoints clustered near 14.5 C, but formal model development now avoids validation leakage.

Calibration-only (2000-2016) breakpoint used for model triggering:
- AM-PM asymmetry breakpoint ≈ **14.8 C**.

Therefore the formal rule is currently:
- `DTR <= 14.8 C`: retain official DSSAT HTEMP exactly.
- `DTR > 14.8 C`: allow local structural correction.

## Confirmed local residual mechanism

- Morning cold bias increases gradually with DTR but has no strong structural breakpoint.
- Afternoon warm bias and daily RMSE show a strong breakpoint near 14-15 C.
- Main error is concentrated in the high-temperature shoulder / afternoon persistence rather than simply Tmax timing.

## Tested DTR-only structural models

### Fixed PL-XJ A/B/C
- High-DTR validation improvement only ~5%.
- Conclusion: fixed parameter regionalization insufficient.

### One-sided post-peak correction
- High-DTR RMSE: `5.1215 -> 4.8629 C` (~5.05%).

### Dynamic A
- High-DTR RMSE: `5.1215 -> 4.9249 C` (~3.84%).
- Combining dynamic A + post-peak caused negative bias and was not retained.

### Exploratory two-sided additive shoulder
- Best DTR-only screening result so far.
- High-DTR RMSE: `5.1215 -> 4.6567 C` = **9.07% improvement**.
- Bias: `+1.2167 -> -0.0954 C`.
- Limitation: `alpha_pre=13.333` is too large / poorly scaled; not acceptable as final formula.

### Asymmetric power curvature (formal threshold 14.8 C)
- `k_rise=0`, `k_fall` hit search upper bound.
- High-DTR improvement only **2.76%**.
- Rejected.

### Signed-skew basis
- `beta_rise=1.5515`, `beta_fall=3.0784 C/C-excess`.
- High-DTR RMSE `5.1215 -> 4.7480 C` = **7.29%**.
- Better mathematical scaling, but does not beat 9.07% benchmark.

### Three-lobe morning/prepeak/postpeak model
- Morning coefficient fitted to exactly 0.
- High-DTR RMSE `5.1215 -> 4.8070 C` = **6.14%**; R2 worsened.
- Rejected.

### Whole-day shoulder contraction + skew
- High-DTR RMSE worsened to **5.2338 C** (-2.19%).
- Rejected.

## New major finding: DTR x solar radiation

A separate dense Diwopu sequence first suggested that radiation modulates high-DTR HTEMP failure. This was then independently repeated on the **main station 51463099999** using its existing HTEMP residuals plus NASA POWER daily radiation at 87.6167E, 43.7833N.

Main-station matched May-Sep days: **2,867**.
Calibration: 2000-2016.
Validation: 2017-2024.
Formal DTR trigger: 14.8 C (calibration only).

Independent high-DTR daily-RMSE prediction:

| Error model | High-DTR prediction RMSE | High-DTR R2 |
|---|---:|---:|
| DTR only | 2.6093 | -0.1292 |
| DTR + SRAD | 2.0742 | 0.2864 |
| DTR + CLEAR | 1.9331 | 0.3802 |
| DTR + SRAD + interaction | 1.9042 | 0.3986 |
| **DTR + CLEAR + interaction** | **1.7842** | **0.4720** |
| FULL | 1.8558 | 0.4287 |

Best model improves high-DTR error prediction by **31.62%** relative to DTR-only.
Afternoon-bias prediction improves by **33.51%**.

High-DTR validation stratification by calibration-period SRAD tertiles:

| SRAD regime | N | Mean DTR | Mean SRAD | Daily RMSE | Afternoon RMSE | Afternoon Bias |
|---|---:|---:|---:|---:|---:|---:|
| Low SRAD | 32 | 16.73 | 12.02 | 7.058 | 10.248 | +10.136 |
| Mid SRAD | 58 | 16.78 | 21.72 | 4.280 | 4.871 | +4.690 |
| High SRAD | 33 | 16.24 | 29.30 | 2.428 | 1.324 | +0.837 |

This is currently the strongest mechanism discovery in the project.

## Current interpretation

DTR identifies when the official Parton-Logan reconstruction enters a failure regime, but **DTR does not uniquely determine the shape error**. Under similarly high DTR, low-radiation days exhibit far stronger afternoon warm bias than high-radiation days. This suggests that the original HTEMP assumption of a fixed smooth daytime thermal trajectory is especially poor when daily thermal amplitude is large but the daily radiative forcing is weak / cloud-modulated.

This is attractive for DSSAT because weather files already contain `SRAD`; the final model may require no new external weather input.

## Immediate next step

1. Compute FAO-style extraterrestrial radiation `Ra` from latitude + DOY.
2. Define an internal clearness index `Kt = SRAD / Ra` using only DSSAT-available variables.
3. Test whether `DTR + Kt + DTR*Kt` reproduces the NASA CLEAR result on 2017-2024 independent validation.
4. If yes, build a low-parameter DTR-triggered, Kt-modulated HTEMP correction and compare directly against:
   - official DSSAT;
   - 9.07% exploratory DTR-only shoulder benchmark.
5. Do not modify Fortran until this statistical prototype passes independent validation with clear advantage, stable bias, and no degradation for DTR<=14.8 C.
