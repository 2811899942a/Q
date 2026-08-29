# Shihezi real-yield three-arm validation V5

**Scope:** Guo Shihezi Xinyu66 real-yield causal screen. 2019 is the published calibration year; 2020 is treated as the independent validation year. Cultivar coefficients are frozen and identical among arms.

**V5 common-arm corrections: exact 2019-2020 field density is 82,500 plants/ha (8.25 plants/m2) and FIELDS coordinates are longitude 85.9964, latitude 44.3244; elevation remains 412 m. Reconstruction caveat:** weather uses the existing provisional NASA POWER reconstruction because the exact original CMA+NASA WTH is unavailable in the current public package; nitrogen is disabled and initial soil water is set to DUL identically among arms. Observed yield targets are digitized from the published figure (~+/-100 kg/ha). Therefore the published M0 RRMSE reproduction gate is mandatory before any accuracy claim.

|Arm|Year|RMSE kg/ha|RRMSE %|MAE kg/ha|Bias kg/ha|Published M0 RRMSE %|
|---|---:|---:|---:|---:|---:|---:|
|M0|2019|1896.9|17.053|1421.2|1421.2|6.52|
|M0|2020|6483.9|58.945|6399.5|6399.5|5.69|
|H0TT|2019|1782.3|16.022|1313.8|1264.2||
|H0TT|2020|5773.1|52.483|5700.8|5700.8||
|M15TT|2019|1896.9|17.053|1421.2|1421.2||
|M15TT|2020|6075.3|55.230|5984.8|5984.8||

## 2020 independent-validation decision

- M0 reproduction gate: **FAIL** (reconstructed 58.945% vs published 5.69%; tolerance +/-3 percentage points).
- H0TT relative RRMSE improvement vs M0: **+10.962%**.
- M15TT relative RRMSE improvement vs M0: **+6.302%**.
- Local M15 contribution relative to H0TT: **-5.234%**.
- Maximum arm-induced HWAM shift: **941.0 kg/ha**; >=100 kg/ha digitization-resolution threshold: **YES**.

**Scientific classification: INCONCLUSIVE FOR FINAL ACCURACY.** The reconstructed M0 does not reproduce the published independent-year baseline closely enough. Modified-arm directions can be used only as a causal screen, not as evidence of improved real-yield accuracy.
