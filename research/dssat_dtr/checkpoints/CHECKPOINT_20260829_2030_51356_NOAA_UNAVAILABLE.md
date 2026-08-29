# CHECKPOINT 2026-08-29 20:30 CST — Shihezi 51356 NOAA daily-data probe closed

## Run
Workflow: `.github/workflows/shihezi-51356-weather-probe.yml`
Run ID: `33251318548`
Status: SUCCESS.
Result directory: `research/dssat_dtr/data/shihezi_real_case/station_weather_probe/`

## Station identity confirmed
NOAA ISD history resolves:
- USAF: 513560
- WBAN: 99999
- station name: SHIHEZI
- country: CH
- coordinates: 44.300 N, 86.033 E
- elevation: 457 m
- public ISD period: 1956-08-20 to 1997-12-31

This is spatially close to the Guo field site (44°19′28″N, 85°59′47″E; 412 m) and confirms the WMO/USAF station identity.

## 2019–2020 public NOAA result
Direct probes were attempted for:
- NOAA Global Summary of the Day: `51356099999` for 2019 and 2020
- GHCN-Daily: `CHM00051356`

Neither source contains usable 2019–2020 station records. The GSOD/GHCN output count is zero for both years. This is consistent with the ISD-history end date of 1997-12-31.

Therefore **NOAA cannot supply the required Shihezi 51356 daily TMAX/TMIN/PRCP for the Guo 2019–2020 validation case**. Do not spend more time retrying NOAA station IDs for this case unless new metadata indicate a successor station identifier.

## Current provisional POWER forcing (May–Aug)
2019 POWER:
- mean Tmax 31.485 C
- mean Tmin 18.046 C
- precipitation 93.41 mm
- mean SRAD 22.949 MJ m-2 d-1

2020 POWER:
- mean Tmax 31.651 C
- mean Tmin 18.288 C
- precipitation 118.84 mm
- mean SRAD 23.622 MJ m-2 d-1

These remain provisional and are not claimed to reproduce the authors' validation weather.

## Important source constraint from Guo (2025)
Guo explicitly states that CERES-Maize daily weather inputs include SRAD, TMAX, TMIN and RAIN and that meteorological data are mainly from the **National Meteorological Science Data Center (China/CMA) and NASA**. Therefore the next weather-reconstruction priority is a CMA/National Meteorological Science Data Center daily dataset or a defensible mirror of that product, not further NOAA probing.

## Next action
Search for 2019–2020 Shihezi 51356 in CMA daily ground-climate products, especially `SURF_CLI_CHN_MUL_DAY` or mirrors/archives that preserve station-level daily Tmax, Tmin and precipitation. If recovered, compare against POWER and Guo Fig. 2-2 before any new crop run.

## Scientific rules
- No crop/genotype/M15 retuning.
- No real-yield accuracy claim while M0 reproduction gate fails.
- Every material result/error/method switch gets a checkpoint before further computation.
