# CHECKPOINT 2026-08-29 21:50 CST — Clean M0 SLOC V5 reaches IPSOIL but fails; OM engineering route closed

## Run
Workflow: `.github/workflows/shihezi-soil-sloc-clean-m0-v5.yml`
Standalone script: `research/dssat_dtr/shihezi/clean_sloc_audit_v5.py`
Run ID: `33252659481`
Job ID: `99100915969`
Conclusion: FAILURE.

## What was successfully fixed
This V5 removed all previous nested-wrapper and stale-runtime concerns:
- a completely pristine frozen DSSAT v4.8.5 M0 installation was compiled;
- no `DSSAT48.INP` existed before either LOWOM or HIGHOM was created;
- LOWOM/HIGHOM were generated from pristine pre-DSSAT copies;
- the identical WTH was written both to `Weather/SHIH2001.WTH` and the `Maize/` working directory, so the prior weather-path failure was eliminated.

## Exact new failure
The clean LOWOM run reached the soil-input module and stopped with:

`More than 19 layers in the soil profile. Correct input file.`

`File: SH.SOL   Line: 0   Error key: IPSOIL`

Thus the new standalone custom `SH.SOL` reconstruction is not being parsed as the intended five-layer profile by the frozen DSSAT soil reader.

## Scientific classification
**ENGINEERING SOIL-FILE PARSE FAILURE — NO NEW OM/CROP RESULT.**

No conclusion can be drawn from V5 about LOWOM/HIGHOM, cache reuse, soil organic matter, nitrogen response, or yield accuracy.

## Stop-loss decision
The OM route is now closed for this real-case validation unless the authors' original DSSAT soil file becomes available.

Reasons:
1. Guo's OM unit itself is ambiguous (`1.485` labeled g/kg, while a later same-station measurement is ~14.12 g/kg).
2. Prior V4-derived tests used a model-read OC profile that did not equal the intended edited SLOC.
3. A fresh standalone rebuild now requires additional legacy `.SOL` parser engineering unrelated to the temperature-method research question.
4. The user explicitly prefers abandoning unproductive debugging paths and progressing toward the result.

The OM uncertainty remains documented as a limitation; it is not silently fixed or optimized to yield.

## Higher-priority source-confirmed reconstruction gaps
Work now moves to inputs/processes that are directly supported by both source evidence and model diagnostics:

### A. Plastic mulch is absent
DSSAT `INFO.OUT` from the current real-case run explicitly states:
`Simulating flat surface with no plastic mulch.`

Guo (2025) explicitly describes the field as plastic-film mulched drip irrigation:
- one film / two drip lines / four maize rows;
- film width 1.45 m;
- 30/60 cm narrow/wide rows;
- drip tape spacing 90 cm.

Therefore current M0 is definitively missing a real field-management process.

### B. First of ten irrigations is absent
Guo reports 10 irrigation events and annual totals W1/W2/W3/W4 = 487.5/525/562.5/600 mm.
Current V4 Summary.OUT applies only 9 events because the first irrigation is on the planting date and is skipped by the current simulation timing. For example W1 IRCM becomes 439 mm rather than 487.5 mm.

This is another definite reconstruction mismatch.

## Next actions
1. Recover the official DSSAT v4.8.5 plastic-mulch input syntax/implementation from the frozen source/data and construct a source-based PE mulch treatment without fitting to yield.
2. Correct irrigation timing so all 10 source-reported events are actually applied while preserving the published total and event amounts (e.g. simulation start before the sowing-date irrigation, not by changing irrigation amount).
3. Use a finite-N scenario only as a clearly labeled station-practice reconstruction clue; do not tune N rate to yield.
4. Rebuild M0 and evaluate against Guo's source-confirmed gate: 2020 yield RRMSE <10%, W2-W4 ARE <5%, W1 ARE about 13.19%.
5. Only after M0 is defensible rerun M0/H0TT/M15TT real-yield comparison.

## Rules
- Xinyu66 genetics remain frozen.
- M15 DTRc=14.8 C and alpha=7.8094 remain frozen.
- No yield-targeted N/OM/weather/mulch/irrigation tuning.
- OM is marked unresolved rather than forced.
- Every material result/failure/method switch gets a GitHub checkpoint before continuation.
