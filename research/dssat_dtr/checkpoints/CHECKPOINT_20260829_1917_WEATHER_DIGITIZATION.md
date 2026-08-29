# CHECKPOINT 2026-08-29 19:17 CST - Shihezi weather digitization

## Objective
Recover source-supported 2019/2020 Shihezi daily weather from the Guo (2025) / Meng (2021) publications, rebuild the common DSSAT WTH, and rerun the M0 reproduction gate before interpreting H0TT or M15TT predictive accuracy.

## Preserved real-case baseline status
- Xinyu66 coefficients frozen: P1=104.7, P2=1.824, P5=957.2, G2=671, G3=15.82, PHINT=42.97.
- Ecotype IB0001 is source-supported: Guo initial six coefficients uniquely match DSSAT v4.8.5 cultivar row IF0011 EV-8443_TG / IB0001.
- Exact Shihezi soil profile, planting dates, W1-W4 irrigation amounts and dates recovered.
- Plant-density conflict: Guo text implies 8.89 plants/m2; Meng same-trial method explicitly reports 82,500 plants/ha (=8.25/m2). Density sensitivity already shows this is not the dominant baseline error.
- V4 (8.89): 2020 M0/H0TT/M15TT RRMSE = 60.771/54.414/56.973%.
- V5 (8.25): 2020 M0/H0TT/M15TT RRMSE = 58.945/52.483/55.230%.
- Published Guo original 2020 yield RRMSE about 5.69%; therefore all current modified-arm directions remain causal-screen evidence only.

## Weather source recovery
### Guo Fig.2-2
- Full public Guo thesis attachment recovered.
- Actual weather figure is PDF page 19.
- PDF embeds original JPEG xref 290 at 3460x1072 RGB, 315,023 bytes.
- Automatic panel split x≈1711.
- 2019 plot geometry approximately x=312–1535, y≈152–842.
- 2020 plot geometry approximately x=2053–3276, y≈136–839.
- Dominant saturated colors are cyan/blue (HSV H≈97–98) and red (H≈0/179), suitable for direct curve segmentation.

### Meng Fig.2-3
- Same-trial weather figure is PDF page 21 and is fully vector, with 209 drawing objects.
- 44 filled rectangles correspond to event-like bars; 3 long line paths correspond to one continuous daily temperature series per year (2019 split over two paths, 2020 one path).
- Plot y-axis text contains 0,5,10,...,40.
- 2019 major x ticks: 5/2,6/2,7/2,8/2,9/2.
- 2020 major x ticks: 5/4,6/4,7/4,8/4,9/4.
- Reconstructed temperature sequence has 129 dated values in 2019 and 126 in 2020. It is a single temperature curve per year, so it is a cross-check only and cannot replace Guo TMAX/TMIN.

## Meng rainfall reconstruction V2
Directory: `research/dssat_dtr/data/shihezi_real_case/meng_weather_series_v2/`
- 2019: 19 detected bars, naive 0–40 axis conversion gives 107.59 mm vs assumed/report comparator 96.45 mm (+11.14).
- 2020: 24 detected bars, naive conversion gives 41.82 mm vs comparator 119.88 mm (-78.06).
- Therefore the naive common 0–40 rainfall-axis assumption FAILS. These rain values must not be used in DSSAT yet.
- Likely issue is rainfall secondary-axis interpretation / object classification, not date mapping.

## Active workflow
`.github/workflows/guo-weather-axis-curve-recovery.yml`
Run: 33249729099
Commit: e77b90d63d10bb703287b69637a3fba2a1eaf9d8
Purpose:
1. one numeric-only OCR pass on axis digits only;
2. recover red/cyan curve pixels from the original embedded JPEG using HSV segmentation;
3. distinguish line-like temperature trajectories from bottom-connected filled rainfall objects;
4. output exact panel geometry and curve coverage.

## Next actions
1. Read active Guo axis/curve recovery result.
2. Identify which colored trajectories are TMAX and TMIN and establish y-axis scale from numeric ticks.
3. Recover dated TMAX/TMIN using plot x geometry, then cross-check their mean `(TMAX+TMIN)/2` against the independently reconstructed Meng single-temperature curve.
4. Revisit precipitation only after temperature recovery; do not force the Meng bar totals by arbitrary rescaling.
5. Build a source-recovered WTH using recovered TMAX/TMIN/RAIN and NASA only for SRAD if needed.
6. Rerun M0 reproduction gate first. No M15 or genotype retuning.

## Scientific hard rule
No strong real-yield accuracy claim is permitted until reconstructed M0 approaches the published baseline. M15 remains frozen at DTRc=14.8 C and alpha=7.8094.
