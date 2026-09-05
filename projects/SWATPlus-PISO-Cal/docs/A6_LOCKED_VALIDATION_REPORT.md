# A6 locked temporal validation

`A6_GATE=PASS`; `VALIDATION_PASS=PASS`; `TEMPORAL_GENERALIZATION=SUPPORTED`.

This report evaluates the parameters produced by the frozen A5 development experiment on the locked 2017-2020 validation period. Validation metrics were not sent back to DDS and did not affect any theta selection or method decision.

## Freeze and data boundary

A6 was executed from baseline commit `f0fe3a3` (`f0fe3a3ec86b98a688a958487a614c6513bf5da1`). The frozen methods are DDS_GLOBAL and DDS_SOFT_AI with sigma `0.2`, formal dimension 14, the frozen A2 region, the original seeds, and the original development objective. Warm-up is 2000-2002; validation is 2017-2020.

The validation reader loaded exactly 2017-01-01 through 2020-12-31 for each gauge and stopped after the last validation row. No 2021-2024 final-test values were loaded.

## Theta selection and deduplication

At each of the six frozen development budgets `25, 50, 100, 150, 200, 250`, the theta with the highest development mean NSE was selected independently for each method and seed. This produced `120` logical selections and `116` unique theta values; duplicate theta values were run once and their budget mappings were restored in `validation_results.csv`.

The CSV therefore has one row per logical method-seed-budget mapping. Repeated `unique_theta_id`, `validation_run_id`, and qsim path values identify deduplicated validation executions.

## Validation mean NSE by development budget

Values are ten-seed summaries of validation mean NSE. Paired delta is SOFT_AI minus GLOBAL; wins count positive/negative/tied paired seed deltas.

| budget | GLOBAL mean | GLOBAL median | GLOBAL std | SOFT_AI mean | SOFT_AI median | SOFT_AI std | paired delta | paired 95% CI | SOFT wins | GLOBAL wins | ties |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 25 | 0.330728 | 0.356025 | 0.072791 | 0.348734 | 0.343052 | 0.040362 | 0.018006 | [-0.015167, 0.060534] | 5 | 5 | 0 |
| 50 | 0.371431 | 0.366992 | 0.027361 | 0.373051 | 0.372666 | 0.012696 | 0.001620 | [-0.011395, 0.014428] | 5 | 5 | 0 |
| 100 | 0.386787 | 0.367706 | 0.046671 | 0.383319 | 0.386908 | 0.019776 | -0.003468 | [-0.028736, 0.017210] | 7 | 3 | 0 |
| 150 | 0.392673 | 0.387905 | 0.037012 | 0.393803 | 0.397393 | 0.014349 | 0.001129 | [-0.020503, 0.019001] | 8 | 2 | 0 |
| 200 | 0.398227 | 0.388051 | 0.037560 | 0.396134 | 0.394845 | 0.018062 | -0.002094 | [-0.022129, 0.014012] | 7 | 3 | 0 |
| 250 | 0.403385 | 0.390842 | 0.035169 | 0.395381 | 0.393953 | 0.019863 | -0.008003 | [-0.031332, 0.011223] | 6 | 4 | 0 |

## Validation anytime AUC

AUC uses only the six frozen nodes 25, 50, 100, 150, 200, and 250 evaluations. It is the trapezoidal area over development-evaluation x divided by 225 (250-25), so the normalized value is on the mean-NSE scale. Bootstrap intervals use 20,000 paired resamples of the ten seeds.

| arm | AUC mean | AUC median | AUC std |
|---|---:|---:|---:|
| DDS_GLOBAL | 0.386808 | 0.377744 | 0.032273 |
| DDS_SOFT_AI | 0.386204 | 0.385140 | 0.015376 |

Paired validation AUC delta = `-0.000604`; 95% CI = `[-0.016942, 0.012834]`.

## Final 250-budget validation comparison

GLOBAL validation mean NSE = `0.403385`; median = `0.390842`.
SOFT_AI validation mean NSE = `0.395381`; median = `0.393953`.
Paired final delta = `-0.008003`; 95% CI = `[-0.030506, 0.011873]`.

| method | seed | development candidate | validation mean NSE | validation min NSE | 01605500 NSE | 01606000 NSE | 01606500 NSE |
|---|---:|---|---:|---:|---:|---:|---:|
| DDS_GLOBAL | 20260909 | DDS_GLOBAL_20260909-0248 | 0.462931 | 0.349503 | 0.349503 | 0.509433 | 0.529858 |
| DDS_SOFT_AI | 20260909 | DDS_SOFT_AI_20260909-0248 | 0.429747 | 0.278945 | 0.278945 | 0.488745 | 0.521552 |

The highest validation mean-NSE candidate at the 250-budget node is `DDS_GLOBAL` (seed `20260909`), with mean NSE `0.462931` and station NSE `{"01605500":0.3495025691906144,"01606000":0.5094326754449581,"01606500":0.5298579953711231}`.

## Pre-frozen validation decision

`VALIDATION_PASS` requires all three conditions: validation anytime AUC is not stably degraded, the low-budget paired results do not show a systematic reversal at 25/50/100, and the 250-budget final comparison is not stably degraded. Operationally, stable degradation means a paired bootstrap 95% interval wholly below zero; a point estimate below zero with a CI crossing zero is treated as equivalent/inconclusive. These rules were fixed in the A6 runner before validation execution.

Decision: `VALIDATION_PASS=PASS`; `TEMPORAL_GENERALIZATION=SUPPORTED`.

## Leakage audit

| audit item | result |
|---|---|
| VALIDATION_USED_FOR_OPTIMIZATION | NO |
| VALIDATION_USED_FOR_THETA_SELECTION | NO |
| VALIDATION_USED_FOR_METHOD_TUNING | NO |
| FINAL_TEST_READ | NO |

## Artifacts

- `validation_results.csv`: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a6\validation_results.csv`
- `A6_GATE.json`: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a6\A6_GATE.json`
- local validation qsim/runtime: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a6\qsim` / `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a6\runtime`

No A5 algorithm, parameter range, A2 region, objective, seed logic, or final-test data boundary was changed by A6.
