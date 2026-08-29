# CHECKPOINT 2026-08-29 19:59 CST — Exact cause of identical finite-N scenarios found

## Root cause
The first nitrogen diagnostic wrote different `*FERTILIZERS` sections and set `NITRO=Y`, but the experiment treatment factor row inherited from V4 still used:

`CU FL SA IC MP MI MF MR MC MT ME MH SM = 1 1 0 1 1 1 0 0 0 0 0 0 1`

The `MF` (fertilizer management factor) remained **0**.

Therefore the fertilizer section was not linked as factor level 1 to the treatment. The nitrogen module itself was enabled, but the intended N64/N129/N193 fertilizer management was not actually selected by the treatment. This explains why all finite-N scenarios produced exactly the same yield despite different generated fertilizer rates.

## Meaning of previous result
- The common ~4.73 t/ha finite-N result is not a valid nitrogen-rate response curve.
- It should be interpreted as nitrogen-module-on / effectively-no-selected-fertilizer severe-stress behavior.
- It cannot be used to assess whether 64, 129 or 193 kg N/ha is appropriate.

## Required correction
For the nitrogen diagnostic only:
- set `MF=1` in the treatment factor row;
- keep all other factor levels unchanged;
- retain `NITRO=Y` and `FERTI=R`;
- verify output-applied N fields differ between N64, N129 and N193;
- save exact generated fertilizer sections and nitrogen summary values for audit.

## Next run
Repeat the same 2020 M0 diagnostic with:
- UNLIMITED baseline from V4;
- N64_SPLIT;
- N129_SPLIT;
- N193_SPLIT;
- N129_BASAL.

No cultivar, M15, weather, irrigation, or target-dependent tuning is allowed.

## Continuity rule
Checkpoint written before rerunning, per user requirement.
