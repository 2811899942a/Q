# M15-V2 Round 1 result — post-peak power warp

## Frozen parameter selection

- DTRc: **13.5 C**.
- Frozen M15 alpha: **6.407985379809**.
- Selected post-peak exponent: **p = 0.500**.
- Calibration status: **NONUNIT_PARAMETER_FROZEN**.
- Calibration active post-peak observations: **918**.
- p=1 mean four-block RMSE: **2.489278 C**.
- selected-p mean four-block RMSE: **2.305447 C**.
- Calibration blocks improved versus p=1: **4/4**.

Parameter selection used only Diwopu 2000-2016 temperature observations. The parameter was frozen before any 2017-2024 validation metric below was computed.

## Hard baseline reproduction

- p=1 maximum pointwise difference versus audited M15: **0.000e+00 C**.
- Target May-Sep: **n=5917**, RMSE **2.796223546 C** (frozen reference 2.796223546).
- Target DTR>=15 RMSE: **4.634433256 C** (frozen reference 4.634433256).
- Baseline consistency: **PASS**.

## Independent dense-station validation, 2017-2024

|Model|p|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
|P1_FROZEN_M15|1.000|May-Sep|29108|1.8392|1.2226|-0.1219|0.9197|
|P1_FROZEN_M15|1.000|ActivePostpeak|510|2.5353|1.4026|+0.5711|0.7714|
|P1_FROZEN_M15|1.000|DTR>=15|1438|3.2210|2.1169|-0.8564|0.8065|
|P_FROZEN_V2|0.500|May-Sep|29108|1.8369|1.2260|-0.1371|0.9198|
|P_FROZEN_V2|0.500|ActivePostpeak|510|2.4413|1.5964|-0.2953|0.7813|
|P_FROZEN_V2|0.500|DTR>=15|1438|3.1951|2.1491|-1.0556|0.8102|

## Independent target-station validation, 2017-2024

|Model|p|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
|P1_FROZEN_M15|1.000|May-Sep|5917|2.7962|1.8406|+0.1225|0.8217|
|P1_FROZEN_M15|1.000|DTR>=15|975|4.6344|3.3625|+0.0836|0.6293|
|P_FROZEN_V2|0.500|May-Sep|5917|2.7631|1.8278|+0.0676|0.8241|
|P_FROZEN_V2|0.500|DTR>=15|975|4.5408|3.2897|-0.1588|0.6360|

- Target May-Sep RMSE gain versus frozen M15-13.5: **+0.0331 C**.
- Target years with worse May-Sep RMSE than p=1: **0/6**.

## Physical QA

- Active target-validation days: **230**.
- Shape violations: **0**.
- TS caps: **15**.
- Maximum above Tmax: **0.000e+00 C**.
- Maximum below Tmin: **0.000e+00 C**.

## Prespecified decision

**KEEP_FOR_DSSAT_CROP_PROPAGATION**

KEEP requires: non-unit stable calibration; dense active-postpeak validation no worse; target May-Sep gain >=0.03 C; target DTR>=15 degradation <=0.01 C; zero physical violations; <=2 target years worse than p=1.

If decision is `DROP_POSTPEAK_POWER`, the next mechanism is the separately prespecified bounded nighttime-decay refinement. Crop results cannot rescue this round if the temperature gate fails.
