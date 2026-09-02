# A0 South Branch takeover audit report

## Gate result

**A0_PASS**

The gate is closed unless every required check below is true. A0 only audits and
standardizes existing assets; it does not start A1-A5, inverse training, or optimizer runs.

## Locked contract

- Study area: `A_SOUTH_BRANCH_POTOMAC`
- SWAT+ revision: `62.0.0`
- Gauges/channels: `01605500/ch12`, `01606000/ch17`, `01606500/ch18`
- Parameter dimension/order: `14`, `cn2, latq_co, lat_ttime, esco, epco, petco, alpha, bf_max, revap_co, deep_seep, surlag, chn, chk, perco`
- Warmup: `2000-2002`; development: `2003-2016`; locked validation: `2017-2020`; final test: `2021-2024`

## Canonical asset locations

- Frozen SWAT+ project/template: `D:\SWAT+_3V3\A_SouthBranchPotomac\calibration_R3_4096\template_frozen`
- Inherited writer/parser/objective source: `D:\SWAT+_3V3\A_SouthBranchPotomac\calibration_R3_4096\r3_calibration.py`; standardized writer-vector bridge: `D:\SWAT+_3V3\A_SouthBranchPotomac\DEEP_CAL_SWAT\04_real_swat_runs\deepcal_standardized_smoke.py`
- rev.62 executable: `D:\QAPP\SWATPlus\Editor\resources\app.asar.unpacked\static\swat_exe\swatplus-62-ifo-win_amd64-Rel.exe`
- 14D source space: `D:\SWAT+_3V3\A_SouthBranchPotomac\DEEP_CAL_SWAT\02_parameter_space\PARAMETER_SPACE_MVP1.csv`; machine-readable dictionary: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a0\parameter_dictionary_14d.json`
- Formal handoff manifest (500): `D:\SWAT+_3V3\A_SouthBranchPotomac\DEEP_CAL_SWAT\04_real_swat_runs\high_throughput_runner_v2\formal_500_handoff_corrected\manifest.json`
- Production Sobol manifest/features (4,500): `D:\SWAT+_3V3\A_SouthBranchPotomac\DEEP_CAL_SWAT\04_real_swat_runs\high_throughput_runner_v2\production_5k\manifest.json`
- Broad/optimizer/unknown derived manifests: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a0\provenance`
- Locked observed streams: `D:\HydroC_SWATPlus\00_QC\clean_csv`; canonical qobs audit: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a0\observations\qobs_audit.csv`
- Standard tensors: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a0\dataset`; gate/metadata: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a0\A0_GATE.json`

## Provenance and tensors

- All manifest rows: `12672`
- Standardized candidate rows: `5000`
- Broad admitted rows: `4980`
- Optimizer-directed/reference rows: `7665`
- Unknown/reference rows: `27`
- Legacy asset-index rows classified optimizer-directed/reference-only: `7665`; the previously suggested approximate 2,400 count is not supported by this local index, so no unverified collapse was performed.
- Tensor shapes: `{'theta': [4980, 14], 'qsim': [4980, 3, 5114], 'qobs': [3, 5114]}`
- qobs unit/rows: `m3/s`, `[3, 5114]`

## Checks

- PASS: `study_lock`
- PASS: `canonical_project`
- PASS: `parameter_dimension`
- PASS: `gauge_order`
- PASS: `period_lock`
- PASS: `broad_provenance`
- PASS: `optimizer_rejection`
- PASS: `paper_rejection`
- PASS: `validation_final_leakage`
- PASS: `qobs_audit`
- PASS: `tensor_shape_and_finite`
- PASS: `manifest_uniqueness`
- PASS: `leakage_audit`
- PASS: `objective_snapshot`
- PASS: `runner_equivalence`
- PASS: `evaluation_accounting`

## Entry boundary

`A1 may start only from dataset/source_class=observation_independent_broad after A0_PASS; A0_FAIL forbids A1-A5/model training.`

The canonical artifacts are under `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a0`. The GitHub commit must include the
source scripts, tests, lock-derived reports, and small metadata manifests; large local
`.npy` tensors remain reproducible outputs and are not committed.
