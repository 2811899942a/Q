# Final lower-bound DTRc audit path failure checkpoint

Timestamp: 2026-08-29 CST
Branch: `research/dssat-dtr-matrix`
Failed workflow run: `33258841665`

## Status
The first final lower-bound audit attempt failed for an engineering path mismatch before any valid crop/output matrix was completed. No scientific conclusion about 13.0, 13.5, 13.8, 14.0, or 14.8 C is allowed from this failed run.

## Root cause
The final lower-bound wrapper changed DSSAT runtime roots to `/tmp/run_lb_<ARM>`, while the reused Guo/Shihezi input builder still writes into `/tmp/run_<ARM>`. The input builder therefore could not find `MZCER048.CUL` under the mismatched runtime root and exited with `MZCER048.CUL not found`.

The DSSAT source patches for H0TT and all M15 threshold arms were applied successfully before this failure. This is not evidence for or against any threshold.

## Corrective action
Use the original `/tmp/run_<ARM>` runtime-root convention expected by the already-audited input builder. Do not change:
- candidate thresholds 13.0 / 13.5 / 13.8 / 14.0 / historical 14.8 C;
- temperature-only alpha calibration;
- 2017-2024 independent temperature validation;
- year-by-year stability checks;
- crop observations or common-input scenarios;
- M15 formulation or DSSAT crop parameters.

Re-run automatically after this path-only repair.
