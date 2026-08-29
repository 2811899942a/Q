# Final lower-bound DTRc audit

Prespecified primary candidates: **13.5, 13.8, 14.0 C**. 13.0 C is an aggressive lower-bound negative control; 14.8 C is the previous frozen reference.
Threshold/alpha selection uses temperature data only. Crop yield is downstream evidence and is prohibited from selecting DTRc or alpha.

## Independent 2017-2024 temperature validation

|Arm|DTRc|alpha|May-Sep RMSE|DTR>=15 RMSE|Bias|R2|Shape violations|TS caps|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|T13P0|13.0|5.6039|2.7881|4.6338|+0.1018|0.8225|0|14|
|T13P5|13.5|6.4080|2.7962|4.6344|+0.1225|0.8217|0|15|
|T13P8|13.8|6.7498|2.8015|4.6358|+0.1397|0.8211|0|15|
|T14P0|14.0|6.8051|2.8053|4.6391|+0.1545|0.8207|0|11|
|T14P8|14.8|7.8094|2.8223|4.6783|+0.1981|0.8188|0|10|

## Year-by-year stability versus current 14.0 C leader

|Arm|Years with lower May-Sep RMSE than T14P0|Years with lower DTR>=15 RMSE than T14P0|
|---|---:|---:|
|T13P0|5/6|3/5|
|T13P5|5/6|4/5|
|T13P8|5/6|4/5|
|T14P0|reference|reference|
|T14P8|0/6|0/5|

## Shihezi activation coverage

|Year|Arm|DTRc|Active days|Active %|
|---:|---|---:|---:|---:|
|2019|T13P0|13.0|91|59.5%|
|2019|T13P5|13.5|80|52.3%|
|2019|T13P8|13.8|71|46.4%|
|2019|T14P0|14.0|66|43.1%|
|2019|T14P8|14.8|46|30.1%|
|2020|T13P0|13.0|89|58.2%|
|2020|T13P5|13.5|75|49.0%|
|2020|T13P8|13.8|70|45.8%|
|2020|T14P0|14.0|67|43.8%|
|2020|T14P8|14.8|47|30.7%|

## Crop propagation (not a selection criterion)

### RAW_N_OFF

|Arm|ALL8 RRMSE|Improvement vs H0TT|
|---|---:|---:|
|T13P0|44.846%|-11.30%|
|T13P5|44.826%|-11.25%|
|T13P8|44.811%|-11.21%|
|T14P0|44.799%|-11.19%|
|T14P8|42.268%|-4.90%|

### SRAD19P8_N_OFF

|Arm|ALL8 RRMSE|Improvement vs H0TT|
|---|---:|---:|
|T13P0|25.532%|+5.14%|
|T13P5|25.497%|+5.27%|
|T13P8|24.012%|+10.78%|
|T14P0|24.288%|+9.76%|
|T14P8|25.038%|+6.97%|

## Temperature-only provisional winner

Among the prespecified primary candidates (13.5/13.8/14.0 C), the minimum independent May-Sep RMSE with zero-shape-violation gating is **T13P5 (13.5 C)**.

Final interpretation must also inspect the year-by-year table, high-DTR RMSE, bias, cap frequency, and the stop rule from `CHECKPOINT_20260829_FINAL_LOWER_BOUND_PLAN.md`. Do not descend below 13.0 C without new mechanism evidence.
