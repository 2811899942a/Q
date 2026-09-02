# Data contract

All arrays must use float32 unless there is a strong reason to retain float64.

## Required files

### `theta.npy`

Shape `[N, P]`. Each row is one Real-SWAT+ parameter vector. Values are in physical units.

### `qsim.npy`

Shape `[N, G, T]`. Daily simulated discharge aligned across all simulations and gauges.

### `qobs.npy`

Shape `[G, T]`. Daily observed discharge for the same gauges and dates.

### `dates.csv`

One ISO date per row. Exactly `T` rows.

### `parameter_bounds.csv`

Columns:

```text
name,lower,upper,transform,change_type,target_file,target_field
```

`transform` is one of `linear`, `log`, or `logit`. `change_type` records SWAT+ absolute, relative, or replacement semantics.

### `metadata.json`

Must include:

```json
{
  "swatplus_revision": "62.0.0",
  "parameter_dim": 14,
  "gauges": ["01605500", "01606000", "01606500"],
  "start_date": "2003-01-01",
  "end_date": "2016-12-31",
  "objective_definition": "frozen identifier",
  "source_archive": "path or DOI",
  "content_hashes": {}
}
```

## Leakage rules

- Simulation train/validation/test indices are split by parameter realization.
- All flow and parameter scalers are fitted on training realizations only.
- Observed flow is never included in simulation training statistics.
- 2017-2020 and 2021-2024 are not read during method selection.
- Public DL4SWAT reproduction and South Branch experiments use separate data roots and manifests.
