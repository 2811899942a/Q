# Formal Anningqu DSSAT weather rainfall selection

Formal M0/M15 crop runs use GHCN-Daily `CHM00051463` precipitation wherever a clean daily PRCP record exists. NASA POWER rainfall is used only for missing GHCN days. SRAD remains NASA POWER; TMAX/TMIN remain the previously QC-controlled dense-station hierarchy.

The original all-POWER-rain WTH pair is preserved under `sensitivity_power_rain/`.

## Rainfall coverage
| Year | GHCN rain days | POWER fallback days | Annual formal rain |
|---|---:|---:|---:|
| 2021 | 330 | 35 | 401.5 mm |
| 2022 | 320 | 45 | 205.4 mm |

2022 May-Oct formal rainfall: **76.5 mm**. The nearby Anningqu DSSAT peanut paper reports about **63.1 mm** for its own 2022 growing season; this is an external magnitude check, not a rescaling target.

## 2022 Tang sowing-to-expected-harvest windows
- A: **70.1 mm**
- B: **60.7 mm**
- C: **59.2 mm**
- D: **53.1 mm**
- E: **57.4 mm**

GHCN source: `https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/CHM00051463.csv.gz`.

Formal comparison rule: M0 and M15 use byte-identical weather inputs. The POWER-rain pair is used only for rainfall-source sensitivity and is never used to tune M15.
