# H0TT fast causal decomposition

H0TT is official DSSAT HMET hourly temperature coupled to the existing CERES extreme-day DTT branch. M0 and M15TT are taken from the completed three-arm real-DSSAT run.

GENERIC=H0TT-M0; LOCAL=M15TT-H0TT; TOTAL=M15TT-M0.

|Year|Sowing|M0 HWAM|H0TT HWAM|M15TT HWAM|Generic dHWAM|Local dHWAM|Total dHWAM|M0 MDAT|H0TT MDAT|M15TT MDAT|
|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2021|Apr21|318|-99|319|-417.0|418.0|1.0|1214 202|2021121|1214 202|
|2021|Apr26|1098|-99|1098|-1197.0|1197.0|0.0|1243 202|2021123|1242 202|
|2021|May06|1069|-99|1071|-1168.0|1170.0|2.0|1250 202|2021133|1250 202|
|2021|May16|1943|-99|1942|-2042.0|2041.0|-1.0|1253 202|2021143|1253 202|
|2021|May26|3370|-99|3353|-3469.0|3452.0|-17.0|1261 202|2021151|1261 202|
|2022|Apr21|495|-99|495|-594.0|594.0|0.0|2217 202|2022121|2217 202|
|2022|Apr26|361|-99|362|-460.0|461.0|1.0|2217 202|2022123|2217 202|
|2022|May06|1145|-99|1143|-1244.0|1242.0|-2.0|2222 202|2022133|2222 202|
|2022|May16|465|-99|464|-564.0|563.0|-1.0|2236 202|2022142|2236 202|
|2022|May26|779|-99|788|-878.0|887.0|9.0|2248 202|2022152|2248 202|

- HWAM changed by generic hourly coupling: **10/10**.
- HWAM changed by local M15 correction after controlling hourly coupling: **10/10**.
- MDAT changed by generic hourly coupling: **0/10**.
- MDAT changed by local M15 correction: **0/10**.
