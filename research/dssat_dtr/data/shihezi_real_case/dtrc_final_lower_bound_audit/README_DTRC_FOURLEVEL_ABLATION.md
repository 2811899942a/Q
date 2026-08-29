# M15 DTRc four-level ablation: 14.0 vs 14.3 vs 14.5 vs 14.8 C

Thresholds were prespecified before this run. Alpha values for the crop arms were fitted only from dense-station 2000-2016 temperature data; crop yield was not used for threshold or alpha fitting.

## 1. Threshold-specific temperature calibration and independent validation

|Arm|DTRc|Refit alpha|Validation active days|May-Sep RMSE|DTR>=15 RMSE|Bias May-Sep|R2 May-Sep|Shape violations|TS caps|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|T13P0|13.0|5.6039|270|2.7881|4.6338|+0.1018|0.8225|0|14|
|T13P5|13.5|6.4080|228|2.7962|4.6344|+0.1225|0.8217|0|15|
|T13P8|13.8|6.7498|199|2.8015|4.6358|+0.1397|0.8211|0|15|
|T14P0|14.0|6.8051|180|2.8053|4.6391|+0.1545|0.8207|0|11|
|T14P8|14.8|7.8094|130|2.8223|4.6783|+0.1981|0.8188|0|10|

### Pure trigger ablation with alpha fixed at 7.8094

|Arm|DTRc|Validation active days|May-Sep RMSE|DTR>=15 RMSE|
|---|---:|---:|---:|---:|
|T13P0|13.0|270|2.7971|4.6764|
|T13P5|13.5|228|2.8001|4.6545|
|T13P8|13.8|199|2.8031|4.6445|
|T14P0|14.0|180|2.8054|4.6415|
|T14P8|14.8|130|2.8223|4.6783|

## 2. Shihezi growing-season coverage

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

## 3. Crop propagation using temperature-calibrated alpha

### RAW_N_OFF

|Arm|DTRc|ALL8 RRMSE|Improvement vs H0TT|Change vs T14P8|Wins vs H0TT|Wins vs T14P8|
|---|---:|---:|---:|---:|---:|---:|
|T13P0|13.0|44.846%|-11.30%|+2.578 pp|0/8|0/8|
|T13P5|13.5|44.826%|-11.25%|+2.559 pp|0/8|0/8|
|T13P8|13.8|44.811%|-11.21%|+2.543 pp|0/8|0/8|
|T14P0|14.0|44.799%|-11.19%|+2.532 pp|0/8|0/8|
|T14P8|14.8|42.268%|-4.90%|+0.000 pp|0/8|0/8|

### SRAD19P8_N_OFF

|Arm|DTRc|ALL8 RRMSE|Improvement vs H0TT|Change vs T14P8|Wins vs H0TT|Wins vs T14P8|
|---|---:|---:|---:|---:|---:|---:|
|T13P0|13.0|25.532%|+5.14%|+0.495 pp|6/8|2/8|
|T13P5|13.5|25.497%|+5.27%|+0.460 pp|6/8|2/8|
|T13P8|13.8|24.012%|+10.78%|-1.025 pp|6/8|6/8|
|T14P0|14.0|24.288%|+9.76%|-0.750 pp|6/8|6/8|
|T14P8|14.8|25.038%|+6.97%|+0.000 pp|6/8|0/8|

## 4. Interpretation rule

- Use the fixed-alpha table to isolate the trigger-threshold effect itself.
- Use the refit-alpha table to judge each threshold as a fair temperature-model candidate.
- A lower DTRc is eligible only if temperature validation and physical QA remain defensible. Crop yield is downstream evidence and cannot be used to select the threshold.
- T14P8 remains the frozen reference until a lower-threshold candidate passes the temperature-side gate.

