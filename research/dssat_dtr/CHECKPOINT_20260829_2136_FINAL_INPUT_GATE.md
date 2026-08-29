# DSSAT-DTR checkpoint — 2026-08-29 21:36 CST

## Final shared-input runtime audit

GitHub Actions run `33254955018` completed successfully.

Engineering/runtime gate: **PASS**.

Confirmed:
- `Soil/SH.SOL`, 2019/2020 weather files, `MZCER048.CUL`, and all 8 Shihezi FileX files are byte-identical across M0 / H0TT / M15TT.
- Representative 2019 W2 and 2020 W2 cases execute successfully in all three arms.
- LOWOM soil organic carbon reaches DSSAT runtime (`INFO.OUT` ~0.09/0.08/0.07... % OC).
- Xinyu66 cultivar (`XY0066`) and Shihezi soil (`SHIH000100`) are present in consolidated `DSSAT48.INP`.

Important distinction: this PASS proves the common-input chain is technically identical and model-read correctly. It does **not** prove the reconstructed crop baseline reproduces Guo's published yield accuracy.

2020 W2 representative outputs under this source-pure common configuration:
- observed W2 yield: 11100 kg/ha
- M0 HWAM: 17617 kg/ha (+6517; +58.7%)
- H0TT HWAM: 17009 kg/ha (+5909; +53.2%)
- M15TT HWAM: 17192 kg/ha (+6092; +54.9%)

Therefore the baseline reproduction gate is still not passed. Remaining source/completeness issues are explicitly known:
1. exact 2019–2020 fertilizer/mineral-N inputs are not reported in Guo Chapter 2, so the source-pure runtime audit keeps N stress disabled;
2. initial soil water is a documented common-arm SDUL/field-capacity assumption, not measured initial-profile data;
3. NASA POWER daily weather is traceable and temperature-reasonable but remains a provisional reconstruction of the exact CMA+NASA weather; model SRADA remains ~24.2 MJ m-2 d-1 in 2020, while the thesis reports a growing-season mean total radiation of ~19.8 MJ m-2 d-1.

Decision:
- Do not confuse engineering PASS with scientific baseline PASS.
- Do not yet declare the current source-pure configuration as the final validated crop baseline.
- Continue resolving/validating the remaining common-input discrepancies, especially the radiation construction and N availability, without tuning M15 or cultivar coefficients to yield.
