# CHECKPOINT 2026-08-29 20:05 CST — Corrected M0 nitrogen diagnostic V2 is valid

## Run
Workflow: `.github/workflows/shihezi-m0-nitrogen-diagnostic-v2.yml`
Run ID: `33250955690`
Status: SUCCESS.
Result directory: `research/dssat_dtr/data/shihezi_real_case/m0_nitrogen_diagnostic_v2/`

## Critical correction
V2 sets treatment fertilizer factor `MF=1`, so the generated `*FERTILIZERS` section is actually linked to the treatment. The nitrogen output now responds distinctly to N rate, confirming the first diagnostic's identical-result issue was an MF linkage bug.

## 2020 M0 results
|Scenario|RRMSE %|Mean HWAM kg/ha|Bias kg/ha|
|---|---:|---:|---:|
|UNLIMITED (`NITRO=N`)|60.771|17,603|+6,603|
|N64_SPLIT|34.709|7,290.8|-3,709.2|
|N129_SPLIT|24.890|8,399.8|-2,600.2|
|N193_SPLIT|16.909|9,401.8|-1,598.2|
|N129_BASAL|24.403|8,486.8|-2,513.2|

Best tested finite-N diagnostic: N193_SPLIT, RRMSE 16.909%, a 72.17% relative reduction from the invalid unlimited-N V4 baseline, but still well above the published original-model 5.69% RRMSE.

## Applied-N audit
DSSAT Summary.OUT confirms distinct fertilizer amounts were used:
- N64_SPLIT: NI#M=9, NICM=54 kg N/ha (first intended split event omitted by simulation timing).
- N129_SPLIT: NI#M=9, NICM=117 kg N/ha.
- N193_SPLIT: NI#M=9, NICM=171 kg N/ha.
- N129_BASAL: NI#M=1, NICM=129 kg N/ha.

The split schedules lose the first application for the same timing reason that the first planting-date irrigation is omitted. Basal application one day after planting is fully counted.

## Scientific interpretation
1. The V4 decision to use `NITRO=N` is a major cause of systematic yield overestimation. Unlimited-N is not an acceptable reconstruction of the published real case.
2. Finite nitrogen is capable of moving M0 strongly toward observed yield, so the original experiment's exact fertilizer management is now a high-priority missing input.
3. The response is physically ordered after MF correction: more applied N -> more crop N uptake -> higher yield.
4. N193_SPLIT still does not reproduce the published model accuracy, so nitrogen alone at the tested rates is insufficient.
5. No temperature-method accuracy conclusion is allowed yet.

## Important methodological warning
The tested N schedules are root-cause diagnostics only. They are not the exact 2019–2020 Guo/Meng fertilizer schedule and must not be selected based on which N rate best fits yield. Do not optimize N to force M0 to the target.

## Next priority
Search the upstream 2019–2020 trial literature (Meng Yu 2021 thesis/article, Liang et al. 2022, related Wang Zhenhua group papers) for the exact fertilizer material/rate/timing and initial soil N. If exact values are found, rebuild M0 with those values. In parallel, verify exact field plant density and weather forcing. Only after defensible M0 reproduction should M0/H0TT/M15TT be rerun for real-yield accuracy.

## Rules unchanged
- Xinyu66 cultivar coefficients remain frozen.
- M15 DTRc=14.8 C and alpha=7.8094 remain frozen.
- No yield-targeted parameter tuning.
- Every material result/error/method change gets a GitHub checkpoint before further computation.
