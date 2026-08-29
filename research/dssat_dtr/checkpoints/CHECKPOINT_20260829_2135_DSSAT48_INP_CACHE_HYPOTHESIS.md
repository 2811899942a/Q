# CHECKPOINT 2026-08-29 21:35 CST — DSSAT48.INP cache/preprocessing hypothesis for SLOC non-propagation

## New engineering inference
The LOWOM/HIGHOM SLOC tests were created by copying `/tmp/run_M0` **after** the proven V4 base workflow had already executed DSSAT cases.

That copied runtime directory can already contain a preprocessed `DSSAT48.INP` file generated during the earlier V4 run.

Subsequent LOWOM/HIGHOM runs edited `Soil/SH.SOL` but did not explicitly delete the inherited `DSSAT48.INP` before calling:

`dscsm048 A SHIH2002.MZX`

The audit then found:
- custom `SH.SOL` files differ;
- `DSSAT48.INP` LOWOM vs HIGHOM diff = 0;
- model-read OC is identical and corresponds to the old/default profile (~1.34–1.43%);
- yields/N outputs are identical.

This is consistent with a stale/preprocessed runtime-input reuse pathway.

## Hypothesis
DSSAT may be reusing the inherited `DSSAT48.INP` for soil/preprocessed input rather than rebuilding soil fields from the modified `SH.SOL` on each copied scenario.

This hypothesis is not yet proven, but it is a cleaner explanation than repeated SLOC formatting failure because:
1. fixed-width `.SOL` formatting has already been corrected;
2. the resolved soil ID and description are correct;
3. the consolidated `DSSAT48.INP` remained byte-identical despite different `SH.SOL` files.

## One-shot verification
Repeat only 2020 W2 / N129 split LOWOM and HIGHOM with fixed-width SLOC edits, but before execution explicitly remove any inherited runtime input/cache files, at minimum:
- `DSSAT48.INP`
- previous `.OUT` files

Then run `dscsm048 A SHIH2002.MZX` and verify `INFO.OUT` model-read OC.

Acceptance:
- LOWOM and HIGHOM `INFO.OUT` OC must differ in the intended direction.
- If they differ, the cache hypothesis is confirmed and one valid OM sensitivity comparison can be made.
- If they still do not differ, stop OM engineering and move to source-confirmed mulch/irrigation reconstruction.

## Rules
No genotype/M15/N/OM target fitting. This is the final one-shot OM propagation correction before closing that route.
