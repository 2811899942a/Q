# CHECKPOINT 2026-08-29 20:12 CST — Shihezi 51356 public-station weather probe

## Purpose

Recover a public daily weather series for the 2019–2020 Shihezi Xinyu66 real-case reconstruction, so common-arm M0 weather forcing can be improved without fitting crop yield.

## Probe executed

GitHub Actions run: `33251318548` (`Shihezi 51356 Weather Probe`), completed successfully as an engineering probe.

The workflow queried:

- NOAA ISD station history for station metadata;
- GSOD daily files using `51356099999` for 2019 and 2020;
- GHCN-Daily using `CHM00051356.dly`;
- existing NASA POWER reconstruction for comparison.

## Results

### Station metadata

The ISD history file returned one metadata match for station identifier 51356/513560.

### Daily observations

Direct daily-file retrieval did not recover the needed 2019–2020 records:

- GSOD `51356099999` 2019: HTTP 404
- GSOD `51356099999` 2020: HTTP 404
- GHCN-Daily `CHM00051356.dly`: HTTP 404

Therefore no NOAA/GHCN daily TMAX/TMIN/PRCP series was recovered through those identifiers in this probe.

This is a data-availability result; it does not establish that the station lacks observations in all archives or under all historical identifiers.

### Existing NASA POWER May–August forcing audit

2019 May–August:
- n = 124 days
- mean TMAX = 31.4848 C
- mean TMIN = 18.0463 C
- total precipitation = 93.41 mm
- mean SRAD = 22.9494 MJ m-2 d-1

2020 May–August:
- n = 123 days
- mean TMAX = 31.6507 C
- mean TMIN = 18.2880 C
- total precipitation = 118.84 mm
- mean SRAD = 23.6218 MJ m-2 d-1

## Interpretation

The May–August POWER precipitation magnitude is already close to the thesis-scale precipitation totals, especially in 2020. The clearer magnitude discrepancy is solar radiation: POWER is around 23 MJ m-2 d-1 while the thesis description indicates roughly 19.8 MJ m-2 d-1.

This comparison does not replace the active-WTH propagation test because the DSSAT `Summary.OUT` crop-period `PRCP` covers the actual simulated crop period and is not numerically identical to the May–August total.

## Next action

1. Keep the exact station-observation series unresolved; do not invent or interpolate an observational station dataset.
2. Complete audited weather-gap diagnostic V2, which must prove that edited SRAD/RAIN values reach the actual DSSAT run path.
3. If V2 shows solar radiation materially influences the M0 yield gap, prioritize recovery of the exact NASA/observed radiation construction used by Guo.
4. Continue same-trial fertilizer and initial-water recovery in parallel.

## Frozen rules

- No M15 retuning.
- No Xinyu66 retuning.
- No weather value may be selected by minimizing the 2020 yield error.
- Public-station failure is recorded as a source-recovery outcome, not treated as justification for arbitrary weather replacement.
