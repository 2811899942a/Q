# M15-V2 Round 3 crop propagation result

## Integrity

- Source `0b91373806786b600d89ccfcfff78fa2f82cb26b`; data `79cb5db71bbca186add92a6a9695866a09c8b51d`.
- Shared inputs byte-identical: **PASS**.
- M15_13P5 vs R1_P05 source: exactly **1** shape line difference.
- R1_P05 vs R3_P05_B105 source: exactly **1** nighttime-B line difference.
- Frozen baseline reproduction: **PASS**.

## ALL8 metrics

|Arm|RMSE kg/ha|RRMSE|MAE|Bias|Mean HWAM|
|---|---:|---:|---:|---:|---:|
|H0TT|2977.272|26.914716%|2503.875|+1824.375|12886.250|
|M15_13P5|2820.487|25.497365%|2383.250|+1713.750|12775.625|
|M15_13P8|2656.200|24.012204%|2254.750|+1584.750|12646.625|
|R1_P05|2820.487|25.497365%|2383.250|+1713.750|12775.625|
|R3_P05_B105|2653.066|23.983874%|2254.875|+1645.375|12707.250|

## Direct contrasts

- R3 vs R1 p=.5 RRMSE: **25.497365% -> 23.983874%** (-1.513491 pp).
- R3 vs M15-13.8: **-0.028330 pp**.
- Treatment wins vs R1: **6/8**; vs M15-13.8: **2/8**.

## Year RRMSE

|Arm|2019|2020|
|---|---:|---:|
|H0TT|11.5093%|36.4649%|
|M15_13P5|11.4794%|34.3532%|
|M15_13P8|11.4808%|32.1153%|
|R1_P05|11.4794%|34.3532%|
|R3_P05_B105|11.3582%|32.1170%|

## Prespecified classification

**ROUND3_CROP_STRONG**

Temperature parameters remain frozen regardless of crop classification.
