# CHECKPOINT 2026-08-29 20:33 CST — Canonical SLOC V4 model-read gate PASS

## Run

Workflow: `Shihezi Soil SLOC Canonical V4`
Run: `33252514758`
Status: PASS.

## Purpose

Resolve whether the Guo soil organic-matter interpretation can materially alter the finite-N Shihezi crop simulation once the custom `.SOL` file is actually read by DSSAT.

The run uses:
- canonical `/tmp/run_M0` runtime root;
- canonical soil edited in place;
- fixed-column DSSAT soil formatting;
- 2020 W2;
- the existing N129 diagnostic bracket;
- identical weather, irrigation, planting, genotype and all other inputs.

## Model-read audit

The hard gate passed.

LOWOM intended SLOC (% C):
`[0.0861, 0.0818, 0.0733, 0.0758, 0.0593]`

INFO.OUT model-read OC (%):
`[0.09, 0.09, 0.09, 0.08, 0.08, 0.07, 0.07, 0.08, 0.08, 0.06]`

HIGHOM intended SLOC (% C):
`[0.8614, 0.8179, 0.7332, 0.7581, 0.5928]`

INFO.OUT model-read OC (%):
`[0.86, 0.86, 0.86, 0.82, 0.82, 0.73, 0.73, 0.76, 0.76, 0.59]`

The duplicated model-read values reflect DSSAT's internal subdivision of the five 20-cm source layers; their magnitudes track the intended LOWOM/HIGHOM inputs.

## Crop/N response

2020 W2, N129:

| Metric | LOWOM | HIGHOM | Change |
|---|---:|---:|---:|
| HWAM kg/ha | 4659 | 6829 | +2170 |
| NI#M | 9 | 9 | 0 |
| NICM kg N/ha | 117 | 117 | 0 |
| NUCM kg N/ha | 94 | 123 | +29 |
| NLCM kg N/ha | 7 | 6 | -1 |
| NMINC kg N/ha | 5 | 49 | +44 |

## Interpretation

Soil organic carbon is a material source-gap lever under finite-N conditions once it enters the DSSAT runtime correctly. The former exact LOWOM/HIGHOM equality was caused by runtime-path/fixed-column input errors.

The HIGHOM interpretation remains conditional. Guo Table 2-1 prints values such as `1.485 g/kg`, while an independent later same-station Xinyu66 measurement is around 14.12 g/kg. HIGHOM tests the plausible interpretation that the original numeric values are percent organic matter, i.e. `1.485% = 14.85 g/kg`, then converts OM to organic C using OM/1.724.

Yield improvement alone cannot be used to choose HIGHOM as the formal 2019-2020 input.

## Next action

1. Run W1-W4 and both years with correctly read LOWOM/HIGHOM to quantify RRMSE impact.
2. Combine corrected soil OC with the source-scale SRAD and audited finite-N brackets in a diagnostic matrix.
3. Continue recovering the exact 2019-2020 soil OM unit / fertilizer total / initial mineral-N state before final M0/H0TT/M15TT validation.
