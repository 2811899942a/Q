# CHECKPOINT 2026-08-29 21:45 CST — Clean M0-only SLOC audit stopped by weather-file path resolution

## Run
Workflow: `.github/workflows/shihezi-soil-sloc-clean-m0-v4.yml`
Commit: `03fca76792289e470be60d94db780809de942a1b`
Run ID: `33252520327`
Job ID: `99100546212`
Conclusion: FAILURE.

## What succeeded
The redesigned workflow eliminated nested-wrapper/extraction problems and successfully:
- cloned frozen DSSAT source commit `0b91373806786b600d89ccfcfff78fa2f82cb26b`;
- cloned frozen DSSAT data commit `79cb5db71bbca186add92a6a9695866a09c8b51d`;
- compiled/installed a clean M0-only DSSAT v4.8.5 environment;
- verified the pristine installation had no inherited `DSSAT48.INP` before the experiment;
- constructed the clean LOWOM case up to DSSAT execution.

## Exact failure
LOWOM stopped before soil/N/crop calculations with:

`Weather file not found. Please check file name or create file.`

`File: SHIH2001.WTH   Line: 0   Error key: MAKEFW`

The workflow had written `SHIH2001.WTH` under the installed root `Weather/` directory. In this clean standalone M0 execution, DSSAT reported an empty `DATA PATH` and did not resolve that weather path as the prior V4 runtime did.

## Scientific classification
**ENGINEERING FILE-PATH FAILURE — NO SLOC/CROP RESULT.**

This run provides no evidence for or against:
- stale `DSSAT48.INP` reuse;
- LOWOM/HIGHOM propagation;
- soil organic-matter sensitivity;
- yield accuracy.

## One-line correction
Do not alter any science/input values.
Write the identical `SHIH2001.WTH` file to the installed `Weather/` directory and also copy it into the experiment working directory `Maize/` before calling `dscsm048 A SHIH2002.MZX`.

This is a path-resolution correction only. All of the following remain identical:
- Xinyu66 genetics;
- LOWOM/HIGHOM SLOC values;
- N129 diagnostic;
- W2 irrigation;
- POWER forcing values;
- initial conditions;
- model version.

## Next acceptance test
After the path correction, the clean LOWOM run must reach `INFO.OUT`. Then HIGHOM is run from another pristine pre-DSSAT copy. The only scientific decision remains whether model-read OC differs between LOWOM and HIGHOM.

## Rules
- No genotype/M15/N/OM target fitting.
- No science conclusion from this failed run.
- Every material result/failure/method switch is checkpointed before continuation.
