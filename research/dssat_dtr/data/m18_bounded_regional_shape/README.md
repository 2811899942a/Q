# M18 bounded regional DTR-radiation HTEMP shape model

M18 keeps M17's region-relative DTR x radiative-deficit exposure, but replaces
unbounded `exp(k*E)` with a bounded convex shape blend. The continuously fitted
regional coefficient is `K_RT in [0,1]`; `K_RT=0` closes to official HTEMP.

Selected using **2000-2016 leave-one-year-out CV only**:
- q = 0.0
- Kt0 = 0.7
- structural P_MAX = 20.0
- final regional K_RT = 1.00000000
- solver = closed-form bounded least squares
- CV all/high-DTR RMSE = 2.3616 / 5.3392 C
- CV folds at K_RT boundary >=0.995 = 16

Independent legacy validation (2017+; kept only for continuity benchmarking):

|Metric|Official|M18|Improvement|
|---|---:|---:|---:|
|May-Sep RMSE|2.946891|2.789879|5.33%|
|DTR>=15 RMSE|5.121512|4.776875|6.73%|

- high-DTR full-curve physical violations = 0/123
- high-DTR annual RMSE wins vs official = 5/5
- idea-feasibility gate vs locked physical M15 = **FAIL**
- fitted K_RT interior (<0.995) = **BOUNDARY**

Interpretation boundary: 2017+ is a historical/legacy validation set already used
during model development and cannot serve as fresh final publication validation.
The purpose of M18 is to test a bounded transferable parameterization before
source-level DSSAT/CERES-Maize propagation and fresh Urumqi/Xinjiang validation.
