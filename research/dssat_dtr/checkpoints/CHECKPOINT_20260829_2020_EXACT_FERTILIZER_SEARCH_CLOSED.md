# CHECKPOINT 2026-08-29 20:20 CST — Exact 2019–2020 fertilizer search temporarily closed

## Search objective
Recover the exact fertilizer material/rate/timing and initial nitrogen management used in the 2019–2020 Shihezi Xinyu66 field experiment that underlies Meng Yu (2021), Liang Yonghui et al. (2022), and Guo Lipeng (2025).

## Sources searched
1. Meng Yu 2021 Shihezi University thesis metadata/full-text index page:
   `降解膜对滴灌玉米土壤水热运动及作物生长影响研究`.
2. Meng Yu et al. 2021 article:
   `降解膜覆盖对滴灌玉米土壤水温变化及其生长的影响`, 西北农业学报 30(2):192–202.
3. Liang Yonghui et al. 2022:
   `基于CERES-Maize模型的新疆滴灌玉米灌溉制度优化`, 灌溉排水学报 41(1):41–48.
4. Targeted searches combining exact titles/names with `施肥`, `尿素`, `施肥量`, `磷酸一铵`, `硫酸钾`, `随水施肥`.
5. Direct Shihezi thesis full-text endpoint was identified but could not be downloaded through the current runtime.

## What is source-confirmed
The Meng thesis metadata confirms this is exactly the target trial lineage:
- 2019–2020
- same Shihezi University modern water-saving irrigation experimental station
- cultivar Xinyu66
- ordinary PE mulch control plus degradable films
- W1/W2/W3/W4 = 4875/5250/5625/6000 m3/ha
- 20 treatments, 3 replicates.

The exact 2019–2020 fertilizer rate/timing is NOT exposed in the accessible indexed text.

## Later same-station/same-cultivar management evidence
A 2021–2022 Shihezi thesis/article from the same research group and same station/cultivar Xinyu66 explicitly reports:
- urea 280 kg/ha, 46% N = 128.8 kg N/ha
- monoammonium phosphate 100 kg/ha, 61% P2O5
- potassium sulfate 60 kg/ha, 52% K2O
- fertilizers applied through the fertigation tank with irrigation
- irrigation/fertilization distribution across stages: 10%, 20%, 35%, 25%, 10%.

This is valuable evidence of station practice but occurs in 2021–2022. It MUST NOT be substituted as the exact formal 2019–2020 fertilizer input.

## Consequence for current M0 reproduction
The corrected nitrogen diagnostic V2 proves nitrogen representation is a major source of V4 overyield, but exact 2019–2020 N input remains unresolved. Therefore nitrogen cannot be tuned against observed yield to force the published 5.69% RRMSE.

## Method switch
The public exact-fertilizer search is temporarily closed after targeted retrieval attempts. Work now moves to other independently recoverable M0 reconstruction variables:
1. exact/closest defensible 2019–2020 weather forcing used by Guo/Liang (CMA station + NASA solar radiation);
2. initial soil water / soil profile state from the original trial;
3. planting-date irrigation handling (current DSSAT misses the first irrigation, so 487.5 mm becomes 439 mm in W1, etc.);
4. exact planting density and geometry cross-check.

If the Meng thesis full PDF later becomes available, reopen fertilizer recovery immediately.

## Scientific rules unchanged
- Xinyu66 genetic coefficients frozen.
- M15 DTRc=14.8 C and alpha=7.8094 frozen.
- No fertilizer or other management parameter may be optimized to the yield target.
- No real-yield accuracy improvement claim until M0 is defensibly reproduced near the published baseline.
- Every material result/error/method switch gets a checkpoint before continuation.
