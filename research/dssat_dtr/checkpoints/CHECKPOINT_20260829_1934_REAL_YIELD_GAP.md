# DSSAT Xinjiang checkpoint - 2026-08-29 19:34 +08

## Current task
Continue real-case validation of the frozen extreme-day hourly thermal-time method using Guo Lipeng (2025) Shihezi Xinyu66 CERES-Maize case. Do not retune M15 (`DTRc=14.8 C`, `alpha=7.8094`) or published cultivar coefficients to force crop-output improvement.

## Frozen method arms
- M0: official DSSAT v4.8.5 CERES-Maize extreme-day synthetic sine DTT.
- H0TT: official HMET/TGRO inserted into the existing extreme-day 24 h DTT branch.
- M15TT: frozen Xinjiang M15 hourly TGRO refinement followed by the same TGRO extreme-day DTT integration.

## Valid V4 real-yield result
Workflow: `.github/workflows/shihezi-real-yield-v4.yml`
Run: `33246786517` (success)
Result: `research/dssat_dtr/data/shihezi_real_case/real_yield_v4/README_REAL_YIELD_V4.md`

2020 independent validation:
- M0 RRMSE = 60.771% (published original baseline = 5.69%) -> reproduction gate FAIL.
- H0TT RRMSE = 54.414% -> +10.461% relative improvement vs reconstructed M0.
- M15TT RRMSE = 56.973% -> +6.250% relative improvement vs reconstructed M0.
- Local M15 contribution vs H0TT = -4.703% in this provisional reconstruction.
- Maximum arm-induced HWAM shift = 934 kg/ha, well above ~100 kg/ha yield-digitization resolution.
- Robust suffix parsing confirms HWAM values are real DSSAT output, not parser misalignment.

Interpretation: crop propagation is real and large in this real cultivar case, but final accuracy claims are invalid until the reconstructed M0 approximates the published baseline.

## Main reconstruction mismatch identified
Published thesis source extraction (`CASE_MANIFEST.md`, Chapter 2):
- site 85 59 47 E, 44 19 28 N, 412 m;
- Xinyu66 published GLUE coefficients P1=104.7, P2=1.824, P5=957.2, G2=671, G3=15.82, PHINT=42.97;
- 2019/2020 sowing 05-03 / 05-05;
- four irrigation totals W1-W4 = 487.5/525/562.5/600 mm in 10 events;
- exact soil LL/DUL/SAT/bulk density layers are available;
- published growing-season precipitation totals = 96.45 / 119.88 mm;
- thesis reports growing-season mean total radiation about 19.8 MJ m-2 d-1.

Current V4 Summary.OUT under provisional NASA POWER reconstruction:
- 2019 SRADA=23.3, PRCP=83.3 mm;
- 2020 SRADA=24.2, PRCP=103.1 mm.
Thus provisional weather is systematically higher-radiation and lower-rain than the thesis-described case. This is a plausible contributor to positive yield bias.

Other unresolved source gaps remain:
- exact 2019/2020 CMA+NASA WTH used by the thesis;
- fertilizer dates/forms/NPK amounts;
- initial soil water and mineral N;
- exact ecotype/support genotype parameters beyond the published six cultivar coefficients;
- exact numerical observations are figure-derived rather than tabulated.

## New source-gap attribution experiment
Workflow: `.github/workflows/shihezi-m0-weather-gap-diagnostic.yml`
Commit: `880909ac6a4f0afa80086d2a64da887c26fdf7df`
Run: `33250348543` (in progress at checkpoint time)

Scenarios, M0 only, no cultivar/M15 tuning:
1. BASE = V4 provisional reconstruction.
2. RAIN_MATCH = year-specific rain magnitude aligned toward thesis reported precipitation.
3. SRAD_19P8 = year-specific radiation scaling toward thesis-reported ~19.8 MJ m-2 d-1.
4. WEATHER_BOTH = both source-supported magnitude checks.
5. N_LOW_BOUND = enable nitrogen stress with existing tiny initial mineral N and no unknown fertilizer. This is explicitly a lower-bound diagnostic, not a candidate reconstruction.

Decision purpose:
- determine whether weather mismatch alone can explain the failed M0 reproduction gate;
- if not, quantify whether missing N management has enough leverage to explain the remaining gap;
- do not accept any scenario as formal validation unless its inputs are source-supported.

## Additional weather recovery already available
`research/dssat_dtr/data/shihezi_real_case/guo_weather_daily_v1/`
- Direct red-curve extraction from thesis Fig.2-2 gives 122 daily Tmax values/year for May-Aug.
- Black Tmin curve detection: 68 days (2019), 86 days (2020); black-only daily-mean agreement against independent same-trial Meng series MAE ~1.56 / 1.61 C and r=0.947 / 0.927.
- Rain-bar extraction is incomplete (27.4 / 74.04 mm May-Aug), so it is not yet a replacement for exact WTH.
This figure-derived temperature series is a candidate diagnostic replacement for NASA daily Tmax/Tmin after the current weather-gap attribution run is interpreted.

## Next step
1. Wait for run 33250348543.
2. Read `m0_source_gap_diagnostic/README.md` and metrics.
3. If weather magnitude materially reduces M0 bias but does not pass the gate, run a second diagnostic using thesis-figure daily Tmax/Tmin + NASA SRAD + source-supported precipitation magnitude.
4. If the remaining gap is dominated by unknown N/management/ecotype, stop pretending the reconstructed case is publication-grade and explicitly require exact original DSSAT inputs or select another public real case.
