# M17 regional radiative monotonic warp

Selected only by 2000-2016 leave-one-year-out temperature CV.

- selected q=0.0, Kt0=0.6; k_pre=39.999999, k_post=39.999998
- calibration LOYO all/high-DTR RMSE=2.2477/4.8144 C
- validation physical violations=0/123

|Metric|Official|M17|Improvement|
|---|---:|---:|---:|
|May-Sep RMSE|2.946891|2.583205|12.34%|
|DTR>=15 RMSE|5.121512|4.376778|14.54%|

Hard gate versus M12 statistical target (2.7639 / 4.4623 C) and physical QA: **PASS**.

This benchmark is historical/legacy and cannot serve as fresh final validation.

Expanded numerical coefficient bound: 0 <= k <= 40. Formula and discrete candidate grids unchanged.
