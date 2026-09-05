# DSSAT regional-temperature reproducibility index

Canonical branch: `research/dssat-regional-dtr-joint-v1`

## Frozen DSSAT baseline

- source: `DSSAT/dssat-csm-os@0b91373806786b600d89ccfcfff78fa2f82cb26b`
- data: `DSSAT/dssat-csm-data@79cb5db71bbca186add92a6a9695866a09c8b51d`
- model: DSSAT v4.8.5 / CERES-Maize

## Canonical research summary

- `research/dssat_dtr/DSSAT_BEST_RESULT_AND_INNOVATION_FLOW_FINAL.md`
- `research/dssat_dtr/EXPERIMENT_LOG_M17_M19.md`

## Best temperature-performance result: M17b

- directory: `research/dssat_dtr/data/m17b_regional_radwarp_boundary_audit/`
- overall RMSE: 2.583205 C vs official 2.946891 C
- high-DTR RMSE: 4.376778 C vs official 5.121512 C
- high-DTR physical violations: 0/123
- annual high-DTR win: 5/5 years
- role: performance benchmark; shape coefficients remain boundary-limited

## Transferable regional parameter: M19

- parameters: `research/dssat_dtr/data/m19_regional_anomaly_threshold/parameters.json`
- regional climatology: `research/dssat_dtr/data/m19_regional_anomaly_threshold/regional_dtr_profile_2000_2016.csv`
- K_RT: 1.40 SD
- M19 source patch: `research/dssat_dtr/dssat485/apply_m19_htemp_patch_2call.py`
- activation diagnostic: `research/dssat_dtr/data/anningqu/m19_activation_diagnostic/`
- activation workflow: `.github/workflows/dssat-m19-anningqu-activation.yml`
- activation run: `33956190680` SUCCESS

## Crop interface audit

- M0/M15/M19 workflow: `.github/workflows/anningqu-m0-m15-m19-propagation-v2.yml`
- run: `33955930639` SUCCESS
- parser: `research/dssat_dtr/scripts/parse_m0_m15_m19_propagation.py`
- compact results: `research/dssat_dtr/data/anningqu/m19_source_propagation/`
- result: M19-only crop output change = 0/10, establishing the CERES-Maize hourly-temperature interface gap

## Final source bridge: M20

Formula:

`DTT_M20 = DTT_official + [TT24(TAIRHR_M19) - TT24(TAIRHR_HTEMP)]`

- source patch: `research/dssat_dtr/dssat485/apply_m20_dtt_bridge_patch.py`
- controlled weather builder: `research/dssat_dtr/scripts/build_controlled_dtr_weather.py`
- parser: `research/dssat_dtr/scripts/parse_m0_m19_m20_bridge.py`
- workflow: `.github/workflows/dssat-m20-dtt-bridge.yml`
- Linux source-level causal run: `33956296856` SUCCESS
- total DSSAT runs: 60/60
- compact results: `research/dssat_dtr/data/anningqu/m20_dtt_bridge/`

Reference M20 results:

- NATURAL: 10/10 scenarios changed; mean yield delta -0.5 kg/ha; max abs 4 kg/ha
- STRESS_DTR4: 10/10 changed; mean yield delta -9.8 kg/ha; range -224 to +208 kg/ha; max abs 224 kg/ha; mean maturity delta +0.2 d

## Windows reproduction

Folder:

`repro/windows_dssat_temperature_v1/`

Primary commands:

```powershell
.\repro\windows_dssat_temperature_v1\run_temperature_only.ps1
.\repro\windows_dssat_temperature_v1\run_m20_bridge.ps1
```

Key files:

- `README_WINDOWS.md`
- `environment_check.ps1`
- `run_temperature_only.ps1`
- `run_m20_bridge.ps1`
- `run_full_crop_ab.ps1` (legacy entry; forwards to M20)

Windows CI:

- workflow: `.github/workflows/dssat-m20-windows-repro.yml`
- first run: `33956557399`; native gfortran compilation and dscsm048.exe link passed, upstream Unix-helper CMake install failed
- fix: bypass upstream `run_dssat` install helper and assemble runtime from native built `dscsm048.exe` plus frozen data
- second run: `33956729437`; see experiment log for terminal status

## Scientific evidence boundaries

Mechanism-level claims currently supported:

- official HTEMP has measurable optimization room under the target high-DTR climate sample;
- K_RT is an interpretable region-relative trigger parameter and has exact inactive closure in the tracked screen;
- M19 activates in natural Anningqu crop-season weather;
- CERES-Maize v4.8.5 does not directly consume the M19 hourly arrays in its main phenology/growth path;
- M20 creates a reproducible incremental-hourly-temperature to DTT crop pathway.

Publication-level regional performance still requires target Xinjiang cultivar observations, phenology/yield validation, formal EFAST/Sobol analysis, and independent/cross-site tests.
