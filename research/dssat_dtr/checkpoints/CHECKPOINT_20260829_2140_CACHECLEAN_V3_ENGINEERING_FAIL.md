# CHECKPOINT 2026-08-29 21:40 CST — Cache-clean SLOC V3 engineering failure

## Material event
Workflow: `.github/workflows/shihezi-soil-sloc-cacheclean-v3.yml`
Run ID: `33252302371`
Job ID: `99099974582`
Conclusion: FAILURE.

## What succeeded
The workflow checkout and the proven V4 base reconstruction completed successfully. Frozen DSSAT v4.8.5 source/data were built, the Xinyu66 cultivar row was generated correctly, and the existing V4 real-case base cases were recreated.

## Exact failure
The new cache-clean LOWOM/HIGHOM audit never reached DSSAT execution.

The workflow extracted the Python-containing shell block from `shihezi-soil-sloc-fixedwidth-v2.yml`, injected recursive deletion of inherited `DSSAT48.INP`, then executed the resulting temporary script. The generated Python had incorrect indentation:

`IndentationError: unexpected indent`

at the injected line:

`for cache in list(r.rglob('DSSAT48.INP')):`

The outer wrapper then raised:

`subprocess.CalledProcessError: Command ['bash', '/tmp/cacheclean_sloc_v3.sh'] returned non-zero exit status 1.`

## Scientific classification
**ENGINEERING WRAPPER FAILURE — NO NEW SOIL/CROP RESULT.**

Therefore this run provides no evidence for or against:
- the DSSAT48.INP stale-cache hypothesis;
- LOWOM versus HIGHOM SLOC propagation;
- organic-matter sensitivity;
- real-yield accuracy.

The previous scientific state remains unchanged.

## Engineering decision
Per the result-oriented workflow rule, do NOT debug this nested/extracted script further.

Abandon the V3 wrapper design and create a clean minimal workflow containing the audit code directly:
1. rebuild only the required frozen M0 environment / proven Guo input;
2. create only 2020 W2 / N129 split LOWOM and HIGHOM cases;
3. delete every inherited `DSSAT48.INP` before DSSAT execution;
4. modify SLOC only through official fixed-width slice `[48:54]`;
5. run `dscsm048 A SHIH2002.MZX`;
6. parse `INFO.OUT` model-read OC and Summary.OUT HWAM/N fields;
7. preserve inputs and outputs for audit.

No nested workflow extraction for the audit logic is permitted.

## Acceptance
- If model-read OC differs between LOWOM and HIGHOM in the intended direction, cache/preprocessing reuse is confirmed and one valid OM sensitivity result can be interpreted.
- If model-read OC remains identical after cache deletion, close the OM route rather than continuing trial-and-error debugging and switch to source-confirmed real-case gaps: plastic mulch and the missing first irrigation event.

## Scientific rules unchanged
- Xinyu66 coefficients frozen.
- M15 DTRc=14.8 C and alpha=7.8094 frozen.
- No yield-targeted N/OM/weather/management tuning.
- Formal real-yield validation requires defensible M0 performance compatible with Guo (2025): yield RRMSE <10%, W2-W4 ARE <5%, W1 2020 ARE about 13.19%.
- Every material result/failure/method switch gets a GitHub checkpoint before continuation.
