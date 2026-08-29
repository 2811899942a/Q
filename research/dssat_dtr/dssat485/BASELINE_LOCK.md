# DSSAT v4.8.5.0 Formal Baseline Lock

Status: **FROZEN FOR THIS STUDY**

This project deliberately uses DSSAT **v4.8.5.0** as the sole formal source/data baseline for all M0-vs-modified-HTEMP comparisons. Newer DSSAT releases are not mixed into the formal experiment.

## Exact upstream references

### DSSAT source
- Repository: `DSSAT/dssat-csm-os`
- Tag: `v4.8.5.0`
- Annotated tag object: `4dbf6d5a8b5928276e8713ead9a943cc5e1b3eed`
- Frozen commit: `0b91373806786b600d89ccfcfff78fa2f82cb26b`
- CMake version fields at this ref: `MAJOR=4`, `MINOR=8`, `MODEL=5`, `BUILD=0`
- Linux executable name: `dscsm048`

### DSSAT data
- Repository: `DSSAT/dssat-csm-data`
- Tag: `v4.8.5.0`
- Annotated tag object: `8cbf76628f0753b9d8d78b5ac6908c2d1d3c4219`
- Frozen commit: `79cb5db71bbca186add92a6a9695866a09c8b51d`

## Official maize regression case

The formal software regression case is the upstream DSSAT maize installation test:

- Experiment: `Maize/UFGA8201.MZX`
- Site: Irrigation Park, University of Florida, Gainesville
- Weather station: `UFGA`
- Weather file: `Weather/UFGA8201.WTH`
- Soil profile referenced by experiment: `IBMZ910014`
- Cultivar: `IB0035 McCurdy 84aa`
- Treatments: 6

The upstream data README explicitly instructs users to test a CSM installation with:

```text
path+executable A UFGA8201.MZX
```

from the Maize directory and states that the run should generate `Summary.OUT`, `PlantGro.OUT`, and other outputs for six treatments.

## Formal comparison rule

1. Build and execute the untouched upstream source/data first (`M0_OFFICIAL_485`).
2. Freeze build/run metadata and hashes of the official outputs.
3. Create the HTEMP modification only after M0 passes end-to-end.
4. M10 and all later candidates must use the exact same compiler/runtime, source baseline, data baseline, experiment, management, soil, genotype, and weather unless an explicitly documented Urumqi experiment replaces the Florida regression case.
5. The Florida case is a software-regression test, not evidence for Urumqi agronomic improvement.
6. Urumqi scientific validation remains a separate stage using Urumqi weather and public maize observations.

## Why v4.8.5.0

The choice is deliberate for reproducibility and project continuity. The study does not claim that v4.8.5.0 is the newest DSSAT release; it is the frozen reference implementation against which the local HTEMP change is evaluated.
