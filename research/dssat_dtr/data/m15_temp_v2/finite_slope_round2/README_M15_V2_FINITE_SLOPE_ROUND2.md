# M15-V2 Round 2 result — finite-slope post-peak warp

## Calibration-only selection

- Formula: `R_k = R + k*R*(1-R)`.
- Frozen **k = 0.865**.
- Status: **NONZERO_K_FROZEN**.
- Active post-peak calibration observations: **918**.
- k=0 four-block objective: **2.489278 C**.
- selected-k objective: **2.373063 C**.
- Blocks improved vs k=0: **3/4**.

k was frozen before the independent 2017-2024 metrics below were computed. Round-1 crop output was not read.

## Dense independent validation

|Model|Parameter|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
|K0_M15|0.000|May-Sep|29108|1.8392|1.2226|-0.1219|0.9197|
|K0_M15|0.000|ActivePostpeak|510|2.5353|1.4026|+0.5711|0.7714|
|K0_M15|0.000|DTR>=15|1438|3.2210|2.1169|-0.8564|0.8065|
|ROUND1_P05|0.500|May-Sep|29108|1.8369|1.2260|-0.1371|0.9198|
|ROUND1_P05|0.500|ActivePostpeak|510|2.4413|1.5964|-0.2953|0.7813|
|ROUND1_P05|0.500|DTR>=15|1438|3.1951|2.1491|-1.0556|0.8102|
|K_FROZEN|0.865|May-Sep|29108|1.8380|1.2249|-0.1324|0.9197|
|K_FROZEN|0.865|ActivePostpeak|510|2.4869|1.5341|-0.0274|0.7723|
|K_FROZEN|0.865|DTR>=15|1438|3.2070|2.1401|-0.9939|0.8092|

## Target-station independent validation

|Model|Parameter|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
|K0_M15|0.000|May-Sep|5917|2.7962|1.8406|+0.1225|0.8217|
|K0_M15|0.000|DTR>=15|975|4.6344|3.3625|+0.0836|0.6293|
|ROUND1_P05|0.500|May-Sep|5917|2.7631|1.8278|+0.0676|0.8241|
|ROUND1_P05|0.500|DTR>=15|975|4.5408|3.2897|-0.1588|0.6360|
|K_FROZEN|0.865|May-Sep|5917|2.7633|1.8277|+0.0688|0.8242|
|K_FROZEN|0.865|DTR>=15|975|4.5436|3.2917|-0.1524|0.6364|

## Incremental comparison with Round-1 p=0.5

- May-Sep RMSE gain: **-0.0003 C**.
- DTR>=15: **4.5408 -> 4.5436 C**.
- Dense active post-peak: **2.4413 -> 2.4869 C**.
- Target years worse than p=0.5: **3/6**.
- Shape violations: **0**; TS caps: **15**.

## Prespecified decision

**RETAIN_ROUND1_P05**

Promotion requires >=0.01 C further target May-Sep RMSE gain versus p=0.5, no material high-DTR degradation, no dense-postpeak degradation, zero physical violations, and <=2 worse target years.
