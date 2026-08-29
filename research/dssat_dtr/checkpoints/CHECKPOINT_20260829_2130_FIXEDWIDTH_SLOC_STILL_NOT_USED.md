# CHECKPOINT 2026-08-29 21:30 CST — Fixed-width SLOC edit still not used by model-read OC

## Run
Workflow: `.github/workflows/shihezi-soil-sloc-fixedwidth-v2.yml`
Run ID: `33252091650`
Status: SUCCESS.
Result directory: `research/dssat_dtr/data/shihezi_real_case/soil_sloc_fixedwidth_v2/`.

## Correction tested
Official DSSAT `.SOL` records confirm soil-layer fields are six characters wide and `SLOC` is field 9 (`row[48:54]`). V2 therefore changed only that fixed-width slice and preserved every other character/field exactly.

LOWOM intended SLOC (%C):
`[0.0861, 0.0818, 0.0733, 0.0758, 0.0593]`

HIGHOM intended SLOC (%C):
`[0.8614, 0.8179, 0.7332, 0.7581, 0.5928]`

## Result
Despite correct fixed-width file edits, DSSAT `INFO.OUT` reports identical model-read OC for both runs:
- 0–20 cm: ~1.34%
- 20–40 cm: ~1.35%
- 40–60 cm: ~1.39%
- 60–80 cm: ~1.43%
- 80–100 cm: ~1.25%

Yield is identical:
- LOWOM W2/N129 HWAM = 8339 kg/ha
- HIGHOM W2/N129 HWAM = 8339 kg/ha
- difference = 0 kg/ha.

## Interpretation
The prior free-spacing format bug was real, but it is not the only reason intended SLOC failed to influence the model. Even a correct fixed-width SLOC edit does not change the OC values used/reported by the current frozen DSSAT run.

The model is clearly resolving the custom `SHIH000100` record and description, but its runtime soil-organic-C initialization is either:
1. replacing/estimating OC from another soil-organic-matter initialization path because other required fields are missing/defaulted;
2. using a different soil organic-C field/data structure for SOILDYN/CENTURY than the edited SLOC in this configuration;
3. applying default/derived OC because of missing soil data flagged in `INFO.OUT`.

## Engineering limit / next action
Do not continue trial-and-error edits of OM values.
Perform ONE source/model-read audit to identify where the reported OC=1.34–1.43% is assigned and under what missing-value condition. If it requires reconstructing multiple undocumented carbon pools or non-published soil parameters, close the OM route as unsuitable for this validation case and move to source-confirmed reconstruction items:
- missing plastic mulch representation;
- first of 10 irrigation events omitted;
- planting density cross-check;
- exact CMA weather/initial conditions.

## Current valid findings unchanged
- Temperature method is independently validated at hourly scale (high-DTR RMSE 5.1215 -> 4.6783 C, -8.65%).
- H0TT/M15TT propagate to real-cultivar yield outputs.
- V4 unlimited-N reconstruction is invalid and overpredicts yield strongly.
- Finite N is a major M0 reconstruction factor, but exact 2019–2020 fertilizer remains unavailable.
- Current M0 still does not meet Guo's source-confirmed yield RRMSE <10% gate.

## Additional documented reconstruction gap
`INFO.OUT` says `Simulating flat surface with no plastic mulch`, while the real experiment is explicitly plastic-film mulched drip irrigation. This is now a higher-priority source-confirmed management gap than further OM tuning.

## Rules
No genotype/M15/N/OM target fitting. Every material result/failure/method switch is checkpointed before continuation.
