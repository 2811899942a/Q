# CHECKPOINT 2026-08-29 21:15 CST — SLOC audit shows custom organic-C edits are not propagating into DSSAT

## Run
Workflow: `.github/workflows/shihezi-soil-sloc-read-audit.yml`
Run ID: `33251858968`
Status: SUCCESS.
Result directory: `research/dssat_dtr/data/shihezi_real_case/soil_sloc_read_audit/`.

## Audit design
One 2020 W2 / N129 split M0 case was run twice:
- LOWOM custom soil: top SLOC about 0.0861% C.
- HIGHOM custom soil: top SLOC about 0.8614% C (10x).

The exact generated `SH.SOL` files were saved, DSSAT N output was enabled, and consolidated runtime input/output was preserved.

## Result
The generated custom soil files are genuinely different (`soil_files_different=True`).

However the model run is identical:
- LOWOM HWAM 8339; HIGHOM HWAM 8339 kg/ha.
- LOWOM/HIGHOM NI#M 9, NICM 117, NUCM 151, NLCM 6, NMINC 85.
- Output file sizes are identical across all major water/N/crop outputs.
- `DSSAT48.INP` LOWOM vs HIGHOM unified diff length = **0 characters**.

## Root-cause interpretation
**The prior HIGHOM diagnostic did not actually test the intended SLOC difference at model-read level.**

The custom `SH.SOL` file changes exist on disk but are not propagating into the consolidated/model-read input in this run. Therefore:
- do NOT conclude that organic matter is irrelevant;
- do NOT use the HIGHOM=LOWOM yield equality as a scientific result;
- treat it as an input-propagation engineering issue.

Likely causes to inspect once, in priority order:
1. DSSAT may be resolving soil ID `SHIH000100` from another soil file/database rather than the modified `Soil/SH.SOL`.
2. The custom soil layer rows may have been reformatted with free spacing (`' '.join(tokens)`) while the frozen DSSAT soil reader expects fixed columns, causing SLOC to be ignored/defaulted.
3. SLOC may be copied/derived during experiment preprocessing from a different resolved soil record.

## Engineering decision
One controlled correction only; no extended debugging loop.
- Identify the exact soil file/record resolved by `SHIH000100` in frozen DSSAT v4.8.5.
- Preserve official fixed-width soil row format when changing SLOC; modify only SLOC columns, never rewrite whole rows with whitespace token joins.
- After one LOWOM/HIGHOM W2 N129 test, verify a model-readable output/input differs in soil-C/N state.
- If propagation succeeds, run the OM causal comparison once.
- If propagation cannot be established cleanly, close OM engineering work and move to source-confirmed irrigation/treatment reconstruction.

## Current scientific status
The best *valid* finite-N M0 screen remains nitrogen diagnostic V2:
- N129 split RRMSE 24.890%.
- N193 split RRMSE 16.909%.
- N129 basal RRMSE 24.403%.
These remain outside Guo's source-confirmed yield RRMSE <10% range.

## Yield gate source correction
Formal reproduction gate now follows Guo's explicit text:
- 2020 yield RRMSE <10%;
- W2-W4 yield ARE <5%;
- W1 2020 yield ARE about 13.19%.
The earlier exact 5.69% value is retained only as an unverified figure-derived working reference until visually confirmed.

## Rules unchanged
- Xinyu66 genetics frozen.
- M15 DTRc=14.8 C and alpha=7.8094 frozen.
- No N/OM/weather/management parameter target fitting.
- Every material result/failure/method change is checkpointed before continuation.
