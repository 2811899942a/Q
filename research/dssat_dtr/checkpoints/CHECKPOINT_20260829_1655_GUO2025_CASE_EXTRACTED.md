# CHECKPOINT 2026-08-29 - Guo 2025 Shihezi real case extracted

## What was completed
The user supplied the full 2025 Shihezi University MSc thesis by Guo Lipeng. Chapter 2 was inspected and the formal Xinjiang CERES-Maize validation case was reconstructed at the metadata/parameter level.

## Major breakthrough
The previous blocker 'local calibrated maize cultivar coefficients missing' is resolved.

Cultivar: Xinyu 66 (新玉66)
Published calibrated CERES-Maize coefficients from Table 2-4:
- P1 = 104.7
- P2 = 1.824
- P5 = 957.2
- G2 = 671
- G3 = 15.82
- PHINT = 42.97

Calibration used 2019 observations and DSSAT GLUE with 20,000 runs. 2020 did not participate in calibration and is an independent validation year.

## Real experiment reconstructed
Site: Shihezi University Modern Water-saving Irrigation Key Experimental Station
Coordinates: 85°59'47"E, 44°19'28"N
Elevation: 412 m
Years: 2019-2020
Sowing: 2019-05-03; 2020-05-05
Four irrigation treatments: 487.5 / 525 / 562.5 / 600 mm total, 10 events.
Published 0-100 cm soil physical/water profile has been transcribed.
Observed targets: phenology, LAI, dry matter, maximum dry matter, grain mass, final yield.

## Files written
- `research/dssat_dtr/data/shihezi_real_case/CASE_MANIFEST.md`
- `research/dssat_dtr/data/shihezi_real_case/guo2025_genotype.csv`
- `research/dssat_dtr/data/shihezi_real_case/guo2025_soil_profile.csv`
- `research/dssat_dtr/data/shihezi_real_case/guo2025_irrigation_schedule.csv`

## Important source warning
Fig. 3-1 in the thesis contains an illustrative Python/DSSAT input example with IB0001 and different genotype values. It is not the formal Xinyu66 calibration and must not be used. Table 2-4 is the authoritative cultivar source.

## Remaining scientifically meaningful gaps
1. Exact 2019/2020 daily weather values used by the original study, plus real hourly temperature for the subdaily method.
2. Fertilizer schedule and nutrient application information.
3. Initial soil water/mineral N conditions.
4. Raw treatment-level numerical observations; thesis figures show them but tables are not printed.
5. Exact observed phenology dates.
6. Explicit plant population density.
7. Some DSSAT soil support fields (pH, CEC, root factor).

## Next action
Do not tune the temperature method. Search/recover the exact weather and underlying raw observations / field-management data from the same Shihezi experiment family. In parallel, prepare a DSSAT input skeleton using only directly published values. Do not fabricate missing fields.

Once sufficient inputs are recovered:
1. reproduce M0 published baseline accuracy;
2. freeze all cultivar/soil/management inputs;
3. run M0 / H0TT / M15TT;
4. compare observation error metrics and causal contrasts GENERIC, LOCAL and TOTAL.
