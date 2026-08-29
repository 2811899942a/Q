# Shihezi M0 nitrogen root-cause diagnostic

**Purpose:** sensitivity/root-cause screen only. Finite-N schedules are NOT claimed to be the exact Guo 2019–2020 fertilizer management. Xinyu66 genetics, weather, irrigation and other V4 assumptions are unchanged.

|Scenario|RMSE kg/ha|RRMSE %|MAE kg/ha|Bias kg/ha|Mean HWAM kg/ha|
|---|---:|---:|---:|---:|---:|
|UNLIMITED|6684.8|60.771|6603.0|6603.0|17603.0|
|N64_SPLIT|6335.9|57.599|6270.0|-6270.0|4730.0|
|N129_SPLIT|6335.9|57.599|6270.0|-6270.0|4730.0|
|N193_SPLIT|6335.9|57.599|6270.0|-6270.0|4730.0|
|N129_BASAL|6335.9|57.599|6270.0|-6270.0|4730.0|

Best finite-N diagnostic: **N64_SPLIT**, RRMSE 57.599% versus unlimited-N 60.771% (relative reduction 5.22%).

Interpretation rule: if finite N materially moves M0 toward the published 5.69% RRMSE, nitrogen representation remains a priority reconstruction variable. If it does not, nitrogen is not sufficient to explain the V4 mismatch. No modified-temperature accuracy claim follows from this diagnostic.
