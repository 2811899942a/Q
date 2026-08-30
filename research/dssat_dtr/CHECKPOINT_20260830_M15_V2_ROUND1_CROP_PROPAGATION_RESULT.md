# M15-V2 Round 1 crop propagation result

## Execution integrity

- DSSAT source commit: `0b91373806786b600d89ccfcfff78fa2f82cb26b`.
- DSSAT data commit: `79cb5db71bbca186add92a6a9695866a09c8b51d`.
- Scenario: **SRAD19P8_N_OFF**.
- Shared crop/weather/soil/management input byte-identity gate: **PASS**.
- M15_13P5 vs V2_P05 HMET source isolation: **PASS**, exactly **1** changed line (the `R -> SQRT(R)` post-peak shape line).
- Frozen baseline reproduction gate: **PASS**.
- Crop output was not used to fit or alter `p=0.5`, `DTRc=13.5 C`, or alpha.

## ALL8 crop metrics

|Arm|RMSE kg/ha|RRMSE|MAE kg/ha|Bias kg/ha|Mean HWAM kg/ha|
|---|---:|---:|---:|---:|---:|
|H0TT|2977.272|26.914716%|2503.875|+1824.375|12886.250|
|M15_13P5|2820.487|25.497365%|2383.250|+1713.750|12775.625|
|M15_13P8|2656.200|24.012204%|2254.750|+1584.750|12646.625|
|V2_P05|2820.487|25.497365%|2383.250|+1713.750|12775.625|

## Direct downstream contrasts

- V2 vs frozen M15-13.5 RRMSE change: **+0.000000 percentage points**.
- V2 vs frozen M15-13.8 RRMSE change: **+1.485161 percentage points**.
- V2 relative RRMSE improvement vs H0TT: **5.266%**.
- Treatment-level absolute-error wins vs M15-13.5: **0/8**.
- Treatment-level absolute-error wins vs M15-13.8: **2/8**.

## Year-specific RRMSE

|Arm|2019|2020|
|---|---:|---:|
|H0TT|11.5093%|36.4649%|
|M15_13P5|11.4794%|34.3532%|
|M15_13P8|11.4808%|32.1153%|
|V2_P05|11.4794%|34.3532%|

## Prespecified downstream classification

**NO_CROP_GAIN**

Classification was fixed before the V2 crop output was read:
- STRONG: V2 RRMSE < M15-13.5 and <= M15-13.8, plus >=4/8 treatment wins vs M15-13.5.
- PARTIAL: V2 RRMSE < M15-13.5 but > M15-13.8.
- NO_CROP_GAIN: V2 RRMSE >= M15-13.5.

The temperature result remains independently valid regardless of this downstream crop classification. No crop result is allowed to retune the temperature algorithm.
