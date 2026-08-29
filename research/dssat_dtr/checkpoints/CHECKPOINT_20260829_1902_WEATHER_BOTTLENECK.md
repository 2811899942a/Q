# CHECKPOINT 2026-08-29 19:02 CST - Shihezi baseline reproduction bottleneck

## Objective
Reproduce the published Guo (2025) Xinyu66 CERES-Maize baseline before interpreting M0/H0TT/M15TT as predictive-accuracy evidence.

## New source recovery completed
1. Full 66-page Guo 2025 thesis attachment was recovered from the Shihezi University public record. Chapter 2 methods and calibration text are extracted under `research/dssat_dtr/data/shihezi_real_case/guo2025_chapter2_exact_inputs/`.
2. Guo Table 2-4 initial genetic coefficients (300.0, 0.600, 850.0, 850, 8.80, 45.00) uniquely match the frozen DSSAT v4.8.5 cultivar row `IF0011 EV-8443_TG`, ecotype `IB0001`. Therefore IB0001 is source-supported, not an arbitrary proxy.
3. Full Meng Yu 2021 thesis was recovered. It documents the same 2019-2020 Shihezi station, Xinyu66 cultivar, W1-W4 irrigation totals and exact 10 irrigation dates. The original trial method reports 20 cm plant spacing and 82,500 plants/ha, whereas Guo 2025 later reports 25 cm plant spacing. This is a source conflict.
4. The Meng thesis reports PE ordinary mulch as the control treatment and W3PE as the maximum-yield treatment in both years, consistent with Guo's observed W1-W4 yield ranking. Exact graph yield values are image-embedded and not yet numerically recovered.

## Density sensitivity already computed
V4 (Guo text-derived 8.89 plants/m2):
- M0 2020 RRMSE = 60.771%
- H0TT = 54.414%
- M15TT = 56.973%

V5 (same-trial Meng 8.25 plants/m2):
- M0 2020 RRMSE = 58.945%
- H0TT = 52.483%
- M15TT = 55.230%

Published Guo original 2020 yield RRMSE is about 5.69%.
Conclusion: density correction changes the reconstructed baseline by only ~1.83 percentage points and cannot explain the baseline failure. Do not spend more effort tuning density.

## Current scientific interpretation
- Cultivar coefficients: recovered and frozen.
- Ecotype IB0001: recovered and frozen.
- Soil hydraulic profile: recovered from Guo Table 2-1.
- Planting dates, irrigation totals, and irrigation dates: recovered.
- Summary.OUT HWAM parser: audited correct.
- NOAA same-station 2019/2020 hourly route: closed; Shihezi GHCNh IDs exist but station-year files are unavailable.
- Remaining dominant uncertainty: exact 2019/2020 daily weather used by Guo (national meteorological source for temperature/precipitation plus NASA radiation). Current NASA POWER-only reconstruction is not adequate.
- Secondary uncertainty: initial soil water. Fertilizer is not reported in Guo Chapter 2, and NITRO remains disabled rather than invented.

## Next action
Digitize the published 2019/2020 temperature and precipitation figures from the full Guo and Meng theses. Use the recovered station/field temperature and precipitation series, with NASA retained only for SRAD if necessary, then rebuild WTH and rerun the M0 reproduction gate before evaluating H0TT/M15TT.

## Hard rule
Do not retune M15 (DTRc=14.8 C, alpha=7.8094) or Xinyu66 genetic coefficients to force a crop-output advantage. All common-arm reconstruction changes must be externally source-supported.
