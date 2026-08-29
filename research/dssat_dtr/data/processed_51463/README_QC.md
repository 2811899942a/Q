# NOAA 51463099999 data QC result

- Station: `51463099999` (Urumqi)
- Requested years: 2000-2024
- NOAA annual files downloaded successfully: **25/25**
- Selected real local-hour temperature observations: **72,177**
- Days with >=20 distinct observed hours (Grade A): **0**
- Days with >=8 distinct observed hours (Grade A+B): **8,637**
- May-Sep Grade A+B days: **3,634**
- Initial HTEMP data verdict: **SPARSE_HTEMP_FEASIBLE**

## Interpretation

`A` days can support direct daily-curve validation. `B` days support HTEMP comparison only at hours actually observed. `C/D` days are auxiliary. No interpolation has been applied. Daily Tmax/Tmin and DTR in the processed table are sample extrema from available reports and must not be called official daily extrema when coverage is incomplete.

## Source

NOAA NCEI Global Hourly / Integrated Surface Database:
https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database

Annual files:
https://www.ncei.noaa.gov/data/global-hourly/access/YYYY/51463099999.csv
