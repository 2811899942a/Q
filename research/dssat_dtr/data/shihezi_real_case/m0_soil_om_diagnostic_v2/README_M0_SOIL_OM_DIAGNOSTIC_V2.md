# Shihezi M0 soil organic-matter interpretation diagnostic V2

**Status:** direct diagnostic after nested-wrapper failure. No crop or temperature parameter is calibrated here. HIGHOM interprets Guo Table 2-1 numeric OM values as percent OM, giving topsoil ~14.85 g/kg OM and SLOC 0.8614%, consistent in magnitude with an independent 2021 same-station Xinyu66 measurement (~14.12 g/kg).

|Scenario|HIGHOM RRMSE %|LOWOM RRMSE %|RMSE kg/ha|Bias kg/ha|Mean HWAM kg/ha|
|---|---:|---:|---:|---:|---:|
|HIGHOM_N129_SPLIT|24.890|24.890|2737.9|-2600.2|8399.8|
|HIGHOM_N193_SPLIT|16.909|16.909|1860.0|-1598.2|9401.8|
|HIGHOM_N129_BASAL|24.403|24.403|2684.4|-2513.2|8486.8|

Best HIGHOM diagnostic: **HIGHOM_N193_SPLIT**, RRMSE **16.909%**.

Interpretation rule: HIGHOM improving over the corresponding LOWOM case supports the OM-unit hypothesis as an important reconstruction issue. It does not establish the exact 2019–2020 fertilizer schedule and cannot by itself validate M15TT yield accuracy.
