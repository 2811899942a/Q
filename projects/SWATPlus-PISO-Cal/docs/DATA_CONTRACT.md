# Data contract

All arrays use float32 unless a reproducibility reason requires float64.

## Formal A-basin files

```text
theta.npy                 [N,14]
qsim.npy                  [N,3,T]
qobs.npy                  [3,T]
dates.csv                 T rows
parameter_bounds.csv      14 rows
metadata.json
```

Gauge order is immutable:

1. 01605500 / ch12
2. 01606000 / ch17
3. 01606500 / ch18

Development data span 2003-01-01 through 2016-12-31 after alignment with the established A-basin workflow. Locked validation and final-test values must not be included in method-development arrays.

## parameter_bounds.csv

Required columns:

```text
name,lower,upper,transform,change_type,target_file,target_field
```

The 14 rows are inherited from the established A-basin calibration workflow. Do not reconstruct parameter semantics from memory.

## Formal metadata.json

At minimum:

```json
{
  "study_area_id": "A_SOUTH_BRANCH_POTOMAC",
  "swatplus_revision": "62.0.0",
  "parameter_dim": 14,
  "gauges": ["01605500", "01606000", "01606500"],
  "gauge_channels": [12, 17, 18],
  "development_start": "2003-01-01",
  "development_end": "2016-12-31",
  "source_class": "observation_independent_broad",
  "contains_locked_validation": false,
  "contains_final_test": false,
  "objective_definition_hash": "sha256 of frozen inherited objective definition",
  "parameter_dictionary_hash": "sha256 of frozen 14D dictionary",
  "source_archive": "absolute local provenance or immutable manifest id",
  "content_hashes": {}
}
```

`source_class=observation_directed_optimizer_trace` is forbidden for the primary inverse/posterior training library.

## Leakage and provenance rules

- Simulation train/validation/test indices are split by parameter realization.
- Flow and parameter scalers are fitted on training realizations only.
- Real observed flow is never used to fit simulation normalization statistics.
- DeepCal/DDS/DE/BO trajectories are not merged into the from-scratch broad training library.
- 2017–2020 and 2021–2024 are not read during method selection.
- Public DL4SWAT reproduction uses a separate generic data root and the generic `load_dataset`; formal A-basin work uses `load_south_branch_dataset`.
