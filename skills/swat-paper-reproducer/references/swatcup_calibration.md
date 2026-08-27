# SWAT-CUP 2012 SUFI-2 Calibration

## Non-Negotiable Parameter-Dictionary Guardrail

SWAT-CUP parameter compatibility is controlled by the local `Swat_Edit` dictionary. Static inspection of `par_inf.txt`, file extensions, or generic SWAT parameter lists cannot prove compatibility.

Before any formal iteration:

1. Locate the **actual GUI project** created by SWAT-CUP, usually ending in `.Sufi2.SwatCup`.
2. Confirm which `SUFI2.IN`, `SUFI2.OUT`, working files, batch files, and `swat.exe` the GUI project actually calls.
3. Configure the full candidate parameter list in that actual project.
4. Temporarily set the simulation range to `1` through `1`.
5. Run `SUFI2_pre.bat`, `SUFI2_run.bat`, and `SUFI2_post.bat` end to end.
6. Require every candidate parameter to be edited successfully by `Swat_Edit`.
7. Require SWAT to complete normally, the target variable to be extracted, and the objective function to be calculated.
8. Restore the intended formal simulation range only after the smoke test passes.

Do not declare `READY_TO_RUN` from static validation alone.

If the console reports:

```text
The given parameter "<NAME>" was not present in the dictionary
```

stop immediately. Remove or correct the exact unsupported parameter, then rerun the complete one-simulation smoke test. Never use the 100/500-run formal iteration as a dictionary test.

A one-simulation post-processing warning about singular matrices or parameter-range updating can be expected because one sample cannot support regression/range statistics. Accept it only when parameter editing, SWAT execution, output extraction, NSE/objective calculation, and 95PPU processing succeeded.

## Project Setup

Use `SUFI2`, SWAT 2012 input format, and the same processor architecture used in ArcSWAT. Prefer short paths.

Required checks before running:

```text
par_inf.txt                  parameter names, ranges, number of simulations
observed_rch.txt             observed calibration values
SUFI2_extract_rch.def        output.rch, variable column, reach, years, timestep
SUFI2_swEdit.def             start/end simulation range
swat.exe                     actual executable called by the GUI project
```

Do not assume that a staging directory such as `D:\SWATCUP_PROJECT\SUFI2.IN` is the directory read by the GUI. New SWAT-CUP projects commonly create their own project-local `SUFI2.IN` and default files.

## Extract Definition

For monthly outlet-flow calibration, `SUFI2_extract_rch.def` should indicate:

```text
output.rch
1 variable
FLOW_OUTcms actual column number
actual total reaches
1 selected reach
outlet reach ID
beginning calibration year
ending calibration year
2 for monthly
```

Always verify the `FLOW_OUTcms` column number from the actual `output.rch` header.

## First-Pass Parameter Strategy

Use a compact first-pass set that avoids nonportable soil-layer dictionary entries:

```text
r__CN2.mgt          -0.20      0.20
v__ALPHA_BF.gw       0.00      1.00
v__GW_DELAY.gw       0.00    500.00
v__GWQMN.gw          0.00   5000.00
v__RCHRG_DP.gw       0.00      1.00
v__GW_REVAP.gw       0.02      0.20
v__ESCO.hru          0.50      1.00
v__SURLAG.bsn        0.50     10.00
v__CH_N2.rte         0.01      0.15
v__CH_K2.rte         0.00    150.00
```

These are candidates, not guaranteed universal names. The real one-simulation smoke test remains mandatory.

Do **not** include the following by default:

```text
SOL_AWC
SOL_K
```

Their availability and accepted syntax vary across SWAT-CUP/`Swat_Edit` builds. Add soil-layer parameters only after confirming their exact local syntax with an isolated one-simulation smoke test.

## Formal Iteration Rules

- Run the real one-simulation smoke test before every new parameter-list design.
- Use the first formal iteration for broad parameter-space search and sensitivity diagnosis.
- Use the next iteration with ranges narrowed from the previous output, while retaining physical bounds such as `ALPHA_BF <= 1` and `ESCO <= 1`.
- Do not equate more iterations with better science. Stop when validation no longer improves or parameters become unstable/overfit.
- Respect user disk limits. Keep only required iteration outputs; do not create redundant project copies, ZIPs, or automatic backups when the user has prohibited them.
- If `goal.txt` has fewer rows than expected, inspect `SUFI2_swEdit.def` for an incorrect end simulation number.

## Smoke-Test Acceptance Checklist

A parameter list passes only if all are true:

```text
No "not present in the dictionary" errors
Expected parameter count was edited
Every expected parameter name appears in the console log
SWAT execution completed normally
Target output file was produced
Target reach and variable were extracted
Objective function was calculated
Formal simulation range was restored after the test
```

Use `scripts/check_swatcup_smoke_log.py` to evaluate a captured console log when available.

## Calibration Decision

Proceed to validation when:

- NSE materially improves over the uncalibrated baseline.
- PBIAS is within a defensible range for the study scale.
- KGE is stable or improved.
- P-factor and R-factor are acceptable for the chosen uncertainty objective.
- Best parameters are not all pressed against their bounds.
- Additional iterations mainly trade off metrics or degrade independent validation.

Do not chase perfect calibration if basin area, land-use year, weather source, or observation quality differs from the reference study.


## External Parallel Execution Alternative

If the official SWAT-CUP Parallel Processing Module is unavailable or limited by a trial license, do not assume the only alternative is a long serial run. Read `references/parallelswat.md` and use the HydroRS/ParallelSWAT execution pattern when appropriate.

The external pattern keeps SWAT-CUP responsible for SUFI-2 setup and post-processing but moves the expensive simulation loop outside the optional licensed parallel module:

```text
SUFI2_Pre once
  -> create isolated Parallel1..ParallelN worker folders
  -> assign disjoint SUFI-2 sample indices through each worker's trk.txt
  -> in each worker: make_input -> Swat_Edit -> swat.exe -> extract
  -> merge worker extraction files into main SUFI2.OUT in sample order
  -> SUFI2_Post once
```

The original MATLAB code requires the total simulation count to be divisible by the worker count. For 1000 simulations and 8 workers, each worker executes 125 samples. Each worker must have its own SWAT working files and outputs; never share `output.rch`, `output.sub`, or `output.hru` between concurrent processes.

This workflow is not a license bypass: it does not modify the official trial module. It simply does not use that optional module and instead launches ordinary SWAT command-line runs externally. Preserve the same SWAT executable, parameter samples, calibration period, extraction definitions, and output ordering as the main SWAT-CUP project.
