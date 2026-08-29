# Urumqi 51463 formal DTR merge result

- GHCN station: `CHM00051463`
- ISD station: `51463099999`
- Period: 2000-2024
- GHCN daily TMAX/TMIN pairs merged: **7,036** days
- Days with both clean GHCN DTR and ISD Grade A/B sub-daily observations: **6,626**
- May-Sep matched days: **2,709**
- Formal DTR >=15 C days (matched A/B): **390**
- Formal DTR >=20 C days (matched A/B): **21**
- May-Sep DTR >=15 C days: **198**
- May-Sep DTR >=20 C days: **9**
- Mean formal DTR on matched A/B days: **9.93 C**
- Mean formal DTR in May-Sep matched days: **11.17 C**

## Formal use rule

For DSSAT-DTR experiments, define daily DTR from GHCN-Daily (`TMAX-TMIN`) and use the ISD observations only as real sub-daily checkpoints for the reconstructed temperature curve. Do not derive the formal daily DTR from the sparse ISD sample extrema.

## Sources

- GHCN-Daily station file: https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/CHM00051463.csv.gz
- NOAA GHCN-Daily documentation: https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt
- NOAA Global Hourly / ISD: https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database
