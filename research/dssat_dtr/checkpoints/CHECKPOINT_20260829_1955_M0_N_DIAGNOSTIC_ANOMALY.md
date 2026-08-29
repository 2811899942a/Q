# CHECKPOINT 2026-08-29 19:55 CST — First M0 nitrogen diagnostic completed; finite-N response anomaly

## Run status
Workflow `.github/workflows/shihezi-m0-nitrogen-diagnostic.yml` completed successfully.
GitHub Actions run: `33250767090`.
Result directory: `research/dssat_dtr/data/shihezi_real_case/m0_nitrogen_diagnostic/`.

## Intended diagnostic
2020 Shihezi Xinyu66 M0 only. Cultivar, provisional NASA POWER weather, soil hydraulic profile, irrigation and planting assumptions were kept as in real-yield V4. Nitrogen was varied only for root-cause screening:
- UNLIMITED: V4 `NITRO=N` baseline.
- N64_SPLIT: 64.4 kg N/ha split across 10 dates.
- N129_SPLIT: 128.8 kg N/ha split across 10 dates.
- N193_SPLIT: 193.2 kg N/ha split across 10 dates.
- N129_BASAL: 128.8 kg N/ha one-time application.
Finite-N runs used `NITRO=Y`, urea `FE005`, and organic-C values derived from the published soil organic matter only to enable nitrogen dynamics. These schedules are DIAGNOSTIC, not claimed as the exact 2019–2020 management.

## Raw metric result
- UNLIMITED: mean HWAM 17,603 kg/ha; RRMSE 60.771%; Bias +6,603 kg/ha.
- Every finite-N scenario: mean HWAM 4,730 kg/ha; RRMSE 57.599%; Bias -6,270 kg/ha.

Per-treatment finite-N yield is identical across N rates/modes:
- W1 4,498 kg/ha
- W2 4,668 kg/ha
- W3 4,794 kg/ha
- W4 4,960 kg/ha

## Scientific classification
**THE FIRST FINITE-N DIAGNOSTIC IS ENGINEERING-INCONCLUSIVE.**

It demonstrates that enabling the CERES nitrogen module can radically change yield, so the V4 unlimited-N assumption is potentially important. However, the fact that 64.4, 128.8 and 193.2 kg N/ha and basal vs split applications produce exactly identical yields is not physically credible and means we must verify how the fertilizer section is actually being read before interpreting the result.

## Important audit clue
The stored audit shows nitrogen-module activity in finite-N runs (e.g. NUCM around 98–101 kg/ha and N-loss values present), while unlimited-N has nitrogen summary fields disabled. Thus `NITRO=Y` itself is active.

But the audit did not store the most diagnostic fields `NI#M` and `NICM`, nor the generated fertilizer rows. Therefore we cannot yet tell whether:
1. all fertilizer rates were parsed as the same amount due fixed-column formatting;
2. fertilizer treatment factor numbering/management linkage caused the intended fertilizer rows not to be used;
3. another FileX nitrogen-management setting overrode the specified amounts;
4. extremely low initial mineral N / soil organic C created a common severe-stress ceiling masking rate differences.

## Next action
Before any more scientific root-cause inference, run a minimal FileX fertilizer-read audit using one 2020 treatment:
- save the exact generated `*FERTILIZERS` sections for N64/N129/N193/basal;
- run DSSAT and record `NI#M`, `NICM`, `NUCM`, N stress and yield;
- verify that `NICM`/applied N differs according to the intended total N;
- use official DSSAT fixed-width fertilizer layout (`F` 0:2, `FDATE` 2:8, `FMCD` 8:14, `FACD` 14:20, `FDEP` 20:26, `FAMN` 26:32, etc.).

Only if DSSAT reports distinct applied-N totals may the nitrogen sensitivity result be interpreted.

## Rules unchanged
- Do not retune Xinyu66 cultivar coefficients.
- Do not retune M15/DTRc/alpha against yield.
- Do not claim real-yield accuracy improvement until reconstructed M0 approaches the published independent-year baseline (~5.69% RRMSE).
- After each material result/error/method change, write a GitHub checkpoint before continuing.
