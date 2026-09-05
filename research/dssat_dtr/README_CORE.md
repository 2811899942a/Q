# DSSAT temperature core line

Active research branch: `research/dssat-regional-dtr-joint-v1`.

Historical CI workflows, stage outputs, diagnostics, checkpoints, and generated result evidence were archived to Google Drive on 2026-09-05 before pruning the active tree.

## Frozen baseline
- DSSAT CSM OS: `0b91373806786b600d89ccfcfff78fa2f82cb26b`
- DSSAT data: `79cb5db71bbca186add92a6a9695866a09c8b51d`
- Crop model: CERES-Maize / DSSAT 4.8.5

## Active mechanism
- `dssat485/apply_m19_htemp_patch.py` + `apply_m19_htemp_patch_2call.py`: regional DTR-anomaly/radiation correction of hourly `TAIRHR` after official HTEMP.
- `dssat485/apply_m20_dtt_bridge_patch.py`: passes `WEATHER % TAIRHR` into `MZ_PHENOL` and adds only the M19-induced hourly thermal-time delta to official DTT.
- `data/m19_regional_anomaly_threshold/`: frozen regional profile/parameters required by M19.
- Anningqu weather/soil/experiment inputs are retained for reproducibility.

## Local causal validation, 2026-09-05
Executable SHA256:
- M0 `95142027168b8e254879cba43d58c0bf73ca7098ee5d8a973cc094cc298f16ba`
- M19 `8f31913306ae9e80d5a7811e858a97e563e32cad4aa48b2e385d6681df2e1463`
- M20 `8ef57efac1e778028ded75934626b362e33e9bd77b9ace7fa92b42b3544d9f34`

Natural weather: M19 key crop outputs changed 0/10; M20 changed 10/10, mean yield delta -0.5 kg/ha, range -4 to +1.

Controlled Tmax +4 C high-DTR test: M19 changed 0/10; M20 changed 10/10, mean yield delta -9.8 kg/ha, range -224 to +208, mean maturity delta +0.2 d.

Direct `PlantGro.OUT` evidence: ANQH2202 controlled test first visible DTT divergence at 2022 DOY 128, M0 18.70 vs M20 18.67 C d; later biomass and yield diverged. This establishes source-level propagation into CERES-Maize. Predictive improvement still requires observed phenology/yield calibration and independent validation.