# H0TT fast causal decomposition V2

Uses the same robust fixed-column parser as the completed three-arm workflow. M0/M15TT come from that completed run; only H0TT was newly simulated.

GENERIC=H0TT-M0; LOCAL=M15TT-H0TT; TOTAL=M15TT-M0.

|Year|Sowing|M0 HWAM|H0TT HWAM|M15TT HWAM|Generic dHWAM|Local dHWAM|Total dHWAM|M0 MDAT|H0TT MDAT|M15TT MDAT|
|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2021|Apr21|318|319|319|1.0|0.0|1.0|1214 202|1214 202|1214 202|
|2021|Apr26|1098|1096|1098|-2.0|2.0|0.0|1243 202|1242 202|1242 202|
|2021|May06|1069|1069|1071|0.0|2.0|2.0|1250 202|1250 202|1250 202|
|2021|May16|1943|1942|1942|-1.0|0.0|-1.0|1253 202|1253 202|1253 202|
|2021|May26|3370|3352|3353|-18.0|1.0|-17.0|1261 202|1261 202|1261 202|
|2022|Apr21|495|495|495|0.0|0.0|0.0|2217 202|2217 202|2217 202|
|2022|Apr26|361|363|362|2.0|-1.0|1.0|2217 202|2217 202|2217 202|
|2022|May06|1145|1143|1143|-2.0|0.0|-2.0|2222 202|2222 202|2222 202|
|2022|May16|465|464|464|-1.0|0.0|-1.0|2236 202|2236 202|2236 202|
|2022|May26|779|788|788|9.0|0.0|9.0|2248 202|2248 202|2248 202|

- Generic hourly coupling changes HWAM in **8/10** cases.
- Local M15 correction changes HWAM after controlling hourly coupling in **4/10** cases.
- Generic hourly coupling changes MDAT in **1/10** cases.
- Local M15 correction changes MDAT in **0/10** cases.
