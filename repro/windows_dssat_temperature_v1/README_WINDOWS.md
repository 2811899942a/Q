# DSSAT regional-temperature experiment: Windows reproduction

This folder reproduces the current temperature-model research chain on a Windows machine. It is intentionally split into two gates so a compiler/runtime problem cannot hide the temperature-method result.

## Frozen research state

- Repository branch: `research/dssat-regional-dtr-joint-v1`
- DSSAT source: v4.8.5.0 commit `0b91373806786b600d89ccfcfff78fa2f82cb26b`
- DSSAT data: commit `79cb5db71bbca186add92a6a9695866a09c8b51d`
- M15: frozen physical benchmark.
- M17b: best temperature-fit candidate; retained as performance evidence.
- M19: transferable-parameter architecture candidate.
- M19 regional parameter: `K_RT = 1.40 SD`, defined as the seasonally standardized local DTR anomaly threshold.

M19 source logic:

```text
z_DTR = (DTR - local seasonal DTR mean) / local seasonal DTR SD
E     = max(z_DTR - K_RT, 0) * max(Kt0 - Kt, 0) / 0.1
S     = 1 - exp(-E / gain_scale)
q_new = (1-S)*q_official + S*q_official^P_TARGET
```

Tracked structural values are read from `research/dssat_dtr/data/m19_regional_anomaly_threshold/parameters.json`; the 366-day Urumqi calibration profile is tracked in `regional_dtr_profile_2000_2016.csv`.

## Layer A — reproduce the temperature mechanism

Requirements: Git, Python, CMake. A Fortran compiler is not required for this layer.

From PowerShell at repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\repro\windows_dssat_temperature_v1\run_temperature_only.ps1
```

PASS requires:

1. M19 recalculates `K_RT` at approximately 1.40 SD.
2. Setting the trigger effectively inactive reproduces official HTEMP with max absolute difference <= `1e-10 C` in the tracked screen.
3. Full-curve physical checks have zero Tmin/Tmax/monotonicity violations.

The exact Linux/Windows text formatting or final floating-point digits are not a scientific requirement.

## Layer B — rebuild DSSAT and reproduce crop propagation

Additional requirements: a Windows Fortran/Make toolchain exposing `gfortran` and `mingw32-make` in `PATH`. The script uses CMake `MinGW Makefiles` and creates all source/build/runtime trees under this folder's `work` directory.

```powershell
.\repro\windows_dssat_temperature_v1\run_full_crop_ab.ps1
```

The script will:

1. clone the exact frozen DSSAT source/data commits;
2. create independent M0, M15 and M19 source trees;
3. apply the tracked source patches;
4. rewrite only each build's Windows `STDPATH` so the experiment does not touch an existing `C:\DSSAT48` installation;
5. compile and install three independent DSSAT executables;
6. copy identical Anningqu weather/soil and create ten controlled maize scenarios per arm;
7. execute 30 DSSAT runs;
8. preserve `Summary.OUT`, `PlantGro.OUT`, stdout and warnings;
9. parse a compact M0/M15/M19 comparison and write a manifest.

The Windows source-level mechanism gate is deliberately simple: M19 must compile and execute cleanly and must produce at least one reproducible CERES-Maize output change relative to M0 with all non-temperature inputs held identical. Exact equality to the GitHub Ubuntu runner is not required.

## Generated locations

```text
repro/windows_dssat_temperature_v1/work/
  src_M0/ src_M15/ src_M19/
  build_M0/ build_M15/ build_M19/
  run_M0/ run_M15/ run_M19/
  results/
    M0/ M15/ M19/
  compact_results/
    m0_m15_m19_crop_outputs.csv
    propagation_summary.csv
    README.md
    manifest.json
```

The generated `work` directory is intentionally retained after a successful run for audit. It can be deleted manually after the outputs have been archived.

## Interpretation boundary

The 2021/2022 Anningqu experiments use fixed DSSAT proxy cultivar IB0035, controlled sowing dates, `WATER=N` and `NITRO=N`. They test propagation from the modified hourly temperature reconstruction into CERES-Maize. They are not a calibration or observed-yield validation for the target Xinjiang cultivar.

A publication-level regional claim still requires fresh/local Xinjiang weather plus observed phenology/yield data under an external validation design.
