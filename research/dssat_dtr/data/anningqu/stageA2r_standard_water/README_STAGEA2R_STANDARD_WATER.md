# Anningqu Stage A2R: standard CERES water pathway, M0 vs M15

Configuration: DSSAT v4.8.5; WATER=Y, NITRO=N, EVAPO=R, PHOTO=R; one Water-6 irrigation of 67.5 mm at sowing and no later irrigation. M0/M15 management and WTH are identical.

This is a clean source-propagation diagnostic after rejecting EVAPO=Z/PHOTO=L (ETPHOT requires an absent maize !*PHOT block) and EVAPO=H (TRANS requires absent maize PHSV/PHTV). No humidity, dew point, wind, or crop parameters were invented.

|Year|Sowing|M0 HWAM|M15 HWAM|dHWAM|M0 CWAM|M15 CWAM|dCWAM|M0 ETCM|M15 ETCM|dETCM|M0 SWXM|M15 SWXM|dSWXM|
|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2021|Apr21|318|318|0.000|0770|0770|0.000|312|312|0.000|0|0|0.000|
|2021|Apr26|1098|1098|0.000|1615|1615|0.000|338|338|0.000|0|0|0.000|
|2021|May06|1069|1069|0.000|0741|0741|0.000|342|342|0.000|0|0|0.000|
|2021|May16|1943|1943|0.000|0989|0989|0.000|324|324|0.000|0|0|0.000|
|2021|May26|3370|3370|0.000|2771|2772|1.000|314|314|0.000|0|0|0.000|
|2022|Apr21|495|495|0.000|0492|0492|0.000|290|290|0.000|0|0|0.000|
|2022|Apr26|361|361|0.000|9932|9932|0.000|276|276|0.000|0|0|0.000|
|2022|May06|1145|1145|0.000|0752|0752|0.000|272|272|0.000|0|0|0.000|
|2022|May16|465|465|0.000|0897|0897|0.000|282|282|0.000|0|0|0.000|
|2022|May26|779|779|0.000|1105|1105|0.000|282|282|0.000|0|0|0.000|

- Scenarios with any M0-M15 process/crop difference: **1/10**.
- Changed scenarios: ANQH2105.
- Interpretation gate: if all deltas remain zero, the frozen M15 hourly correction is not consumed by standard CERES-Maize water/crop outputs under this configuration; further crop-response work must target a source pathway that actually uses subdaily temperature, rather than tuning management to force a difference.
