# Weather-gap V4 checkpoint

Engineering propagation status: PASS. The canonical `/tmp/run_M0/Weather` files were edited in place, audited immediately before execution, and `Summary.OUT` SRADA/PRCP moved in the requested direction.

|Scenario|Year|RRMSE %|Mean HWAM kg/ha|Bias kg/ha|Summary SRADA|Summary PRCP|WTH mean SRAD|WTH total RAIN|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|BASE|2019|18.602|12768.5|+1644.8|23.30|83.30|19.942|125.50|
|BASE|2020|60.771|17603.0|+6603.0|24.20|103.10|20.576|153.40|
|RAIN_MATCH|2019|18.640|12771.0|+1647.2|23.30|96.10|19.942|144.80|
|RAIN_MATCH|2020|60.996|17626.8|+6626.8|24.20|119.40|20.576|177.60|
|SRAD_19P8|2019|11.738|10784.0|-339.8|19.90|81.70|16.947|125.50|
|SRAD_19P8|2020|33.500|14532.5|+3532.5|19.80|105.30|16.838|153.40|
|WEATHER_BOTH|2019|11.738|10784.0|-339.8|19.90|94.20|16.947|144.80|
|WEATHER_BOTH|2020|33.591|14543.0|+3543.0|19.80|122.00|16.838|177.60|

## 2020 effects relative to BASE

- RAIN_MATCH: RRMSE +0.225 percentage points; mean HWAM +23.8 kg/ha; SRADA +0.00; PRCP +16.30 mm.
- SRAD_19P8: RRMSE -27.270 percentage points; mean HWAM -3070.5 kg/ha; SRADA -4.40; PRCP +2.20 mm.
- WEATHER_BOTH: RRMSE -27.180 percentage points; mean HWAM -3060.0 kg/ha; SRADA -4.40; PRCP +18.90 mm.

This is a source-magnitude diagnostic with nitrogen disabled. It quantifies weather leverage on the current M0 gap; it does not define the final 2019–2020 weather reconstruction by yield fit.
