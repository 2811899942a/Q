---
name: swat-paper-reproducer
description: Specialized workflow guidance for reproducing SWAT, ArcSWAT, and SWAT-CUP 2012 papers. Use when the user wants to reproduce a SWAT hydrological modeling paper, build or troubleshoot an ArcSWAT 2012 project, prepare inputs, extract output.rch, calibrate with SWAT-CUP SUFI-2, validate, or run large calibration batches with external multi-core ParallelSWAT-style orchestration when the official parallel module is unavailable or trial-limited. Includes real-execution parameter-dictionary checks for new SWAT-CUP parameter lists. Not intended for QSWAT, SWAT+, or non-SWAT hydrological models.
---

# SWAT Paper Reproducer

Use this skill to run a structured reproduction workflow for **SWAT / ArcSWAT / SWAT-CUP 2012** papers. Assume the user wants the shortest reliable path: automate data preparation, parsing, plotting, and text-file edits with code/Codex; reserve manual work for ArcSWAT and SWAT-CUP GUI clicks.

## Operating Rules

- Focus only on SWAT 2012, ArcSWAT, and SWAT-CUP 2012. If the task concerns QSWAT, QSWAT+, SWAT+, or SWAT+ Editor, state that this skill is not the right template.
- Start every project by extracting paper-specific settings: study area, outlet/gauge, area, DEM, land use, soil, weather, streamflow, warm-up, calibration, validation, output frequency, objective functions, reported metrics, and calibrated parameters.
- Prefer code/Codex instructions for data download, ArcPy preprocessing, raster/vector cleanup, SWAT text-file editing, output parsing, metric calculation, and plotting.
- Give manual GUI instructions only for ArcSWAT and SWAT-CUP operations that are not safely automatable. Tell the user exactly which menu/button/field to click.
- Treat a first complete SWAT run as a workflow test, not a valid reproduction, until observed streamflow is aligned and metrics are computed.
- Preserve only necessary baselines before overwriting `TxtInOut`, `SUFI2.OUT`, or SWAT-CUP iteration output. Respect explicit user limits on disk usage; do not create redundant backups, ZIPs, or duplicate project trees.
- Never assume the outlet reach. Identify it from `output.rch` by largest `AREAkm2` unless the paper or user provides a verified reach.
- For SWAT-CUP, verify the **actual GUI project** files `observed_rch.txt`, `SUFI2_extract_rch.def`, `par_inf.txt`, `SUFI2_swEdit.def`, and `swat.exe` before calibration. Do not assume a staging folder is the one read by the GUI.
- Never declare a SWAT-CUP parameter list compatible based only on static text inspection. Parameter support is determined by the local `Swat_Edit` dictionary at runtime.
- Before any 100/500/1000-run calibration, execute a **one-simulation end-to-end smoke test** with the full candidate parameter list in the actual GUI project. Require successful parameter editing, SWAT execution, output extraction, and objective-function calculation.
- If the smoke-test log contains `not present in the dictionary`, stop. Do not retry the large run. Remove or correct only the exact unsupported parameter, then rerun the one-simulation smoke test.
- Treat `SOL_AWC` and `SOL_K` as version-dependent and **exclude them from the default first-pass parameter set**. Add soil-layer parameters only after their exact local syntax passes a real one-simulation smoke test.
- A one-simulation post-processing singular-matrix/range-update warning may be expected because one sample cannot support parameter-range statistics. It is acceptable only when parameter editing, SWAT execution, output extraction, and objective calculation all succeed.
- When the official SWAT-CUP Parallel Processing Module is unavailable or trial-limited, do not treat serial execution as the only option. Use an external ParallelSWAT-style runner that keeps SUFI-2 sampling/post-processing in SWAT-CUP but executes ordinary SWAT runs concurrently in isolated worker folders. Never patch or bypass license checks. See `references/parallelswat.md`.
- For the original HydroRS/ParallelSWAT MATLAB implementation, choose a worker count that divides the simulation count exactly; for example, 1000 simulations / 8 workers = 125 simulations per worker. Preserve exact sample-index ordering when merging results.

## Workflow Decision Tree

1. **User provides a paper or asks to reproduce a SWAT paper**: read `references/workflow.md` and produce a reproducibility extraction table plus project plan.
2. **User is preparing ArcSWAT inputs**: use `references/arcswat_troubleshooting.md` and generate Codex/ArcPy tasks for DEM, land use, soil, weather, and streamflow.
3. **User has `output.rch` or model results**: use `scripts/extract_output_rch.py` and `scripts/calculate_metrics.py` to extract outlet flow and compute R2, NSE, PBIAS, KGE, RMSE, MAE.
4. **User is preparing SWAT-CUP**: read `references/swatcup_calibration.md`; generate observed files with `scripts/prepare_observed_flow.py`; configure the actual GUI project; run the mandatory one-simulation dictionary smoke test; then start the formal iteration only after the smoke test passes.
   - If the calibration batch is large or the official parallel module is license-limited, also read `references/parallelswat.md`. Prefer external worker-folder orchestration over the official trial module: `SUFI2_Pre` once, parallel SWAT runs, merge `SUFI2.OUT`, then `SUFI2_Post` once.
5. **User has calibrated parameters and wants validation**: use `scripts/write_best_params_to_txtinout.py`, rerun SWAT, then compute calibration-period and validation-period metrics.
6. **User asks for a report or standard summary**: use `references/metrics_and_reporting.md`.

## Standard Project Layout

Recommend this layout for every paper reproduction:

```text
<root>/
  00_paper/
  01_boundary/
  02_dem/
  03_landuse/
  04_soil/
  05_weather/
  06_streamflow/
  07_arcswat_project/
  08_swatcup/
  09_results/
  10_notes/
  11_scripts/
  12_gee_export/
```

Use short paths for SWAT-CUP when possible, for example `D:\SWATCUP_<PROJECT>`, because SWAT-CUP 2012 is fragile with long paths.

## Minimum Viable Reproduction Stages

Push through these milestones in order:

1. **Paper extraction**: method table, periods, data sources, metrics, target values.
2. **Observed streamflow**: daily download, unit conversion, monthly aggregation, missing-date check.
3. **ArcSWAT inputs**: DEM, land use lookup, soil database, weather files.
4. **Watershed delineation**: basin area check against paper; outlet/reach verification.
5. **HRU generation**: landuse/soil/slope overlay; HRU count and report.
6. **Initial SWAT run**: real-weather run and output audit.
7. **Output extraction**: outlet `output.rch`, simulated flow, observed alignment.
8. **Uncalibrated metrics**: R2, NSE, PBIAS, KGE, RMSE, MAE.
9. **SWAT-CUP project preflight**: actual GUI paths, control files, observation count, executable, parameter syntax.
10. **One-simulation smoke test**: full candidate parameter list, real `Swat_Edit`, real SWAT execution, real post-processing.
11. **Formal SUFI-2 calibration**: broad search, diagnose, narrow ranges, rerun as justified.
12. **Validation**: write best parameters into a clean validation run and evaluate the validation period.
13. **Report**: compare calibration/validation metrics with the paper and list deviations.

## Reusable Scripts

Use bundled scripts when local files are available. Adapt file paths and column names as needed.

- `scripts/extract_output_rch.py`: parse `output.rch`, identify outlet reach, extract flow.
- `scripts/calculate_metrics.py`: compute R2, NSE, PBIAS, KGE, RMSE, MAE from paired observed/simulated values.
- `scripts/prepare_observed_flow.py`: split observed flow into calibration/validation files for SWAT-CUP.
- `scripts/write_best_params_to_txtinout.py`: copy a clean `TxtInOut`, write best SWAT-CUP parameters, and prepare validation.
- `scripts/check_swatcup_smoke_log.py`: inspect a captured smoke-test console log and fail if any parameter is unsupported, expected parameters were not edited, SWAT did not complete, or objective/post-processing evidence is missing.

When a script cannot be run directly in the current environment, give the user a Codex command or local Python command using their actual paths.

## Key Quality Gates

- Basin area should generally be within 5% of the paper for strict reproduction. A 5-15% mismatch may be acceptable for workflow training but must be recorded.
- `output.rch` record count must match the configured period and output frequency.
- Observed/simulated alignment must have the expected record count for the selected timestep.
- Simulation-weather performance is only a software test. Real weather must be used before judging hydrology.
- Calibration improvement should be assessed against the uncalibrated baseline, not only against the paper.
- Validation must use a separate period and fixed calibrated parameters.
- Never start a formal SWAT-CUP iteration unless the actual project passes the one-simulation smoke test with the same parameter list.

## Common Failure Responses

- If ArcSWAT reads a landuse value like `-128`, set it to NoData, rebuild raster attributes, and ensure every remaining value has a SWAT landuse code.
- If `.sol` writing fails because `SWAT_US_SSURGO_Soils.mdb` is missing, obtain the SWAT US SSURGO database and place it in the ArcSWAT `Databases` directory.
- If SWAT-CUP reports `The given parameter "<NAME>" was not present in the dictionary`, stop the formal run immediately. Do not claim static validation was sufficient. Remove/correct the exact parameter in the actual GUI project's `par_inf.txt`, reset to one simulation, rerun the complete smoke test, and restore the intended simulation count only after it passes.
- Never include `SOL_AWC` or `SOL_K` in the default first-pass list. Their names/syntax are not portable across SWAT-CUP/Swat_Edit builds.
- If a one-simulation post step reports a singular matrix while NSE/95PPU/objective output was produced, treat it as an expected smoke-test limitation, not a dictionary failure.
- If `goal.txt` has fewer rows than expected, inspect `SUFI2_swEdit.def` for the wrong start/end simulation range.
- If SWAT-CUP cannot find `swat`, verify the actual GUI project path and place the correct executable where that project expects it. Do not infer compatibility from the filename alone.
