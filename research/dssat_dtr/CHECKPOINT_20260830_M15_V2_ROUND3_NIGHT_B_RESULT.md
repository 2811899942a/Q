# M15-V2 Round 3 result — nighttime B

## Calibration-only selection

- Frozen incoming shape: `p=0.5`.
- Official/frozen baseline B: **2.2**.
- Selected **Bnight = 1.050**.
- Status: **NONBASELINE_B_FROZEN**.
- Active-night calibration observations: **2603**.
- B=2.2 four-block objective: **3.134028 C**.
- selected-B objective: **2.995790 C**.
- Blocks improved vs B=2.2: **4/4**.

Bnight was frozen before all 2017-2024 scores below. Crop output was not read.

## Dense independent validation

|Model|Bnight|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
|ROUND1_P05_B2P2|2.200|May-Sep|29108|1.8369|1.2260|-0.1371|0.9198|
|ROUND1_P05_B2P2|2.200|ActiveNight|1210|3.0852|2.0836|-1.0952|0.7331|
|ROUND1_P05_B2P2|2.200|DTR>=15|1438|3.1951|2.1491|-1.0556|0.8102|
|B_FROZEN|1.050|May-Sep|29108|1.8304|1.2256|-0.1038|0.9199|
|B_FROZEN|1.050|ActiveNight|1210|2.9898|2.0737|-0.2944|0.7221|
|B_FROZEN|1.050|DTR>=15|1438|3.1283|2.1413|-0.7197|0.7999|

## Target-station independent validation

|Model|Bnight|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
|ROUND1_P05_B2P2|2.200|May-Sep|5917|2.7631|1.8278|+0.0676|0.8241|
|ROUND1_P05_B2P2|2.200|DTR>=15|975|4.5408|3.2897|-0.1588|0.6360|
|B_FROZEN|1.050|May-Sep|5917|2.7247|1.7930|+0.1649|0.8278|
|B_FROZEN|1.050|DTR>=15|975|4.4456|3.1787|+0.1043|0.6416|

## Incremental comparison versus Round-1 p=0.5, B=2.2

- Target May-Sep RMSE gain: **+0.0383 C**.
- Target DTR>=15: **4.5408 -> 4.4456 C**.
- Dense active-night: **3.0852 -> 2.9898 C**.
- Target years worse: **0/6**.
- Shape violations: **0**; TS caps: **15**.
- B=2.2 pointwise reproduction max difference: **0.000e+00 C**.

## Prespecified decision

**PROMOTE_NIGHT_B**
