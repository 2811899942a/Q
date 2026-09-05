# M19 regional thermal-anomaly threshold screen

M19 relocates the transferable regional parameter from response amplitude to the anomaly trigger.

- **K_RT = 1.40 SD**: local seasonally standardized DTR anomaly threshold.
- fixed radiative threshold Kt0 = 0.70; fixed P_TARGET = 20.0.
- selected bounded gain scale = 0.25 from the exploratory 2000-2016 mechanism screen.
- official calibration all/high-DTR RMSE = 2.4389 / 5.7359 C.
- selected calibration all/high-DTR RMSE = 2.3946 / 5.3030 C.

Legacy 2017+ continuity benchmark:

|Metric|Official|M19|Improvement|
|---|---:|---:|---:|
|May-Sep RMSE|2.946891|2.833762|3.84%|
|DTR>=15 RMSE|5.121512|4.742319|7.40%|

- high-DTR full-curve physical violations = 0/123
- high-DTR annual wins vs official = 5/5
- gate vs locked physical M15 = **FAIL**
- K_RT inside exploratory search bounds = **PASS**
- inactive-threshold closure max |M19-official| = 0.000e+00 C

Scientific boundary: this is a mechanism/parameter-definition screen. The legacy validation has already influenced the broader model-development sequence and is not a fresh publication test. Final claims require fresh Xinjiang/Urumqi weather plus crop phenology/yield validation.
