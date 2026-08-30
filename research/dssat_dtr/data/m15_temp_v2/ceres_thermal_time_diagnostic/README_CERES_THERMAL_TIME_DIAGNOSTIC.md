# M15-V2 CERES thermal-time sensitivity diagnostic result

## Locked CERES thermal parameters

- DSSAT source: `0b91373806786b600d89ccfcfff78fa2f82cb26b`.
- Ecotype: **IB0001**.
- TBASE: **8.0 C**; TOPT: **34.0 C**; ROPT: **34.0 C**.
- TOPT=ROPT, so the Shihezi case uses one development upper clipping temperature (**34 C**) before and after anthesis.
- HMET hourly sampling is reproduced at H=1,...,24 exactly.
- Scenario: **SRAD19P8_N_OFF**.

## Two-year planting-to-horizon propagation

|Contrast|Days|Days with nonzero DTT delta|Cumulative DTT delta (C d)|Mean abs daily DTT delta|Max abs daily DTT delta|Mean abs hourly temp delta|
|---|---:|---:|---:|---:|---:|---:|
|R1_minus_M15_13P5|350|80|-10.808505|0.030881|0.576254|0.094650|
|R3_minus_R1|350|82|+23.061051|0.065889|0.491153|0.150335|
|M15_13P8_minus_13P5|350|82|+5.996402|0.017133|0.234400|0.039453|

## Year-specific direct thermal-time contrasts

|Year|Contrast|nonzero DTT days|cum DTT delta|mean abs daily delta|max abs daily delta|delta degree-hours <8C|delta degree-hours >34C|
|---:|---|---:|---:|---:|---:|---:|---:|
|2019|R1_minus_M15_13P5|40|-4.359198|0.024768|0.321444|+0.000|-115.237|
|2019|R3_minus_R1|44|+12.600191|0.071592|0.491153|-29.025|+0.000|
|2019|M15_13P8_minus_13P5|44|+2.906680|0.016515|0.234400|-1.797|+10.083|
|2020|R1_minus_M15_13P5|40|-6.449308|0.037065|0.576254|+0.000|-60.260|
|2020|R3_minus_R1|38|+10.460860|0.060120|0.405934|-42.801|+0.000|
|2020|M15_13P8_minus_13P5|38|+3.089721|0.017757|0.191161|-2.614|+4.289|

## Mechanism classification

**ROUND3_HAS_STRONGER_DIRECT_DTT_PROPAGATION**

- Round-1 post-peak shape: mean absolute daily DTT change **0.030881 C d**, cumulative two-year change **-10.808505 C d**, nonzero on **80/350** days.
- Round-3 nighttime-B increment: mean absolute daily DTT change **0.065889 C d**, cumulative two-year change **+23.061051 C d**, nonzero on **82/350** days.

This diagnostic does not fit parameters and does not alter the current temperature winner. Full daily 24-hour TGRO and CERES DTT values are committed in `daily_hourly_thermal_time.csv`.
