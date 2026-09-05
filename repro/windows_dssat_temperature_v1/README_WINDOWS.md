# DSSAT regional-temperature experiment: Windows reproduction

This folder reproduces the current regional-temperature research chain on a Windows machine. The workflow is split into a temperature gate and a full DSSAT source gate so compiler/runtime issues cannot obscure the model-method result.

## Frozen research state

- Repository branch: `research/dssat-regional-dtr-joint-v1`
- DSSAT source commit: `0b91373806786b600d89ccfcfff78fa2f82cb26b`
- DSSAT data commit: `79cb5db71bbca186add92a6a9695866a09c8b51d`
- M17b: strongest hourly-temperature fit candidate.
- M19: transferable regional-parameter architecture candidate.
- M20: validated source bridge from the M19 hourly signal into CERES-Maize daily thermal time (DTT).
- Regional parameter: `K_RT = 1.40 SD`, the local seasonally standardized DTR anomaly trigger threshold.
- Structural bridge constant: `K_LINK = 1.0`; it is fixed and is not a second regional calibration parameter.
- Linux reference workflow: GitHub Actions run `33956296856`, SUCCESS.

## Method chain

M19 weather trigger:

```text
z_DTR = (DTR - local seasonal DTR mean) / local seasonal DTR SD
E     = max(z_DTR - K_RT, 0) * max(Kt0 - Kt, 0) / 0.1
S     = 1 - exp(-E / gain_scale)
q_new = (1-S)*q_official + S*q_official^P_TARGET
```

Tracked structural values:

```text
K_RT       = 1.40 SD      # regional calibration target
Kt0        = 0.70
P_TARGET   = 20.0
gain_scale = 0.25
```

M20 source bridge:

```text
DTT_M20 = DTT_official
        + K_LINK * [TT24(TAIRHR_M19) - TT24(TAIRHR_HTEMP)]

TT24(T) = mean_h( clip(T_h, TBASE, DOPT) - TBASE ), h=1..24
K_LINK  = 1.0
```

If M19 is inactive, `TAIRHR_M19 = TAIRHR_HTEMP`; therefore the bracketed term is exactly zero and CERES-Maize retains the official DTT solution.

## Why M20 is required

The source audit showed that DSSAT v4.8.5 `MZ_CERES.for` takes daily `TMAX`, `TMIN`, `SRAD` and `DAYL` into the CERES-Maize phenology/growth routines. The weather-layer hourly arrays `TAIRHR/TGRO` are not directly consumed by `MZ_PHENOL` or `MZ_GROSUB`.

This was verified experimentally: M19 activated on multiple 2021/2022 Anningqu growing-season days but M0 and M19 produced identical CERES-Maize crop outputs in all 10 scenarios. M20 explicitly passes the hourly state into `MZ_PHENOL` and adds only the M19-induced hourly thermal-time delta to official DTT.

## Layer A — reproduce the temperature mechanism

Requirements: Git, Python and CMake. A Fortran compiler is not required for this layer.

From PowerShell at repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\repro\windows_dssat_temperature_v1\run_temperature_only.ps1
```

PASS requires:

1. M19 recalculates `K_RT` at approximately 1.40 SD.
2. An effectively inactive trigger reproduces official HTEMP with max absolute difference <= `1e-10 C` in the tracked screen.
3. Full-curve physical checks contain zero Tmin/Tmax/monotonicity violations.

Exact Linux/Windows final floating-point digits are not a scientific requirement.

## Layer B — full M0/M19/M20 source reproduction

Additional requirements: a Windows Fortran/Make toolchain exposing `gfortran` and `mingw32-make` in `PATH`. The script uses CMake `MinGW Makefiles` and creates independent source/build/runtime trees.

Recommended command:

```powershell
.\repro\windows_dssat_temperature_v1\run_m20_bridge.ps1
```

The legacy entry point also forwards to the same validated workflow:

```powershell
.\repro\windows_dssat_temperature_v1\run_full_crop_ab.ps1
```

The script will:

1. clone the exact frozen DSSAT source/data commits;
2. create independent M0, M19 and M20 source trees;
3. apply M19 to M19/M20 and apply the neutral DTT bridge only to M20;
4. rewrite each Windows build's `STDPATH` to its own runtime folder and leave any installed `C:\DSSAT48` untouched;
5. compile/install three independent DSSAT executables;
6. add identical Anningqu weather, soil, fixed proxy cultivar and five sowing dates for 2021/2022;
7. run NATURAL weather: 10 scenarios x 3 variants = 30 DSSAT runs;
8. create identical controlled high-DTR weather in all arms by adding +4 C to TMAX during DOY 121-273;
9. run STRESS_DTR4: another 30 DSSAT runs;
10. preserve Summary.OUT, PlantGro.OUT and stdout for every run;
11. parse M0/M19/M20 crop-output deltas and enforce the causal bridge gates;
12. write `manifest.json` with frozen commits and PASS state.

Required causal invariants:

```text
NATURAL M19 vs M0       changed scenarios = 0
STRESS_DTR4 M19 vs M0   changed scenarios = 0
STRESS_DTR4 M20 vs M0   changed scenarios >= 1
```

Linux reference run `33956296856` produced:

```text
NATURAL M20:     10/10 scenarios changed
                  mean yield delta = -0.5 kg/ha
                  max absolute yield delta = 4 kg/ha
                  mean anthesis delta = 0 d
                  mean maturity delta = 0 d

STRESS_DTR4 M20: 10/10 scenarios changed
                  mean yield delta = -9.8 kg/ha
                  yield delta range = -224 to +208 kg/ha
                  max absolute yield delta = 224 kg/ha
                  mean anthesis delta = 0 d
                  mean maturity delta = +0.2 d
```

These exact numeric values are reference results, not cross-platform equality requirements. Windows reproduction passes when the source builds/runs cleanly and the causal invariants are reproduced.

## Generated locations

```text
repro/windows_dssat_temperature_v1/work_m20/
  src_M0/ src_M19/ src_M20/
  build_M0/ build_M19/ build_M20/
  run_M0/ run_M19/ run_M20/
  results/
    NATURAL/
      M0/ M19/ M20/
    STRESS_DTR4/
      M0/ M19/ M20/
  compact_results/
    bridge_detail.csv
    bridge_summary.csv
    README.md
    manifest.json
```

The generated work tree is retained for audit after a successful run and can be deleted manually after archiving.

## Interpretation boundary

The 2021/2022 Anningqu experiments use fixed DSSAT proxy cultivar IB0035, controlled sowing dates, `WATER=N` and `NITRO=N`. NATURAL runs prove that the bridge can transmit the small regional hourly-temperature signal into CERES-Maize. STRESS_DTR4 is a controlled causal stress test that proves the bridge responds under stronger DTR forcing. These runs are mechanism tests, not target-cultivar observed-yield validation.

Publication-level regional claims still require local Xinjiang/Urumqi hourly temperature, target-cultivar phenology/yield observations, formal sensitivity analysis and independent/cross-site validation.
