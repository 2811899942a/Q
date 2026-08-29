# Xinjiang extreme-DTR mechanism validation

This analysis was prespecified before the new crop ablation results. M15 remains frozen at DTRc=14.8 C and alpha=7.8094. The 18 C and 20 C crop arms are diagnostic gates only; the M15 correction magnitude still uses DTR-14.8.

## 1. Independent hourly-temperature evidence by DTR

|DTR bin|n hourly points|M0 RMSE C|M15 RMSE C|RMSE reduction|M0 bias|M15 bias|
|---|---:|---:|---:|---:|---:|---:|
|<10|898|1.687|1.687|0.00%|0.275|0.275|
|10-<15|4044|2.398|2.397|0.04%|0.139|0.138|
|15-<18|856|4.835|4.455|7.85%|1.120|0.494|
|18-<20|72|6.290|5.543|11.88%|1.352|-0.557|
|>=20|47|7.602|6.744|11.28%|2.777|-0.307|

High-DTR year robustness (the stored yearly file is the high-DTR validation subset):

|Year|High-DTR days|M0 RMSE C|M15 RMSE C|Reduction|
|---|---:|---:|---:|---:|
|2020|25|5.182|4.722|8.89%|
|2021|33|5.098|4.564|10.47%|
|2022|19|4.796|4.507|6.02%|
|2023|22|4.977|4.626|7.05%|
|2024|24|5.457|4.960|9.10%|

## 2. Shihezi crop-season DTR exposure

|Year|Days analyzed|Mean DTR|Max DTR|DTR>14.8 days|DTR>=18 days|DTR>=20 days|
|---|---:|---:|---:|---:|---:|---:|
|2019|151|13.29|18.28|46|3|0|
|2020|149|13.23|22.33|46|4|1|

## 3. Crop-output extreme-day ablation

All crop, soil, irrigation, cultivar and weather inputs are identical among arms within each scenario. Nitrogen remains disabled to avoid introducing unsupported 2019-2020 fertilizer assumptions.

### RAW_N_OFF

|Arm|ALL8 RRMSE %|change vs H0TT pp|relative improvement vs H0TT|yield-response magnitude share of full M15|error wins vs H0TT|
|---|---:|---:|---:|---:|---:|
|H0TT|40.292|0.000|0.00%|0.0%|0/8|
|M15_FULL|42.268|+1.975|-4.90%|100.0%|0/8|
|M15_18PLUS|40.859|+0.567|-1.41%|20.6%|3/8|
|M15_20PLUS|40.859|+0.567|-1.41%|20.6%|3/8|

### SRAD19P8_N_OFF

|Arm|ALL8 RRMSE %|change vs H0TT pp|relative improvement vs H0TT|yield-response magnitude share of full M15|error wins vs H0TT|
|---|---:|---:|---:|---:|---:|
|H0TT|26.915|0.000|0.00%|0.0%|0/8|
|M15_FULL|25.038|-1.877|+6.97%|100.0%|6/8|
|M15_18PLUS|27.045|+0.130|-0.48%|4.9%|0/8|
|M15_20PLUS|27.045|+0.130|-0.48%|4.9%|0/8|

## 4. Interpretation

- Mean RMSE reduction in the two most extreme DTR strata (18-20 and >=20 C): **11.58%**; in the two ordinary strata below 15 C: **0.02%**.
- This contrast directly tests the intended Xinjiang mechanism: the correction is nearly inactive in ordinary-DTR weather and becomes materially beneficial when DTR is extreme.
- Crop ablation should be interpreted mechanistically: if M15_18PLUS or M15_20PLUS reproduces a substantial share of the full M15 yield response, the crop-level effect is concentrated in the same extreme-DTR regime that shows the largest hourly-temperature error reduction.
- No threshold or M15 parameter in this analysis is selected from crop-yield performance.

