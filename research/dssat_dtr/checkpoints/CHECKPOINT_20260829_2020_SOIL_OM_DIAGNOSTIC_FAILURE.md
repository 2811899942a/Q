# CHECKPOINT 2026-08-29 20:20 CST — Shihezi M0 soil-OM diagnostic engineering failure

## Purpose

Test a source-interpretation hypothesis for Guo Table 2-1 organic-matter values while keeping M15 and Xinyu66 frozen.

The hypothesis is diagnostic only: Guo reports top-layer organic matter as `1.485` with units typed as g/kg, while a later same-station Xinyu66 experiment reports topsoil organic matter around 14.12 g/kg. The attempted HIGHOM bracket treats `1.485` as 1.485% OM (=14.85 g/kg) and converts OM to DSSAT organic C using OM/1.724.

## Run status

Workflow: `Shihezi M0 Soil OM Diagnostic`
Run: `33251428013`
Conclusion: failure before any HIGHOM crop simulation result was accepted.

## Exact failure

The workflow tried to rebuild the V4 base by extracting a shell block from `.github/workflows/shihezi-m0-nitrogen-diagnostic.yml`.

The generated `/tmp/rebuild_v4.sh` failed with:

```text
/tmp/rebuild_v4.sh: line 18: syntax error near unexpected token `)'
subprocess.CalledProcessError: Command '['bash', '/tmp/rebuild_v4.sh']' returned non-zero exit status 2.
```

The failure occurred during the V4-base reconstruction step. No HIGHOM_N129_SPLIT, HIGHOM_N193_SPLIT, or HIGHOM_N129_BASAL DSSAT runs were completed.

## Scientific consequence

- No soil-organic-matter sensitivity conclusion is available from this run.
- The unit/decimal hypothesis remains unresolved.
- No M0 reproduction improvement is claimed.
- No H0TT/M15TT real-yield accuracy claim is affected.

## Correction

Use the known-good V4 rebuild extraction directly from `.github/workflows/shihezi-real-yield-v4.yml`, the same route already used by the audited weather workflow. Then rerun the same three HIGHOM finite-N brackets without changing any scientific parameter.

The rerun must audit:

1. the active soil file really contains the intended SLOC values;
2. treatment `MF=1` is active for all finite-N cases;
3. DSSAT `NICM` confirms fertilizer application;
4. output is compared against the already validated LOWOM N-diagnostic V2 values;
5. the hypothesis stays labeled diagnostic unless the original 2019–2020 unit is source-resolved.
