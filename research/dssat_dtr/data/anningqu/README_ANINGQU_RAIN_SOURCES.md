# Anningqu 2021-2022 precipitation-source comparison

Two independent public sources are compared without rescaling:
- NASA POWER `PRECTOTCORR` at 87.49 E, 43.95 N, LST;
- NOAA GHCN-Daily `CHM00051463` `PRCP`, clean records only.

The nearby Anningqu 2022 DSSAT peanut study reports **63.1 mm** total growing-season rainfall. Its exact crop-season window differs from the fixed May-Oct comparison below, so this number is an external magnitude check rather than a fitting target.

## 2022 May-Oct
- POWER: **98.32 mm**
- GHCN: **76.5 mm**, coverage **99.46%**

## 2022 Tang maize windows
| Sowing window | POWER rain | GHCN rain | GHCN coverage |
|---|---:|---:|---:|
| TANG_A (04-21 to 09-04) | 89.27 | 70.1 | 100.0% |
| TANG_B (04-26 to 09-07) | 81.34 | 60.7 | 100.0% |
| TANG_C (05-06 to 09-15) | 80.2 | 59.2 | 99.25% |
| TANG_D (05-16 to 09-27) | 73.12 | 53.1 | 99.26% |
| TANG_E (05-26 to 10-13) | 78.62 | 57.4 | 99.29% |

GHCN download used: `https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/CHM00051463.csv.gz`.

Decision rule: prefer GHCN for formal WTH rainfall only if daily coverage is essentially complete and values are internally plausible. If observed-station and gridded precipitation materially disagree, retain both as a rainfall sensitivity pair; do not force either source to match 63.1 mm. The first M0-vs-M15 crop propagation experiment remains the fully irrigated treatment, reducing sensitivity to this rainfall choice.
