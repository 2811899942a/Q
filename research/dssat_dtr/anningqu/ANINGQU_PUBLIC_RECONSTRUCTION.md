# Anningqu 2021–2022 Public DSSAT Reconstruction Inventory

Status: public-data-first reconstruction; no user local DSSAT project required.

## Primary agronomic experiment

Tang, H.; Xie, X.; Zhang, L.; Liu, C. (2024). Assessing the Influence of Planting Dates on Sustainable Maize Production under Drought Stress Conditions. Sustainability 16(11):4571. DOI: 10.3390/su16114571.

Site:
- Anningqu, Urumqi, Xinjiang.
- 87.49 E, 43.95 N, about 590 m elevation.
- 2021 and 2022.
- Randomized complete block / split-plot style field experiment, three replicates.
- Six maize hybrids named in the paper: KWS3376, Xinyu 65, KWS9384, Huamei No. 1, Xinyu 102, Heyu 187.
- Six rows per material, row length 3 m, row spacing 0.6 m, plant spacing 0.25 m.

### Sowing dates

| Code | Date |
|---|---|
| A | 21 April |
| B | 26 April |
| C | 6 May |
| D | 16 May |
| E | 26 May |

Paper Table 2 expected flowering/harvest calendar:
- A: flowering Jun 27, harvest Sep 4.
- B: flowering Jul 1, harvest Sep 7.
- C: flowering Jul 7, harvest Sep 15.
- D: flowering Jul 14, harvest Sep 27.
- E: flowering Jul 21, harvest Oct 13.

### Irrigation treatments

Paper Table 1 gives eight watering stages: emergence, jointing, small trumpet, big trumpet, flowering, early filling, filling, filling end.

Each treatment uses 675 m3/ha at emergence. Each of the remaining seven events uses a constant treatment-dependent amount:

| Water treatment | Nominal level | Event amount after emergence | Paper total |
|---|---:|---:|---:|
| Water 1 | 100% | 675 m3/ha | 5400 m3/ha |
| Water 2 | 80% | 540 m3/ha | 4455 m3/ha |
| Water 3 | 60% | 405 m3/ha | 3510 m3/ha |
| Water 4 | 40% | 270 m3/ha | 2565 m3/ha |
| Water 5 | 20% | 135 m3/ha | 1620 m3/ha |
| Water 6 | 0% | 0 m3/ha | 675 m3/ha |

The paper says actual irrigation was adjusted downward for rainfall. Therefore these are planned/nominal treatment amounts; daily event dates and rainfall-adjusted actual amounts still need reconstruction.

### Observations available in the paper

- sowing, emergence, jointing, trumpet, anthesis/powdering, silking, filling, maturity stages recorded;
- DTT, DTA, DTS and ASI shown by treatment/variety/year in figures;
- plant height, ear height, tassel traits, leaf traits;
- yield components;
- grain yield at 14% standard moisture;
- soil moisture measured at 10, 20, 30, 40, 60 and 100 cm before sowing / after harvest or dynamically by treatment.

The article states that Xinyu 65 produced the highest yield and is the preferred initial cultivar for DSSAT reconstruction.

## Weather reconstruction

Formal DSSAT weather should be built independently of the statistical HTEMP discovery dataset:
- TMAX/TMIN: NOAA/GHCN or station-quality daily observations for Urumqi/Diwopu/Anningqu proximity.
- RAIN: quality-controlled daily public observations; do not reuse known-problematic client GSOD precipitation.
- SRAD: public daily solar radiation (NASA POWER initially, and/or a defensible station/reanalysis source); DSSAT M15 itself uses the native CLOUDS computed from the WTH SRAD.

M0 and M15 must use the exact same WTH.

## Soil reconstruction candidates

The Tang 2024 experiment states only medium soil fertility and does not provide a full DSSAT hydraulic profile in the article body. Public same-area sources can constrain the soil:

1. Anningqu long-term gray desert soil fertility station, Urumqi:
   - gray desert soil / oasis irrigated agriculture;
   - pH around 7.95-8.03;
   - bulk density reported around 1.25 g/cm3 in a long-term soil-fertility publication;
   - layer-specific nutrient properties reported for 0-20 and 20-40 cm.

2. A 2022 Anningqu maize field study near 43°56'28N, 87°28'35E reports topsoil approximately:
   - pH 8.10;
   - organic matter 16.90 g/kg;
   - nitrate N 34.84 mg/kg;
   - Olsen P 14.03 mg/kg;
   - available K 401.05 mg/kg.

These sources can inform fertility and bulk density but do not by themselves provide all DSSAT hydraulic properties (lower limit, drained upper limit, saturation, saturated hydraulic conductivity). Those should be sourced from a public soil profile / SoilGrids + pedotransfer only if a same-site measured profile cannot be found.

## Cultivar strategy

No published CERES-Maize genetic coefficients for Xinyu 65 have yet been located.

Preferred hierarchy:
1. search for a published DSSAT/CERES-Maize parameterization of Xinyu 65 or a closely documented Xinjiang hybrid;
2. if absent, estimate P1/P2/P5/G2/G3/PHINT from public Anningqu phenology/yield observations, using one year/treatment subset for calibration and the other for validation;
3. never tune cultivar coefficients separately for M0 and M15. Calibrate once under a predeclared baseline and freeze them for the M0-vs-M15 source comparison.

## Scientific comparison rule

The crop-stage test is not intended to prove that every treatment yield improves. It tests whether a demonstrably better high-DTR subdaily temperature pathway propagates coherently into:
- thermal exposure / thermal time;
- tasseling / anthesis / silking / maturity;
- biomass/LAI where observations are defensible;
- final grain yield.

M0 and M15 must use identical crop, soil, irrigation, fertilizer and weather inputs. The only changed model component is the source-level subdaily temperature pathway.

## Current gaps to resolve from public sources before asking the user

1. exact numeric DTT/DTA/DTS and yield values from article figures for a manageable subset, preferably Xinyu 65;
2. actual or reconstructable irrigation event dates by phenological stage;
3. fertilizer management used in the 2021–2022 Tang experiment;
4. full DSSAT soil hydraulic profile at/near the Anningqu experimental station;
5. Xinyu 65 CERES-Maize coefficients or sufficient public observations to estimate them.

Do not ask the user for local data until these public-source paths have been exhausted.
