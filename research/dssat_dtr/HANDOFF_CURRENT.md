# DSSAT-DTR Urumqi Research Handoff

Last checkpoint: 2026-08-29 12:31 CST
Branch: `research/dssat-dtr-matrix`
Study station: NOAA `51463099999` / GHCN `CHM00051463`, Urumqi

## What is being done

Develop a Urumqi-specific DSSAT `HTEMP` improvement from local observations rather than copying an existing improved temperature model. Formula search is now **stopped** because a statistically robust candidate has been obtained. The next stage is source-level / crop-response propagation, which requires the actual DSSAT weather/project inputs so that the radiation term is taken from the same `SRAD` used by DSSAT rather than the NASA POWER screening series.

## Confirmed baseline

- NOAA ISD `51463099999`, 2000-2024: **72,177** real sub-daily temperature observations.
- GHCN-Daily `CHM00051463` supplies formal Tmax/Tmin/DTR.
- Original DSSAT `DAYLEN + HTEMP` reproduced using official `A=2.0, B=2.2, C=1.0`.
- **55,756** observation-model pairs over **7,036** days.
- 2017-2024 May-Sep official DSSAT RMSE ≈ **2.9469 C**.
- 2017-2024 May-Sep high-DTR (`DTR>=15 C`) official RMSE = **5.1215 C**.

## Local mechanism found

1. DTR-related failure is threshold-like rather than simply linear.
2. Formal model trigger is based only on 2000-2016 calibration data:
   - `DTRc = 14.8 C`.
3. Below this level, official HTEMP is retained.
4. Above it, the dominant failure is excessive hot-shoulder / afternoon thermal persistence.
5. DTR alone is insufficient: solar-radiation state strongly controls how severe the high-DTR failure becomes.

Main-station high-DTR validation SRAD stratification showed:
- low-radiation days: afternoon Bias ≈ **+10.14 C**;
- middle-radiation days: ≈ **+4.69 C**;
- high-radiation days: ≈ **+0.84 C**.

Thus the most defensible local interpretation is:

> DTR identifies the regime in which Parton-Logan becomes vulnerable, while radiative forcing determines the magnitude of the hot-shoulder / afternoon persistence error.

## Radiation variable without new DSSAT inputs

An internally computable clearness index was tested:

`Kt = SRAD / Ra`

where `Ra` is FAO-style extraterrestrial radiation from latitude + DOY. This needs only variables already available to DSSAT (`SRAD`, latitude, date).

For independent high-DTR error prediction:
- DTR-only RMSE = 2.6093;
- `DTR + Kt + interaction` RMSE = **1.8252**;
- gain = **30.05%**;
- only 2.30% worse than using an external NASA clear-sky radiation ratio.

A separate hard Kt breakpoint was investigated and rejected as a physical threshold because calibration and validation breakpoints were not stable (calibration ~0.70-0.73, validation ~0.52-0.53). Radiation therefore remains a continuous modulator, not a second claimed climate threshold.

## Model screening history

- Fixed PL-XJ A/B/C regionalization: ~5% high-DTR improvement; insufficient.
- One-sided post-peak correction: ~5.05%.
- Dynamic A: ~3.84%.
- Exploratory two-sided DTR-only shoulder: **9.07%**; useful benchmark but poorly scaled pre-peak coefficient.
- Asymmetric-power curvature: 2.76%; rejected.
- Signed-skew: 7.29%; rejected as final.
- Three-lobe: 6.14%; rejected.
- Whole-day shoulder contraction + skew: worsened; rejected.
- M9 DTR + Kt linear modulation: **12.84%**, but overcorrected high-Kt days.
- M11 nonlinear `(1-Kt)^p` gate: 12.16%; inferior to M10.

## Current accepted statistical prototype: M10

Name: **cross-validated radiative-deficit-gated HTEMP**.

Formal trigger:

`DTR > 14.8 C`

Radiation gate:

`Rdef = max(0, Kt0 - Kt) / 0.1`

with `Kt0` selected only within 2000-2016 by leave-one-year-out cross-validation. Current selected value:

`Kt0 = 0.900`

Important: `Kt0` is treated as a **cross-validated taper scale**, not a universal physical threshold. It reached the current search upper edge, so its exact numerical value should not be overinterpreted until the same test is repeated with the actual DSSAT WTH SRAD series.

Daytime shoulder correction:

- pre-peak basis: `Bpre = 4*v*(1-v)` from solar noon to modeled Tmax;
- post-peak basis: `Bpost = 4*u*(1-u)` from modeled Tmax to sunset;
- both bases are zero at their endpoints.

Current frozen parameters:
- `beta_pre = 2.3436078691`
- `beta_post = 0.4969689850`

The correction is proportional to:

`(DTR-DTRc) * Rdef * B`

and `DTR<=14.8 C` remains effectively official DSSAT.

## M10 independent validation result

2017-2024 May-Sep:
- official RMSE: **2.9469 C**
- M10 RMSE: **2.7526 C**
- improvement: **6.59%**
- R2: `0.8029 -> 0.8218`

2017-2024 high-DTR (`DTR>=15 C`):
- official RMSE: **5.1215 C**
- M10 RMSE: **4.4196 C**
- improvement: **13.71%**
- Bias: `+1.2167 -> +0.4936 C`
- R2: `0.5559 -> 0.6107`

DTR-stratified validation:
- 15-<18 C: `4.8348 -> 4.2487 C` (~12.1% improvement)
- 18-<20 C: `6.2900 -> 4.9652 C` (~21.1%)
- >=20 C: `7.6018 -> 6.2179 C` (~18.2%; very small sample, treat as extreme-case support only)

Key solar-hour validation:
- 14 h: `4.0302 -> 3.4072 C`
- 17 h: `3.9514 -> 3.3391 C`

Kt strata:
- LowKt: `7.1254 -> 5.8613 C` (strong improvement)
- MidKt: `4.4053 -> 3.9491 C` (improvement)
- HighKt: `2.7271 -> 2.7753 C` (small ~1.8% degradation; far smaller than M9 but still a caveat)

## Final frozen-parameter robustness test

No M10 parameter was refitted.

High-DTR validation years with observations:
- 2020: 11.73% RMSE improvement
- 2021: 16.70%
- 2022: 12.57%
- 2023: 13.83%
- 2024: 12.63%

M10 improves **5/5** validation years containing high-DTR observations.

Paired day-block bootstrap on 123 high-DTR validation days / 975 points:
- observed improvement: **13.71%**
- bootstrap median: **13.65%**
- 95% CI: **10.76%-16.54%**
- absolute RMSE reduction 95% CI: **0.521-0.890 C**
- probability that RMSE improvement >0: **100%**

This satisfies the predefined stopping criterion for formula search. Further temperature-formula tuning should stop to avoid overfitting.

## Next step / data now required

Before modifying DSSAT Fortran and assessing phenology/yield effects, obtain the **actual DSSAT maize project/weather inputs for the Urumqi experiment** (preferred Anningqu 2021-2022 if that is the chosen validation experiment), especially:

1. the exact `.WTH` file(s) used by DSSAT, including daily `SRAD`, `TMAX`, `TMIN`;
2. experiment file(s) / management data (sowing date, cultivar, irrigation, fertilization);
3. cultivar/ecotype coefficients currently used or calibrated;
4. soil profile used by DSSAT;
5. observed phenology/yield table used for calibration/validation.

Reason: the M10 mechanism has been established with station temperature observations and NASA POWER SRAD used as a radiation screening/prototype series. The next scientifically valid test must compute `Kt` from the **same SRAD that DSSAT itself reads from WTH**. Once those inputs are supplied, implement M10 inside the DSSAT temperature pathway, compare official vs modified HTEMP, and quantify propagation into thermal time, phenology and yield.
