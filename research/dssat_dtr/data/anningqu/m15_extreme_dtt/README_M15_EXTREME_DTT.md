# Anningqu M15 extreme-DTT three-arm propagation test

Arms: M0 = official DSSAT v4.8.5; M15W = frozen Urumqi HMET hourly-temperature correction only; M15TT = M15W plus replacement of CERES-Maize synthetic extreme-day hourly TH with WEATHER%TGRO.

The M15TT crop coupling is active only in the pre-existing CERES branch `TMIN < TBASE OR TMAX > DOPT`; the normal-temperature DTT branch and thermal thresholds are unchanged.

|Year|Sowing|M0 ADAT|M15W ADAT|M15TT ADAT|M0 MDAT|M15TT MDAT|M0 HWAM|M15W HWAM|M15TT HWAM|dHWAM TT-W|M0 CWAM|M15TT CWAM|dCWAM TT-W|
|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2021|Apr21|1189 202|1189 202|1189 202|1214 202|1214 202|318|318|319|1.0|0770|0778|8.0|
|2021|Apr26|1191 202|1191 202|1191 202|1243 202|1242 202|1098|1098|1098|0.0|1615|1622|7.0|
|2021|May06|1198 202|1198 202|1198 202|1250 202|1250 202|1069|1069|1071|2.0|0741|0734|-7.0|
|2021|May16|1201 202|1201 202|1201 202|1253 202|1253 202|1943|1943|1942|-1.0|0989|0991|2.0|
|2021|May26|1208 202|1208 202|1208 202|1261 202|1261 202|3370|3370|3353|-17.0|2771|2762|-10.0|
|2022|Apr21|2184 202|2184 202|2184 202|2217 202|2217 202|495|495|495|0.0|0492|0505|13.0|
|2022|Apr26|2186 202|2186 202|2186 202|2217 202|2217 202|361|361|362|1.0|9932|9944|12.0|
|2022|May06|2189 202|2189 202|2189 202|2222 202|2222 202|1145|1145|1143|-2.0|0752|0766|14.0|
|2022|May16|2203 202|2203 202|2203 202|2236 202|2236 202|465|465|464|-1.0|0897|0910|13.0|
|2022|May26|2211 202|2211 202|2211 202|2248 202|2248 202|779|779|788|9.0|1105|1135|30.0|

- Weather-only M15W scenarios with any Summary response: **1/10** (ANQH2105).
- Extreme-DTT coupling M15TT scenarios with any Summary response relative to M15W: **10/10** (ANQH2101, ANQH2102, ANQH2103, ANQH2104, ANQH2105, ANQH2201, ANQH2202, ANQH2203, ANQH2204, ANQH2205).
- Primary causal contrast for the new relationship is M15TT minus M15W. M0 minus M15W checks whether weather-only hourly improvement reaches CERES outputs without the coupling.
