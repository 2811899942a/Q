# M15-V2 Round 4 result — nonlinear CLOUDS gamma

## Blocked calibration CV
- Frozen gamma: **1.110**; final alpha: **7.319617798**.
- Status: **NONUNIT_GAMMA_FROZEN**.
- gamma=1 alpha reproduction: **6.407985379809**.
- gamma=1 CV RMSE: **2.668380 C**; selected: **2.662870 C**.
- Held-out blocks improved: **3/4**.

## Independent validation
- Dense sunset RMSE: **2.7327 -> 2.7126 C**; bias **+0.0013 -> +0.0460 C**.
- Dense May-Sep hourly RMSE: **1.8304 -> 1.8297 C**.
- Target May-Sep RMSE: **2.7247 -> 2.7234 C** (gain +0.0013 C).
- Target DTR>=15 RMSE: **4.4456 -> 4.4448 C**.
- Target years worse: **1/6**.
- Shape violations: **0**; TS caps: **17**.
- gamma=1 Round-3 pointwise reproduction max difference: **0.000e+00 C**.

## Prespecified decision
**RETAIN_ROUND3_GAMMA1**
