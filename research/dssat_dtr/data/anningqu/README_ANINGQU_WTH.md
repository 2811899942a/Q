# Anningqu DSSAT weather reconstruction, 2021-2022

## Status

Two standard DSSAT v4.8.5 weather files were generated:
- `ANQH2101.WTH`
- `ANQH2201.WTH`

Station metadata used for the Anningqu experiment: `ANQH`, 43.950 N, 87.490 E, 590 m.

## Temperature hierarchy

Across 2021-2022 (730 calendar days):
- dense NOAA ISD 51463599999 days (>=20 distinct solar hours): **720**
- GHCN CHM00051463 fallback days: **6**
- NASA POWER T2M fallback days: **4**

No interpolation was used to create a daily station Tmax/Tmin. Each day is either based on dense real reports or explicitly flagged as a fallback source.

## Radiation and precipitation

Daily SRAD and RAIN come from NASA POWER at the Anningqu coordinate in **LST**:
`ALLSKY_SFC_SW_DWN` and `PRECTOTCORR`.

POWER request used by the workflow:
`https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN,PRECTOTCORR,T2M_MAX,T2M_MIN&community=AG&longitude=87.49&latitude=43.95&start=20210101&end=20221231&format=JSON&time-standard=LST`

This rainfall is a gridded/reanalysis-derived public estimate, not a local rain-gauge measurement. It must therefore remain a disclosed uncertainty/sensitivity dimension. For the first crop propagation experiment, the fully irrigated treatment is preferred because temperature-pathway attribution is cleaner.

## DSSAT climate constants

Using dense NOAA 51463599999 daily extrema from 2000-2024 on days with >=20 observed solar hours:
- `TAV = 9.08 C`
- `AMP = 40.58 C`
- monthly climatological Tmean (Jan-Dec C): 1:-13.82, 2:-9.70, 3:2.16, 4:13.72, 5:19.79, 6:24.85, 7:26.76, 8:25.30, 9:19.53, 10:10.65, 11:0.20, 12:-10.46

These values are used identically in M0 and M15.

## 2022 same-site external consistency check

The public 2022-2023 DSSAT peanut study at the Anningqu Comprehensive Experimental Station reports 2022 growing-season rainfall of about **63.1 mm** and a temperature envelope of approximately **Tmax 3.7-38.5 C / Tmin -1.4-26.6 C** during its stated season.

Current public WTH reconstruction gives for 2022:
- May-Oct POWER rainfall: **98.32 mm**
- full-year maximum Tmax: **40.00 C**
- full-year minimum Tmin: **-22.70 C**

The rainfall values are not expected to match exactly because the paper reports local station/experimental-season precipitation whereas POWER is a gridded estimate and May-Oct is a fixed comparison window. Any material discrepancy is retained as uncertainty rather than scaled away.

## Comparison rule

M0 official DSSAT v4.8.5 and M15 must use these exact same WTH files. No weather variable is recalibrated separately for either source version. The M15 `CLOUDS` driver is calculated internally by DSSAT from the WTH SRAD using its existing `SOLAR.for` pathway.
