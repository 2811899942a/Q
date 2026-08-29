# CHECKPOINT 2026-08-29 — Shihezi real-yield V4 -> V5

## Current completed result
- Frozen DSSAT v4.8.5 three-arm real-yield run completed for Shihezi Xinyu66, 2019/2020, W1-W4.
- Arms: M0 official CERES; H0TT official HMET TGRO used in existing CERES extreme-day DTT branch; M15TT frozen M15 high-DTR refinement + H0TT.
- V4 parser audited against raw Summary.OUT rows and HWAM extraction is valid.

### V4 yield metrics
|Arm|Year|RRMSE %|RMSE kg/ha|
|---|---:|---:|---:|
|M0|2019|18.602|2069.2|
|H0TT|2019|17.480|1944.4|
|M15TT|2019|18.598|2068.8|
|M0|2020|60.771|6684.8|
|H0TT|2020|54.414|5985.5|
|M15TT|2020|56.973|6267.0|

2020 screening contrasts:
- H0TT vs M0 relative RRMSE improvement: +10.461%.
- M15TT vs M0 relative RRMSE improvement: +6.250%.
- Local M15 vs H0TT: -4.703%.
- Max arm-induced HWAM shift: 934 kg/ha.
- Published original CERES 2020 yield RRMSE is about 5.69%; reconstructed M0 is 60.771%, so reproduction gate FAILS. No final real-yield accuracy claim is allowed from V4.

## Root cause direction
V4 inputs still contain reconstruction assumptions that are inconsistent with the exact 2019-2020 field experiment. The major remaining mismatch is not the M15 algorithm; the M0 reconstruction itself is wrong.

## Newly recovered exact 2019-2020 experiment facts
Public Shihezi University thesis material for Meng Yu's 2019-2020 experiment (same Xinyu66, same site and W1-W4 framework) gives:
- site: 85°59′47″E, 44°19′28″N; elevation 412 m;
- cultivar: Xinyu66;
- film width 1.45 m;
- drip tape spacing 90 cm;
- maize row spacing 30 cm;
- plant spacing 20 cm;
- theoretical density 82,500 plants/ha = 8.25 plants/m2;
- irrigation totals W1/W2/W3/W4 = 4875/5250/5625/6000 m3/ha;
- 10 irrigation events during the season.

Therefore V4 PPOP=8.89 plants/m2 is incorrect and must be replaced by 8.25. V4 field X/Y coordinates are also reversed in the DSSAT FIELDS line; correct decimal coordinates are longitude 85.996389, latitude 44.324444. The average DSSAT row-spacing representation remains 45 cm for now because the physical layout is a wide/narrow multi-row pattern and changing PLRS to 30 cm without a DSSAT-equivalent-layout derivation would be unjustified.

## V5 plan
Apply only source-supported common-arm corrections:
1. PPOP/PPOE 8.89 -> 8.25 plants/m2.
2. Field XCRD -> 85.996389; YCRD -> 44.324444.
3. Keep elevation 412 m.
4. Keep frozen cultivar coefficients and all M0/H0TT/M15TT source code unchanged.
5. Do not tune M15 against yield.
6. Re-run all 24 cases and test the published-M0 reproduction gate again.
7. Continue searching exact 2019/2020 planting, fertilization, initial soil water and original weather inputs if the gate still fails.

## Scientific decision rule
Only if reconstructed M0 approaches the published 2020 RRMSE (~5.69%, predefined tolerance +/-3 percentage points) may H0TT/M15TT accuracy contrasts be promoted from causal screening to provisional real-yield validation. Otherwise the result remains inconclusive for final accuracy.
