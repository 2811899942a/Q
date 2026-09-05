# DSSAT temperature optimization handoff — 2026-09-05

## Scope lock

Repository: `2811899942a/Q`  
Branch: `research/dssat-regional-dtr-joint-v1`  
DSSAT source: `0b91373806786b600d89ccfcfff78fa2f82cb26b`  
DSSAT data: `79cb5db71bbca186add92a6a9695866a09c8b51d`  
Model: DSSAT v4.8.5 / CERES-Maize

Canonical research summary:

`research/dssat_dtr/DSSAT_BEST_RESULT_AND_INNOVATION_FLOW_FINAL.md`

Reproducibility index:

`research/dssat_dtr/DSSAT_REPRODUCIBILITY_INDEX.md`

Continuous experiment record:

`research/dssat_dtr/EXPERIMENT_LOG_M17_M19.md`

## Current scientific state

### M17b — temperature performance benchmark

- overall hourly-temperature RMSE: 2.583205 C vs official 2.946891 C; improvement 12.34%
- DTR>=15 C RMSE: 4.376778 C vs official 5.121512 C; improvement 14.54%
- 2020-2024 annual high-DTR win: 5/5
- physical violations: 0/123
- k_pre/k_post remain at expanded upper boundary ~40
- role: performance benchmark only

### M19 — transferable regional parameter architecture

`K_RT = local seasonally standardized DTR anomaly threshold`, unit SD.

Current exploratory Urumqi value:

`K_RT = 1.40 SD`

Other tracked structure:

- Kt0 = 0.70
- P_TARGET = 20.0
- gain_scale = 0.25

Result:

- overall RMSE 2.833762 C
- high-DTR RMSE 4.742319 C
- annual win 5/5
- physical violations 0/123
- inactive closure 0.000e+00 C

### M19 source-interface audit

M19 activates in natural Anningqu crop seasons, but M19-only does not change CERES-Maize outputs because frozen DSSAT v4.8.5 CERES-Maize does not directly consume Weather%TAIRHR/TGRO in MZ_PHENOL/MZ_GROSUB.

Evidence:

- M0/M15/M19 source workflow run 33955930639 SUCCESS
- M19 crop change 0/10
- activation diagnostic run 33956190680 SUCCESS
- 2021 May-Sep active days: 6
- 2022 May-Sep active days: 2

### M20 — final mechanistic bridge

Formula:

`DTT_M20 = DTT_official + [TT24(TAIRHR_M19)-TT24(TAIRHR_HTEMP)]`

K_LINK = 1.0 fixed structural constant.

Source patch:

`research/dssat_dtr/dssat485/apply_m20_dtt_bridge_patch.py`

Linux source-level causal run 33956296856: SUCCESS.

- 60/60 DSSAT runs completed
- NATURAL M19 vs M0: 0/10 changed
- NATURAL M20 vs M0: 10/10 changed; mean yield -0.5 kg/ha; max abs 4 kg/ha
- STRESS_DTR4 M19 vs M0: 0/10 changed
- STRESS_DTR4 M20 vs M0: 10/10 changed; mean yield -9.8 kg/ha; range -224 to +208; max abs 224; mean maturity +0.2 d

Scientific decision:

**Core innovation architecture = M19 K_RT + M20 neutral incremental DTT bridge.**

M17b remains the strongest hourly-temperature performance reference.

## Windows reproduction

Canonical command:

```powershell
.\repro\windows_dssat_temperature_v1\run_m20_bridge.ps1
```

First Windows CI: run 33956557399.

Verified before failure:

- Windows Server 2022
- MinGW gfortran 16.1.0
- M19/M20 source patches
- M0 native Fortran compilation and `dscsm048.exe` link at 100%

Failure source: upstream CMake install attempted to install Unix helper `Utilities/run_dssat` after executable link.

Fix commit: `315d2272a99607d3759d0f4281a9d562e04023a9`.

Fix strategy: keep normal native CMake compile, skip the irrelevant Unix-helper install action, assemble each runtime from its successfully built `dscsm048.exe` plus exact frozen data.

Second Windows CI: run `33956729437`; terminal result must be checked before claiming Windows end-to-end PASS.

## Next publication-level work

1. obtain/use target Urumqi/Xinjiang hourly temperature and target-cultivar observations;
2. formal high/low/DTT/K_RT sensitivity with EFAST or Sobol, including growth-stage effects;
3. calibrate K_RT on training years/sites;
4. validate phenology and yield on independent years/sites;
5. perform at least one cross-site/cross-region transfer test with the same M19+M20 structure;
6. only then quantify real regional crop-accuracy improvement.

## Language boundary for reports

Safe current claim:

“Regional DTR-anomaly information can be represented by an interpretable threshold parameter and propagated through a neutral incremental thermal-time bridge into CERES-Maize.”

Avoid claiming current proxy-cultivar or controlled-stress yield deltas are real Xinjiang yield impacts.
