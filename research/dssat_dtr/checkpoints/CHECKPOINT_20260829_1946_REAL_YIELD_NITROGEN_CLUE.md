# CHECKPOINT 2026-08-29 19:46 CST — New nitrogen-management clue for Shihezi M0 mismatch

## Material new evidence
A public Shihezi University experiment from the same modern water-saving irrigation station and the same maize cultivar Xinyu66 (2021–2022) reports the following fertilization practice:
- urea: 280 kg/ha, 46% N -> 128.8 kg N/ha
- monoammonium phosphate: 100 kg/ha, 61% P2O5
- potassium sulfate: 60 kg/ha, 52% K2O
- fertilizer applied through the fertigation tank with irrigation
- all plots received the same weed control, irrigation, fertilization and pesticide management.

This is later than the target 2019–2020 Guo/Meng experiment, so it is NOT accepted as the exact formal input. It is only a same-station/same-cultivar management clue.

## Why it matters
V4 reconstructed Shihezi DSSAT cases used NITRO=N because Guo (2025) did not publish an explicit fertilizer schedule in the model-input subsection. In DSSAT this removes nitrogen stress rather than representing a finite fertilizer supply. The resulting 2020 M0 yield is ~17.6 t/ha versus observed roughly 9–12 t/ha, with a strong positive bias.

A finite nitrogen supply of the same order as the later station practice could plausibly create substantial nitrogen stress and reduce simulated yield. Therefore nitrogen handling is now a higher-priority root-cause candidate than it was in the previous checkpoint.

## What remains source-confirmed for 2019–2020
Guo (2025) explicitly confirms:
- cultivar Xinyu66
- sowing dates: 2019-05-03 and 2020-05-05
- 1 mulch / 2 drip lines / 4 rows
- plant spacing 25 cm
- narrow row 30 cm, wide row 60 cm
- sowing depth 4 cm
- mulch width 1.45 m
- four irrigation totals: W1 487.5 mm, W2 525 mm, W3 562.5 mm, W4 600 mm
- 10 irrigation events during the season
- published genetic coefficients P1=104.7, P2=1.824, P5=957.2, G2=671, G3=15.82, PHINT=42.97
- 2020 is an independent validation year.

The thesis does not explicitly state the fertilizer schedule in the visible management subsection.

## Immediate next diagnostic
Do NOT overwrite the formal reconstruction with the 2021–2022 fertilizer schedule. Instead run an M0-only diagnostic matrix to determine whether nitrogen representation is capable of explaining the large positive yield bias:
1. V4 unlimited-N baseline (NITRO=N).
2. NITRO=Y with a finite ~128.8 kg N/ha fertigation scenario derived from the same-station later experiment, clearly labeled DIAGNOSTIC ONLY.
3. If necessary, a small N-rate bracket around this value, with no cultivar or M15 retuning.

If finite nitrogen moves M0 toward the published 2019/2020 yield range, continue searching for the exact 2019–2020 fertilizer schedule in Meng Yu (2021) / Liang et al. (2022) before any formal three-arm claim.

## Scientific rule
The same-station fertilizer values are evidence for root-cause testing only, not publication-grade input for Guo 2019–2020. No final M0/H0TT/M15TT accuracy claim is allowed until the M0 reproduction gate is met with defensible input data.
