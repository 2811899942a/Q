# M15 DTRc four-level ablation: 14.0 vs 14.3 vs 14.5 vs 14.8 C

Thresholds were prespecified before this run. Alpha values for the crop arms were fitted only from dense-station 2000-2016 temperature data; crop yield was not used for threshold or alpha fitting.

## 1. Threshold-specific temperature calibration and independent validation

|Arm|DTRc|Refit alpha|Validation active days|May-Sep RMSE|DTR>=15 RMSE|Bias May-Sep|R2 May-Sep|Shape violations|TS caps|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|T14P0|14.0|6.8051|180|2.8053|4.6391|+0.1545|0.8207|0|11|
|T14P3|14.3|7.3094|157|2.8104|4.6469|+0.1685|0.8202|0|12|
|T14P5|14.5|7.5925|146|2.8141|4.6556|+0.1791|0.8198|0|11|
|T14P8|14.8|7.8094|130|2.8223|4.6783|+0.1981|0.8188|0|10|

### Pure trigger ablation with alpha fixed at 7.8094

|Arm|DTRc|Validation active days|May-Sep RMSE|DTR>=15 RMSE|
|---|---:|---:|---:|---:|
|T14P0|14.0|180|2.8054|4.6415|
|T14P3|14.3|157|2.8096|4.6449|
|T14P5|14.5|146|2.8136|4.6539|
|T14P8|14.8|130|2.8223|4.6783|

## 2. Shihezi growing-season coverage

|Year|Arm|DTRc|Active days|Active %|
|---:|---|---:|---:|---:|
|2019|T14P0|14.0|66|43.1%|
|2019|T14P3|14.3|56|36.6%|
|2019|T14P5|14.5|52|34.0%|
|2019|T14P8|14.8|46|30.1%|
|2020|T14P0|14.0|67|43.8%|
|2020|T14P3|14.3|61|39.9%|
|2020|T14P5|14.5|56|36.6%|
|2020|T14P8|14.8|47|30.7%|

## 3. Crop propagation using temperature-calibrated alpha

### RAW_N_OFF

|Arm|DTRc|ALL8 RRMSE|Improvement vs H0TT|Change vs T14P8|Wins vs H0TT|Wins vs T14P8|
|---|---:|---:|---:|---:|---:|---:|
|T14P0|14.0|44.799%|-11.19%|+2.532 pp|0/8|0/8|
|T14P3|14.3|44.785%|-11.15%|+2.518 pp|0/8|0/8|
|T14P5|14.5|44.771%|-11.12%|+2.504 pp|0/8|0/8|
|T14P8|14.8|42.268%|-4.90%|+0.000 pp|0/8|0/8|

### SRAD19P8_N_OFF

|Arm|DTRc|ALL8 RRMSE|Improvement vs H0TT|Change vs T14P8|Wins vs H0TT|Wins vs T14P8|
|---|---:|---:|---:|---:|---:|---:|
|T14P0|14.0|24.288%|+9.76%|-0.750 pp|6/8|6/8|
|T14P3|14.3|25.208%|+6.34%|+0.171 pp|6/8|0/8|
|T14P5|14.5|25.179%|+6.45%|+0.142 pp|6/8|0/8|
|T14P8|14.8|25.038%|+6.97%|+0.000 pp|6/8|0/8|

## 4. Interpretation rule

- Use the fixed-alpha table to isolate the trigger-threshold effect itself.
- Use the refit-alpha table to judge each threshold as a fair temperature-model candidate.
- A lower DTRc is eligible only if temperature validation and physical QA remain defensible. Crop yield is downstream evidence and cannot be used to select the threshold.
- T14P8 remains the frozen reference until a lower-threshold candidate passes the temperature-side gate.

