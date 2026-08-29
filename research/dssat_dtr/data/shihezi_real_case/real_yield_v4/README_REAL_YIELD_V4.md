# Shihezi real-yield three-arm validation V4

**Scope:** Guo Shihezi Xinyu66 real-yield causal screen. 2019 is the published calibration year; 2020 is treated as the independent validation year. Cultivar coefficients are frozen and identical among arms.

**Reconstruction caveat:** weather uses the existing provisional NASA POWER reconstruction because the exact original CMA+NASA WTH is unavailable in the current public package; nitrogen is disabled and initial soil water is set to DUL identically among arms. Observed yield targets are digitized from the published figure (~+/-100 kg/ha). Therefore the published M0 RRMSE reproduction gate is mandatory before any accuracy claim.

|Arm|Year|RMSE kg/ha|RRMSE %|MAE kg/ha|Bias kg/ha|Published M0 RRMSE %|
|---|---:|---:|---:|---:|---:|---:|
|M0|2019|2069.2|18.602|1644.8|1644.8|6.52|
|M0|2020|6684.8|60.771|6603.0|6603.0|5.69|
|H0TT|2019|1944.4|17.480|1484.8|1484.8||
|H0TT|2020|5985.5|54.414|5916.2|5916.2||
|M15TT|2019|2068.8|18.598|1644.5|1644.5||
|M15TT|2020|6267.0|56.973|6179.2|6179.2||

## 2020 independent-validation decision

- M0 reproduction gate: **FAIL** (reconstructed 60.771% vs published 5.69%; tolerance +/-3 percentage points).
- H0TT relative RRMSE improvement vs M0: **+10.461%**.
- M15TT relative RRMSE improvement vs M0: **+6.250%**.
- Local M15 contribution relative to H0TT: **-4.703%**.
- Maximum arm-induced HWAM shift: **934.0 kg/ha**; >=100 kg/ha digitization-resolution threshold: **YES**.

**Scientific classification: INCONCLUSIVE FOR FINAL ACCURACY.** The reconstructed M0 does not reproduce the published independent-year baseline closely enough. Modified-arm directions can be used only as a causal screen, not as evidence of improved real-yield accuracy.
