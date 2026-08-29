# DSSAT v4.8.5.0 M15 source integration

- Status: **SOURCE BUILD + UNIT + OFFICIAL MAIZE RUN PASS**
- Frozen source commit: `0b91373806786b600d89ccfcfff78fa2f82cb26b`
- Frozen data commit: `79cb5db71bbca186add92a6a9695866a09c8b51d`
- M15 formal source candidate: DTR-triggered, DSSAT-CLOUDS-modulated sunset-anchor correction.
- `DTRC=14.8 C` from primary-station 2000-2016 breakpoint analysis.
- `ALPHA=7.8094` from dense Diwopu 2000-2016 sunset-anchor observations.
- No coefficient was fitted on primary-station 2017-2024 validation data.
- Official `HTEMP` subroutine is preserved unchanged; `HTEMP_DTRCLOUD` is called immediately afterward.

## Source-level acceptance
- Source-extracted Fortran unit test: **PASS**.
- Low-DTR synthetic case: exact no-change check PASS.
- High-DTR with CLOUDS=0: exact no-change check PASS.
- High-DTR cloudy synthetic case: bounded and late-branch cooling check PASS.
- Full DSSAT CMake build/install: **PASS**.
- Official UFGA8201 six-treatment execution: **PASS**.
- UFGA8201 Summary.OUT byte-identical to M0: **NO**.
- UFGA8201 PlantGro.OUT byte-identical to M0: **NO**.

Output differences are not themselves a failure because UFGA weather may activate the high-DTR correction. The Florida case is a software/regression execution test, not evidence of Urumqi agronomic benefit.

## Artifacts
- `HMET_M15.for`: patched source snapshot.
- `M15_HMET.patch`: exact diff against frozen upstream HMET.for.
- `M15_UNIT.txt`: source-extracted unit-test output.
- `Summary_M15.OUT`, `PlantGro_M15.OUT`: official maize run outputs.
- `Summary_M0_vs_M15.diff`, `PlantGro_M0_vs_M15.diff`: comparisons with frozen M0.
