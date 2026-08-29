# Shihezi M0 SRAD x nitrogen source-gap factorial V3

Diagnostic purpose: quantify interaction between the two largest proven common-input gaps without tuning any missing value against yield. SRAD target follows the thesis-scale ~19.8 MJ m-2 d-1 description; N129/N193 are the previously audited finite-N sensitivity brackets.

|Scenario|Year|RRMSE %|Mean HWAM kg/ha|Bias kg/ha|SRADA|Mean NICM|
|---|---:|---:|---:|---:|---:|---:|
|BASE_UNLIMITED|2019|18.602|12768.5|+1644.8|23.30||
|BASE_UNLIMITED|2020|60.771|17603.0|+6603.0|24.20||
|SRAD19P8_UNLIMITED|2019|11.738|10784.0|-339.8|19.90||
|SRAD19P8_UNLIMITED|2020|33.500|14532.5|+3532.5|19.80||
|BASE_N129|2019|24.136|8722.2|-2401.5|23.30|117.0|
|BASE_N129|2020|25.853|8291.5|-2708.5|24.20|117.0|
|BASE_N193|2019|15.976|9798.8|-1325.0|23.30|171.0|
|BASE_N193|2020|18.407|9191.0|-1809.0|24.20|171.0|
|SRAD19P8_N129|2019|21.624|9076.5|-2047.2|19.90|117.0|
|SRAD19P8_N129|2020|18.988|9196.0|-1804.0|19.80|117.0|
|SRAD19P8_N193|2019|18.643|9478.8|-1645.0|19.90|171.0|
|SRAD19P8_N193|2020|14.017|9865.0|-1135.0|19.80|171.0|

## 2020 interaction summary

- SRAD19P8_UNLIMITED: RRMSE change vs BASE_UNLIMITED -27.270 pp; mean HWAM change -3070.5 kg/ha.
- BASE_N129: RRMSE change vs BASE_UNLIMITED -34.917 pp; mean HWAM change -9311.5 kg/ha.
- BASE_N193: RRMSE change vs BASE_UNLIMITED -42.364 pp; mean HWAM change -8412.0 kg/ha.
- SRAD19P8_N129: RRMSE change vs BASE_UNLIMITED -41.783 pp; mean HWAM change -8407.0 kg/ha.
- SRAD19P8_N193: RRMSE change vs BASE_UNLIMITED -46.753 pp; mean HWAM change -7738.0 kg/ha.

Lowest 2020 RRMSE in this fixed diagnostic matrix: **SRAD19P8_N193 = 14.017%**.

This minimum is not a calibrated final model. The matrix is used only to determine whether source recovery of radiation and N availability can plausibly explain the M0 reproduction gap. Exact 2019-2020 fertilizer/initial-N inputs are still required before final three-arm accuracy validation.
