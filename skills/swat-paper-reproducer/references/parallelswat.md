# External Parallel SWAT Execution Compatible with SWAT-CUP

Source basis: HydroRS/ParallelSWAT public GitHub repository, especially `Parallel_SWAT_modelling.m`, `Parallel_Computing.m`, `Paramter_Set_Redistribute.m`, and `Comb_Parallel.m`.
Repository: https://github.com/HydroRS/ParallelSWAT
Paper cited by the repository: Zhang L, Zhao Y, Ma Q, Wang P, Ge Y, Yu W. Journal of Hydrology 599 (2021) 126359.

## Purpose

Use this pattern when SWAT-CUP is still useful for SUFI-2 sampling, parameter definitions, extraction definitions, and post-processing, but the built-in SWAT-CUP parallel module is unavailable, trial-limited, or undesirable. This is an external orchestration pattern; do not patch, crack, or bypass licensing checks in the official module.

## Repository Components

The repository separates three roles:

1. `Parallel_SWAT_SetUp`: automate recurring SWAT-CUP setup tasks such as parameter-range updates, observations, time step, warm-up, and simulation period.
2. `Parallel_SWAT_Modelling`: run the SWAT simulations in parallel while keeping the workflow compatible with SWAT-CUP. This is the component to use for ordinary outlet-flow calibration.
3. `Parallel_SWAT_SUFI_Modeling`: spatially stepwise, sub-watershed objective optimization. Use only when the study explicitly needs spatial objective functions such as streamflow plus satellite ET.

## Core Parallelization Algorithm

Preserve the SUFI-2 parameter sample order and split only the expensive SWAT execution stage.

1. Run `SUFI2_Pre.bat` once in the main SWAT-CUP project. This creates the SUFI-2 parameter samples, including `SUFI2.IN/par_val.txt` and the normal control files.
2. Create one isolated worker directory per CPU worker, for example sibling directories `Parallel1`, `Parallel2`, ..., `ParallelN`.
3. Copy the SWAT-CUP execution project into each worker so every worker has its own SWAT inputs, `SUFI2.IN`, `SUFI2.OUT`, executable files, and independent output files. Never let multiple workers write to the same `output.rch`, `output.sub`, or `output.hru`.
4. Redistribute the simulation starting index by writing a different starting value to each worker's `SUFI2.IN/trk.txt`. The original code uses the shared `par_val.txt` and advances each worker through a disjoint contiguous block of sample indices.
5. For each assigned simulation in each worker, run the normal SWAT-CUP execution sequence:
   - `SUFI2_make_input.exe`
   - `Swat_Edit_Hidden.bat` / the project-local Swat_Edit command
   - `swat.exe`
   - `SUFI2_extract_rch.exe`
   - `SUFI2_extract_sub.exe` when needed
   - increment that worker's `trk.txt`
6. After all workers finish, concatenate the worker extraction files back into the main project's `SUFI2.OUT` in the original simulation order.
7. Run `SUFI2_Post.bat` once in the main project so SUFI-2 statistics, objective-function processing, and plots use the merged results.
8. Optionally archive the completed `SUFI2.IN` and `SUFI2.OUT` as one iteration.

The key idea is therefore:

`SUFI2_Pre once -> split sample indices -> isolated parallel SWAT runs -> merge extracted outputs -> SUFI2_Post once`.

## Worker Count and Simulation Count

The original MATLAB implementation assumes:

`Num_simulation / work_number` is an integer.

Choose a worker count that divides the formal simulation count exactly. Example: 1000 simulations with 8 workers gives 125 simulations per worker and satisfies the original implementation's assumption.

If adapting the framework to a scheduler that supports uneven chunks, preserve the exact one-to-one mapping between SUFI-2 sample index and output row; never drop, duplicate, or reorder simulations silently.

## Implementation Notes

The repository implementation is MATLAB-era code using `matlabpool`, `Composite`, and `spmd`. On modern MATLAB, the orchestration may need `parpool` or updated parallel APIs. A Python or PowerShell process-pool port is also valid if it preserves the same file-level isolation, sample-index bookkeeping, command sequence, and result ordering.

The repository README instructs users to copy helper files from `Source/Bat_files` into the SWAT-CUP execution folder. Relevant helpers include `Swat_Edit_Hidden.bat` and post-processing wrappers. Verify command names against the local SWAT-CUP project rather than assuming the repository's old filenames match the installed version.

## Safety and Reproducibility Gates

- External parallelization does not prove that a parameter name is accepted by the local `Swat_Edit` dictionary. Parameter compatibility still needs a real project-level execution check when a new parameter list is introduced.
- Use the exact same SWAT executable revision in every worker.
- Clone the same Dynamic LULC files, weather files, `file.cio`, and calibration-period settings into every worker.
- Keep the test/validation period out of the calibration objective and parameter selection.
- Record worker count, simulation count, sample-index ranges, failed simulation IDs, executable revision, and elapsed time.
- If any worker fails, do not merge partial results as if the iteration were complete. Identify failed simulation IDs and rerun only the missing jobs using the same parameter samples.
- Do not use an external runner to circumvent software licensing controls. The legitimate pattern is to bypass the optional official parallel module entirely and execute ordinary command-line SWAT instances in isolated worker folders.

## Practical Decision Rule

When a user encounters a SWAT-CUP parallel-module trial limit, distinguish two different things:

- Official SWAT-CUP parallel module: may have its own license or trial restrictions.
- External ParallelSWAT-style orchestration: independently launches ordinary SWAT/SWAT-CUP command-line steps across isolated workers and then returns merged outputs to SUFI-2.

Do not tell the user that a trial limit necessarily forces serial calibration if an external orchestration workflow is technically and legally available for their project.
