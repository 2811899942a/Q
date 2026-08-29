# Shihezi three-arm SRAD x N yield-accuracy matrix

Purpose: test whether the frozen M15 temperature correction improves crop-output accuracy after correcting major shared-input gaps. No common input is selected by M15 performance.

Temperature evidence is already frozen independently: M15 reduced May-Sep hourly RMSE 2.9469 -> 2.8241 C (4.17%); on DTR>=15 C days 5.1215 -> 4.6783 C (8.65%), with bias +1.2167 -> +0.3784 C.

## Yield RRMSE by common-input scenario

|Scenario|Period|M0|H0TT|M15TT|M15-M0 pp|M15-H0 pp|M15 relative improvement vs M0|
|---|---|---:|---:|---:|---:|---:|---:|
|RAW_N_OFF|2019|18.609|17.488|18.609|+0.000|+1.121|+0.00%|
|RAW_N_OFF|2020|60.911|54.505|57.090|-3.821|+2.585|+6.27%|
|RAW_N_OFF|ALL8|44.827|40.292|42.268|-2.559|+1.975|+5.71%|
|SRAD19P8_N_OFF|2019|11.738|11.509|11.359|-0.379|-0.151|+3.23%|
|SRAD19P8_N_OFF|2020|33.559|36.465|33.704|+0.145|-2.761|-0.43%|
|SRAD19P8_N_OFF|ALL8|25.030|26.915|25.038|+0.008|-1.877|-0.03%|
|RAW_N129_STAGE|2019|58.640|59.042|58.640|-0.000|-0.402|+0.00%|
|RAW_N129_STAGE|2020|62.462|64.902|63.790|+1.329|-1.112|-2.13%|
|RAW_N129_STAGE|ALL8|60.561|62.009|61.241|+0.681|-0.768|-1.12%|
|SRAD19P8_N129_STAGE|2019|53.227|54.621|54.375|+1.148|-0.246|-2.16%|
|SRAD19P8_N129_STAGE|2020|50.836|51.034|50.851|+0.014|-0.184|-0.03%|
|SRAD19P8_N129_STAGE|ALL8|52.060|52.879|52.663|+0.603|-0.216|-1.16%|
|SRAD19P8_N193_STAGE|2019|42.895|44.642|44.306|+1.410|-0.336|-3.29%|
|SRAD19P8_N193_STAGE|2020|41.710|41.895|41.490|-0.220|-0.405|+0.53%|
|SRAD19P8_N193_STAGE|ALL8|42.314|43.306|42.938|+0.623|-0.368|-1.47%|

## Paired treatment-year wins

|Scenario|M15 better than M0|M15 better than H0TT|
|---|---:|---:|
|RAW_N_OFF|4/8|0/8|
|SRAD19P8_N_OFF|2/8|6/8|
|RAW_N129_STAGE|1/8|8/8|
|SRAD19P8_N129_STAGE|0/8|8/8|
|SRAD19P8_N193_STAGE|4/8|8/8|

Interpretation rule:
- Temperature advantage is judged only from the independent hourly validation and is not re-tuned here.
- Yield advantage is supported only if M15TT lowers error under the same shared inputs. H0TT is retained to separate the generic hourly/DTT-path effect from the specific M15 correction.
- N129/N193 cases are robustness/proxy scenarios because exact 2019-2020 fertilizer and initial mineral N were not reported in Guo Chapter 2; they cannot be called the exact historical field input.
- If M15TT does not outperform M0/H0TT in yield, that result must be reported rather than tuned away.
