# Shihezi real Xinjiang CERES-Maize case - reconstruction manifest

Updated: 2026-08-29
Primary detailed source: Guo Lipeng (2025), Shihezi University MSc thesis, 基于作物生长模型的新疆干旱区滴灌玉米灌溉决策研究.

## Objective
Reconstruct a real calibrated Xinjiang drip-irrigated maize CERES-Maize case and use the same frozen cultivar / soil / management inputs to compare M0, H0TT and M15TT. No arm-specific recalibration is allowed.

## 1. Real experiment now directly confirmed

- Site: Shihezi University Modern Water-saving Irrigation Key Experimental Station, Xinjiang.
- Coordinates: 85°59'47"E, 44°19'28"N.
- Elevation: 412 m.
- Experiment: May-October, 2019 and 2020.
- Cultivar: Xinyu 66 (新玉66).
- Calibration year: 2019.
- Independent validation year: 2020; 2020 did not participate in cultivar calibration.
- Calibration method: DSSAT GLUE, 20,000 runs.
- Observations used: phenology, LAI, dry matter, maximum dry matter, grain mass and final yield.

## 2. Published calibrated CERES-Maize cultivar coefficients - authoritative values

Use Table 2-4 values, not the illustrative screenshot in Fig. 3-1.

| Parameter | Initial | Calibrated optimum |
|---|---:|---:|
| P1 | 300.0 | 104.7 |
| P2 | 0.600 | 1.824 |
| P5 | 850.0 | 957.2 |
| G2 | 850 | 671 |
| G3 | 8.80 | 15.82 |
| PHINT | 45.00 | 42.97 |

Published GLUE ranges:
- P1: 5-450
- P2: 0-2.0
- P5: 580-999
- G2: 248-990
- G3: 5-16.5
- PHINT: 30-75

Thesis note: P1 and P5 effective thermal time is counted when temperature >8°C.

### Critical warning
Fig. 3-1 is an input/output programming example. It shows an example cultivar/ecotype and values such as IB0001, P1≈243.1, P2≈1.974, P5≈742.2, G2≈635, G3≈10, PHINT≈70. These are NOT the calibrated Xinyu66 values and must never be used for the formal reconstruction.

## 3. Published soil profile

Table 2-1; 20-cm layers.

| Depth cm | Clay % | Silt % | Bulk density g/cm3 | DUL / field capacity cm3/cm3 | LL / wilting point cm3/cm3 | SAT cm3/cm3 | Organic matter g/kg |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0-20 | 32.75 | 51.93 | 1.51 | 0.237 | 0.122 | 0.457 | 1.485 |
| 20-40 | 31.52 | 54.11 | 1.54 | 0.264 | 0.136 | 0.425 | 1.410 |
| 40-60 | 43.28 | 44.53 | 1.59 | 0.231 | 0.120 | 0.371 | 1.264 |
| 60-80 | 30.21 | 60.74 | 1.63 | 0.214 | 0.113 | 0.346 | 1.307 |
| 80-100 | 29.13 | 49.76 | 1.61 | 0.236 | 0.105 | 0.385 | 1.022 |

Sand is not printed but may be arithmetically derived as 100-clay-silt if needed; mark it as derived rather than observed. Organic carbon is not printed and must not be silently inferred from organic matter without an explicit conversion assumption.

Still absent from the thesis table: pH, CEC, layer root-growth factor and initial NO3/NH4.

## 4. Published planting and drip-irrigation management

- Cultivar: Xinyu66.
- Sowing: 2019-05-03; 2020-05-05.
- Dry-seed sowing.
- Pattern: one film, two drip tubes, four rows.
- Plant spacing: 25 cm.
- Narrow row: 30 cm; wide row: 60 cm.
- Sowing depth: 4 cm.
- Film width: 1.45 m.
- Drip tape: single-wing labyrinth, OD 16 mm, wall thickness 0.3 mm.
- Emitter spacing: 30 cm.
- Lateral spacing: 90 cm.
- Four irrigation levels: W1=4875, W2=5250, W3=5625, W4=6000 m3/ha = 487.5, 525, 562.5, 600 mm total.
- Ten irrigation events.

### Event-level irrigation schedule

Amounts below are m3/ha. Divide by 10 for mm.

| Stage | 2019 | 2020 | W1 | W2 | W3 | W4 |
|---|---|---|---:|---:|---:|---:|
| Seedling | 05-03 | 05-05 | 487.5 | 525 | 562.5 | 600 |
| Jointing | 06-14 | 06-15 | 325 | 350 | 375 | 400 |
| Jointing | 06-22 | 06-23 | 325 | 350 | 375 | 400 |
| Jointing | 07-01 | 07-02 | 325 | 350 | 375 | 400 |
| Tasseling | 07-08 | 07-09 | 731.25 | 787.5 | 843.75 | 900 |
| Tasseling | 07-15 | 07-16 | 731.25 | 787.5 | 843.75 | 900 |
| Tasseling | 07-22 | 07-23 | 731.25 | 787.5 | 843.75 | 900 |
| Filling | 07-29 | 07-30 | 365.63 | 393.75 | 421.88 | 450 |
| Filling | 08-09 | 08-10 | 365.63 | 393.75 | 421.88 | 450 |
| Maturity stage | 08-23 | 08-24 | 487.5 | 525 | 562.5 | 600 |

## 5. Observation protocol directly confirmed

Phenology observed: emergence, jointing, tasseling, filling and maturity. Stage date criterion: 50% of plants in a plot reached the stage.

At the end of major stages, three representative plants per treatment were sampled for leaf area and dry matter. Dry matter was separated into stem/leaf/ear, killed at 105°C for 30 min, then dried at 75°C to constant weight. Leaf area used 0.75 × leaf length × maximum leaf width. LAI was calculated from leaf area and plant density / land area.

At maturity, ten consecutive ears per plot were sampled for grain mass and 1000-kernel weight; measured density, effective harvest area and grain moisture were used to calculate field economic yield.

Raw treatment-level numerical observations are mainly plotted in Figs. 2-4, 2-5 and 2-6 and are not tabulated in the thesis text.

## 6. Weather information directly confirmed

CERES input uses daily solar radiation, Tmax, Tmin and precipitation. The thesis states weather sources as the National Meteorological Science Data Center and NASA. A 1988-2018 daily database was used for hydrologic-year classification.

2019 and 2020 growing-season precipitation totals are reported as 96.45 and 119.88 mm, respectively; both were classified as normal-water years.

The thesis plots daily 2019/2020 Tmax, Tmin and precipitation in Fig. 2-2, but it does not print the underlying daily series. The exact 2019/2020 .WTH data therefore still require recovery from station/public data.

## 7. Published baseline accuracy to reproduce

- Yield: RRMSE <10% for all treatments.
- W2/W3/W4 yield ARE <5%.
- W1 yield ARE: 15.17% in 2019; 13.19% in 2020.
- Grain mass: ARE <5%; RRMSE around 2%; W3 ARE 4.88% in 2019 and 2.5% in 2020.
- Maximum dry matter: RRMSE close to 10%; W4 ARE 13.70% in 2019 and 15.95% in 2020.
- LAI RRMSE: 2019 12.68-25.19%; 2020 12.88-16.74%.
- Dry-matter time-series RRMSE: 2019 20.38-23.93%; 2020 22.69-24.30%.

M0 should approximately reproduce these magnitudes before H0TT/M15TT accuracy claims are interpreted.

## 8. Remaining scientifically meaningful gaps

1. Exact 2019/2020 daily weather series used in the validation run; for the new subdaily method, real hourly temperature for the same/nearby station is also required.
2. Fertilizer dates, forms, N/P/K amounts and application method/depth are not reported in Chapter 2.
3. Initial soil water and initial mineral N conditions are not reported.
4. Exact treatment-level observed numeric values for yield, grain mass, maximum dry matter, LAI time series and dry-matter time series are plotted but not tabulated.
5. Exact observed phenology dates are described as measured but not tabulated.
6. Explicit plant population density is not printed in the Chapter 2 management text; do not derive and silently use a density from row geometry without documenting the inference.
7. Some .SOL support fields such as pH/CEC/root-growth factor are absent.

## 9. Formal causal validation protocol

### Step 0 - M0 reproduction gate
Reconstruct the published 2019 calibration / 2020 independent validation case with Xinyu66 Table 2-4 coefficients. Keep published cultivar coefficients frozen. M0 should first reach approximately the published baseline accuracy.

### Step 1 - frozen-arm comparison
Identical cultivar, soil, management, initial conditions and daily weather for every arm:
- M0: official CERES extreme-day synthetic sine DTT.
- H0TT: official DSSAT HMET/TGRO -> CERES extreme-day 24 h DTT; no M15.
- M15TT: frozen Xinjiang M15 high-DTR hourly TGRO refinement -> same extreme-day DTT integration.

### Step 2 - metrics
Primary: yield RMSE/RRMSE/MAE/Bias/ARE; maximum dry matter; grain mass; LAI time-series RMSE/RRMSE; phenology MAE/Bias if exact observed dates can be recovered.

### Step 3 - causal contrasts
- GENERIC = H0TT - M0
- LOCAL = M15TT - H0TT
- TOTAL = M15TT - M0

No crop-output tuning of DTRc=14.8 or alpha=7.8094 is allowed.

## Current decision

Guo (2025) is now the primary detailed reconstruction source because it exposes the actual 2019-2020 experiment, Xinyu66 calibrated coefficients, soil layers and event-level irrigation schedule. Liang et al. (2022) remains a peer-reviewed corroborating case from the same Shihezi research system.

The former hard blocker 'missing local cultivar coefficients' is resolved. The next priority is exact 2019/2020 weather + raw observation recovery; then build the formal DSSAT input skeleton and pass the M0 baseline reproduction gate before evaluating H0TT and M15TT.