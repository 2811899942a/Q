# Dual-track regional HTEMP / crop-response pilot

Engineering computation completed. These results are exploratory; scientific promotion requires separate gates.

## Temperature-only selection
{"model": "REG_SEASONAL_Q0", "seasonal": true, "q": 0.0, "beta": 1.1085040032550604, "CV_RMSE_C": 1.89102219543389, "CV_n": 2564}

|Model|Legacy May-Sep RMSE C|High-DTR RMSE C|
|---|---:|---:|
|HTEMP_ORIGINAL|2.946890|5.140931|
|M15_13P5|2.796224|4.651516|
|M15_13P8|2.801549|4.652874|
|REG_SEASONAL_Q0|2.771266|4.671719|

## Paired year-block 95% intervals; negative favors regional candidate
|Comparator|Group|Delta RMSE C|95% low|95% high|Years|
|---|---|---:|---:|---:|---:|
|M15_13P5|MaySep|-0.024957|-0.037872|-0.014101|6|
|M15_13P8|MaySep|-0.030282|-0.045993|-0.017092|6|
|M15_13P5|DTR_GE15|0.020203|0.007631|0.036574|5|
|M15_13P8|DTR_GE15|0.018845|0.006318|0.031422|5|

## Crop diagnostic: RAW_N_OFF
|Arm|2019 RMSE|2020 RMSE|ALL8 RMSE|ALL8 RRMSE %|
|---|---:|---:|---:|---:|
|M0|2070.048|6700.169|4958.698|44.827|
|H0TT|1945.307|5995.560|4457.070|40.292|
|M15_13P5|2070.419|6699.925|4958.610|44.826|
|M15_13P8|2070.048|6697.517|4956.906|44.811|
|M15_13P8_HR|1381.061|6190.820|4485.175|40.546|
|REGIONAL|2070.048|6693.168|4953.968|44.784|
|REGIONAL_HR|1374.549|6097.898|4420.053|39.958|
|M15_HR_K0.25|1863.850|6603.377|4851.728|43.860|
|REG_HR_K0.25|1860.898|6597.592|4847.224|43.819|
|M15_HR_K0.5|1675.261|6509.495|4752.895|42.966|
|REG_HR_K0.5|1669.985|6466.316|4722.399|42.691|
|M15_HR_K0.75|1511.398|6369.856|4629.222|41.848|
|REG_HR_K0.75|1504.883|6361.499|4622.410|41.787|

## Crop diagnostic: SRAD19P8_N_OFF
|Arm|2019 RMSE|2020 RMSE|ALL8 RMSE|ALL8 RRMSE %|
|---|---:|---:|---:|---:|
|M0|1305.717|3691.516|2768.771|25.030|
|H0TT|1280.267|4011.136|2977.272|26.915|
|M15_13P5|1276.940|3778.851|2820.487|25.497|
|M15_13P8|1277.099|3532.678|2656.200|24.012|
|M15_13P8_HR|1659.918|2835.538|2323.317|21.003|
|REGIONAL|1263.519|3709.380|2770.919|25.049|
|REGIONAL_HR|1635.454|2906.461|2358.201|21.318|
|M15_HR_K0.25|1329.731|3445.891|2611.738|23.610|
|REG_HR_K0.25|1301.646|3619.314|2719.716|24.586|
|M15_HR_K0.5|1414.677|3338.788|2564.061|23.179|
|REG_HR_K0.5|1380.636|3463.400|2636.408|23.833|
|M15_HR_K0.75|1526.551|2934.458|2338.953|21.144|
|REG_HR_K0.75|1494.615|3302.382|2563.162|23.171|

## Previous joint-screen leave-one-year-out reanalysis
|Scope|Held-out pooled RMSE|Frozen M15 pooled RMSE|
|---|---:|---:|
|prft|2759.995|2656.200|
|rgfill|2711.172|2656.200|
|both|2890.142|2656.200|
|all_modes|2890.142|2656.200|

## Interpretation boundaries
- Regional model parameters/structure use dense-station temperature calibration CV only; crop observations do not select them.
- The primary 2017-2024 benchmark has been repeatedly inspected previously. It is a legacy benchmark; fresh independent final validation remains required.
- Shihezi crop inputs reconstruct a published experiment. RAW and SRAD19P8 scenarios both disable nitrogen. Report each scenario, not a selected favorable scenario.
- ADAT/MDAT/CWAM are simulated outputs. No observed phenology or biomass is invented; those accuracy gains are not asserted.
- A global standardized hinge can be an affine reparameterization of a fixed-degree hinge; this pilot distinguishes seasonal profiles and a bounded nonlinear anchor response.
- All candidate results are retained. An engineering COMPLETE is not a scientific PASS.
