# Shihezi M0 nitrogen root-cause diagnostic V2 (MF=1)

**Purpose:** sensitivity/root-cause screen only. Finite-N schedules are NOT claimed to be the exact Guo 2019–2020 fertilizer management. Xinyu66 genetics, weather, irrigation and other V4 assumptions are unchanged.

|Scenario|RMSE kg/ha|RRMSE %|MAE kg/ha|Bias kg/ha|Mean HWAM kg/ha|
|---|---:|---:|---:|---:|---:|
|UNLIMITED|6684.8|60.771|6603.0|6603.0|17603.0|
|N64_SPLIT|3818.0|34.709|3709.2|-3709.2|7290.8|
|N129_SPLIT|2737.9|24.890|2600.2|-2600.2|8399.8|
|N193_SPLIT|1860.0|16.909|1598.2|-1598.2|9401.8|
|N129_BASAL|2684.4|24.403|2513.2|-2513.2|8486.8|

Best finite-N diagnostic: **N193_SPLIT**, RRMSE 16.909% versus unlimited-N 60.771% (relative reduction 72.17%).

Interpretation rule: if finite N materially moves M0 toward the published 5.69% RRMSE, nitrogen representation remains a priority reconstruction variable. If it does not, nitrogen is not sufficient to explain the V4 mismatch. No modified-temperature accuracy claim follows from this diagnostic.
