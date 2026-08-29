# Shihezi M0 source-gap attribution diagnostic

This is a reconstruction-diagnostic experiment only. No cultivar coefficient, M15 threshold, or crop-output parameter is fitted.

- BASE: current V4 NASA POWER reconstruction, N stress disabled.
- RAIN_MATCH: precipitation multiplied by a year-specific factor so the current crop-period PRCP magnitude approaches the thesis reported 96.45/119.88 mm.
- SRAD_19P8: solar radiation multiplied by a year-specific factor so current simulated crop-period mean SRAD approaches the thesis reported ~19.8 MJ m-2 d-1.
- WEATHER_BOTH: both source-supported magnitude checks together.
- N_LOW_BOUND: N stress enabled with existing minimal initial N and no fertilizer; this is only a lower bound because fertilizer is missing from Chapter 2.

Run status: `{"BASE": "PASS", "RAIN_MATCH": "PASS", "SRAD_19P8": "PASS", "WEATHER_BOTH": "PASS", "N_LOW_BOUND": "PASS"}`

|Scenario|Year|RRMSE %|Mean HWAM kg/ha|Bias kg/ha|Mean SRADA|Mean PRCP|
|---|---:|---:|---:|---:|---:|---:|
|BASE|2019|18.602|12768.5|1644.8|23.30|83.30|
|BASE|2020|60.771|17603.0|6603.0|24.20|103.10|
|RAIN_MATCH|2019|18.602|12768.5|1644.8|23.30|83.30|
|RAIN_MATCH|2020|60.771|17603.0|6603.0|24.20|103.10|
|SRAD_19P8|2019|18.602|12768.5|1644.8|23.30|83.30|
|SRAD_19P8|2020|60.771|17603.0|6603.0|24.20|103.10|
|WEATHER_BOTH|2019|18.602|12768.5|1644.8|23.30|83.30|
|WEATHER_BOTH|2020|60.771|17603.0|6603.0|24.20|103.10|
|N_LOW_BOUND|2019|57.211|4865.2|-6258.5|23.30|83.30|
|N_LOW_BOUND|2020|57.599|4730.0|-6270.0|24.20|103.10|

## 2020 attribution relative to BASE

- RAIN_MATCH: mean HWAM shift +0.0 kg/ha; RRMSE shift +0.000 percentage points.
- SRAD_19P8: mean HWAM shift +0.0 kg/ha; RRMSE shift +0.000 percentage points.
- WEATHER_BOTH: mean HWAM shift +0.0 kg/ha; RRMSE shift +0.000 percentage points.
- N_LOW_BOUND: mean HWAM shift -12873.0 kg/ha; RRMSE shift -3.172 percentage points.

Interpretation rule: weather scenarios can identify whether the provisional weather magnitude is sufficient to explain the failed M0 reproduction gate. N_LOW_BOUND only tests whether the missing N-management block has enough leverage to explain the remaining discrepancy; it cannot be used as a final reconstruction.
