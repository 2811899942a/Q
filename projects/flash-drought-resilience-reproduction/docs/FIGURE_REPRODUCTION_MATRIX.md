# Figure Reproduction Matrix

Status values: `READY_FROM_PAPER`, `NEEDS_SOURCE_DATA`, `NEEDS_CAPSULE`, `NEEDS_SUPPLEMENT`, `PASS`, `BLOCKED`.

| Target | Scientific content | Minimum inputs | Methods | Initial status |
|---|---|---|---|---|
| Fig.1 | global count/severity/onset speed; MAP-MAE space; 1950-2023 trends/change points | historical event metrics + climate climatology | event engine, anomalies, BEAST, MK/Sen | NEEDS_CAPSULE |
| Fig.2 | hotspot/non-hotspot map and MFDI distributions/trends | MFDI + regional partition | eco-climate partition, MFDI, t-tests, Kendall tau | NEEDS_CAPSULE |
| Fig.3 | GPP resilience flash vs slow and hotspot vs non-hotspot | event table + FluxSat GPP | growing season, recovery selection, resilience | NEEDS_CAPSULE |
| Fig.4 | RF attribution at flash-drought hotspots | resilience + 15 predictors | VIF, RF, OOB permutation importance, PDP | NEEDS_CAPSULE |
| Fig.5 | RF attribution at non-hotspots | resilience + 15 predictors | VIF, RF, OOB permutation importance, PDP | NEEDS_CAPSULE |
| Fig.6 | conceptual synthesis | conclusions | schematic only | READY_FROM_PAPER |

## Supplementary targets referenced by the main text

| Target | Inferred/explicit role | Status |
|---|---|---|
| Fig.S1 | slow-drought temporal metrics | NEEDS_SUPPLEMENT |
| Fig.S2 | flash drought ratio / slow-to-flash transition | NEEDS_SUPPLEMENT |
| Fig.S3 | climate-factor anomalies flash vs slow + FLUXNET comparison | NEEDS_SUPPLEMENT |
| Fig.S4 | MFDI construction/hotspot detail | NEEDS_SUPPLEMENT |
| Fig.S5 | SIF resilience validation | NEEDS_SUPPLEMENT |
| Fig.S6 | FLUXNET site resilience validation | NEEDS_SUPPLEMENT |
| Fig.S7-S8 | SIF attribution confirmation | NEEDS_SUPPLEMENT |
| Fig.S9 | land-atmosphere coupling flash vs slow/trend/resilience | NEEDS_SUPPLEMENT |
| Fig.S10 | CMIP6 SSP245 future flash-drought changes | NEEDS_SUPPLEMENT |
| Fig.S11 | climate control of CO2 fertilization sensitivity difference | NEEDS_SUPPLEMENT |
| Fig.S12 | flash vs slow duration | NEEDS_SUPPLEMENT |
| Fig.S13 | hotspot/non-hotspot climate stress and resilience | NEEDS_SUPPLEMENT |
| Fig.S14 | SIF confirmation of intensifying impact | NEEDS_SUPPLEMENT |
| Fig.S15 | CMIP6 Taylor plot / model screening | NEEDS_SUPPLEMENT |
| Fig.S16 | flash/slow event identification illustration | NEEDS_SUPPLEMENT |
| Fig.S17 | energy limitation + aridity + vegetation partitions | NEEDS_SUPPLEMENT |
| Fig.S18 | vegetation recovery conceptual framework | NEEDS_SUPPLEMENT |
| Fig.S19 | growing-season identification + SIF verification | NEEDS_SUPPLEMENT |
| Fig.S20 | drought-response-period predictor definition | NEEDS_SUPPLEMENT |
| Fig.S21 | VIF and RF performance diagnostics | NEEDS_SUPPLEMENT |

## First-pass reproduction priority

`Fig.1 -> Fig.2 -> Fig.3 -> Fig.4/5 -> Fig.S10`.

This order first validates drought identification, then spatial classification, then ecological response, then attribution, and finally future projection.
