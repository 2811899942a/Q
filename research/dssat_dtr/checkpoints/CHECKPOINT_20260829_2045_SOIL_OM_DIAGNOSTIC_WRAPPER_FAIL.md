# CHECKPOINT 2026-08-29 20:45 CST — Soil-OM diagnostic workflow failed before DSSAT experiment

## Material event
Workflow `.github/workflows/shihezi-m0-soil-om-diagnostic.yml` was triggered from commit `e0340ffd98cf49396998ad96b794489c9f284d78`.
GitHub Actions run: `33251428013`.
Job: `99097662040`.
Conclusion: FAILURE.

## Exact failure
The workflow tried to reconstruct the already-proven V4 base by extracting the `Rebuild the identical V4 case` shell block from `.github/workflows/shihezi-m0-nitrogen-diagnostic.yml` and executing that extracted block again.

That first-level block itself creates another `/tmp/rebuild_v4.sh` by extracting V4 workflow steps. The resulting second-level nested extraction corrupted shell/Python quoting and failed with:

`/tmp/rebuild_v4.sh: line 18: syntax error near unexpected token ')'`

followed by Python `subprocess.CalledProcessError`.

## Scientific classification
**ENGINEERING WRAPPER FAILURE — NO SCIENTIFIC RESULT.**

DSSAT never reached the new HIGHOM crop simulations. Therefore:
- the soil-organic-matter unit hypothesis remains unresolved;
- no HIGHOM yield/RRMSE result exists from this run;
- the failure must not be interpreted as evidence against the hypothesis.

## Hypothesis still under test
Guo (2025) Table 2-1 reports OM numeric values `1.485, 1.410, 1.264, 1.307, 1.022` while labeling them g/kg. A later same-station, same-cultivar Xinyu66 experiment reports topsoil OM around 14.12 g/kg. This supports testing whether the Guo values may actually be percent OM (e.g. 1.485% = 14.85 g/kg).

If interpreted as percent OM, the five DSSAT organic-C values are approximately:
- 0–20 cm: SLOC 0.8614%
- 20–40 cm: 0.8179%
- 40–60 cm: 0.7332%
- 60–80 cm: 0.7581%
- 80–100 cm: 0.5928%

These are about 10x the literal-g/kg interpretation used in nitrogen diagnostic V2.

## Engineering decision
Do not debug the nested workflow-extraction approach further.
Restart this diagnostic with a clean, direct **M0-only** workflow:
1. clone frozen DSSAT v4.8.5 source/data;
2. compile/install only M0;
3. build the Guo 2020 Xinyu66 inputs directly using the already-proven fixed-column formats;
4. set HIGHOM soil profile directly;
5. set MF=1, NITRO=Y, FERTI=R;
6. run the same independently motivated diagnostic N scenarios used previously (N129 split, N193 split, N129 basal);
7. record HWAM, CWAM, NI#M, NICM, NUCM, NLCM and calculate RRMSE;
8. compare directly with validated LOWOM V2 values: 24.890%, 16.909%, 24.403%.

No double extraction or wrapper-inside-wrapper is permitted.

## Scientific rules unchanged
- Xinyu66 coefficients remain frozen: P1 104.7, P2 1.824, P5 957.2, G2 671, G3 15.82, PHINT 42.97.
- M15 remains frozen at DTRc=14.8 C and alpha=7.8094.
- No N/OM parameter may be optimized against yield.
- No real-yield accuracy claim until a defensible M0 approaches the published 2020 baseline (~5.69% RRMSE).
- Every material result, failure, method switch or major decision must be checkpointed before continuing.
