# Flash Drought Resilience Reproduction

Reproduction workspace for:

> Guo, R., Wu, X., Wang, P. et al. (2026). **Increased spread of global flash droughts threatens vegetation productivity resilience.** *Nature Communications*, 17, 4050. DOI: 10.1038/s41467-026-70417-z.

Official code capsule: https://doi.org/10.24433/CO.0939560.v1

## Purpose

This project is deliberately organized in two layers:

1. **Author-package reproduction**: obtain the official Source Data, Supplementary Information and Code Ocean capsule, preserve them with provenance, and reproduce the paper's published figures/results before changing any method.
2. **Method learning / independent reconstruction**: only after the author package is verified, rebuild the main pipeline from upstream public datasets (ERA5-Land, GLDAS_CLSM, FluxSat, CSIF, CMIP6, etc.).

The first target is a low-risk reproducibility pass. No claim of exact reproduction is allowed until the official code/data package has been imported and its outputs have been compared against the paper.

## Current state

See [`docs/REPRODUCTION_STATUS.md`](docs/REPRODUCTION_STATUS.md).

Current initialization includes:

- paper logic and method map derived from the supplied Version of Record PDF;
- a data/provenance manifest with official URLs;
- a figure-to-input/method/output reproduction matrix;
- a staged run order designed to minimize unnecessary global-data downloading;
- scripts for fetching/verifying official Springer Nature assets once run in a network-enabled environment;
- explicit unresolved-method questions that must be answered from the Code Ocean capsule / Supplementary Information before independent implementation.

The Code Ocean binary package and Nature Source Data are **not yet mirrored into this public repository**. Their contents and licensing must be verified first; the current execution environment also cannot directly materialize those remote binary assets. This is tracked as a blocking item rather than silently substituted with guessed files.

## Repository layout

```text
paper/
  PAPER_LOGIC.md
  PAPER_METHODS_MAP.md

docs/
  RUN_ORDER.md
  FIGURE_REPRODUCTION_MATRIX.md
  REPRODUCTION_STATUS.md
  KNOWN_UNCERTAINTIES.md
  LICENSE_AND_PROVENANCE.md

data/
  DATA_MANIFEST.md

scripts/
  fetch_official_assets.py
  verify_official_assets.py

vendor/nature/README.md
vendor/codeocean/README.md
```

## Reproduction gate

- **G0 AUTHOR_ASSETS_VERIFIED**: Supplementary + Source Data + Code Ocean capsule obtained, hashes recorded, license/provenance checked.
- **G1 AUTHOR_RUN_REPRODUCED**: official capsule runs and at least the principal numeric outputs/figures match the paper within expected tolerance.
- **G2 CORE_METHOD_REBUILT**: flash/slow drought event identification, MFDI/hotspots and resilience reconstructed independently from upstream data.
- **G3 ATTRIBUTION_REBUILT**: four RF attribution models + permutation importance + partial dependence reproduced.
- **G4 CMIP6_REBUILT**: future SSP2-4.5 analysis reproduced from the eight retained CMIP6 models.

Do not jump from G0 to G3/G4 merely because scripts execute.
