# Flash Drought Resilience Reproduction

Reproduction workspace for:

> Guo, R., Wu, X., Wang, P. et al. (2026). **Increased spread of global flash droughts threatens vegetation productivity resilience.** *Nature Communications*, 17, 4050. DOI: 10.1038/s41467-026-70417-z.

Official code capsule: https://doi.org/10.24433/CO.0939560.v1

## Strategy

The project is deliberately split into two layers:

1. **Author-package reproduction**: use the official Supplementary Information, Source Data and Code Ocean process data/code to reproduce the paper before changing any method.
2. **Independent method reconstruction**: after the author package is understood, rebuild selected parts from upstream public datasets (ERA5-Land, GLDAS_CLSM, FluxSat, CSIF, CMIP6, etc.).

This design keeps the first reproduction pass low risk and prevents unnecessary global-data downloads.

## Current state - 2026-09-03

The user has supplied the full set of Springer Nature article assets:

- Supplementary Information;
- Reporting Summary;
- Transparent Peer Review;
- Source Data XLSX.

All four were audited, byte sizes and SHA256 hashes were recorded, and Source Data were structurally/numerically checked. See:

- [`docs/AUTHOR_ASSET_AUDIT_20260903.md`](docs/AUTHOR_ASSET_AUDIT_20260903.md)
- [`docs/PEER_REVIEW_METHOD_CLARIFICATIONS.md`](docs/PEER_REVIEW_METHOD_CLARIFICATIONS.md)
- [`docs/SOURCE_DATA_AUDIT.md`](docs/SOURCE_DATA_AUDIT.md)
- [`docs/REPRODUCTION_STATUS.md`](docs/REPRODUCTION_STATUS.md)

The remaining author-package blocker is the **Code Ocean capsule itself**. The Nature assets establish `G0A=PASS`; Code Ocean is still required for exact executable details and `G0B`.

Important findings already recovered before Codex/local execution:

- Reporting Summary confirms the formal analysis/visualization environment as **MATLAB R2020b**.
- Peer review clarifies that soil-moisture pentads were converted to percentiles after **deseasonalization and detrending**.
- Peer review clarifies the GPP growing-season rule and the tropical year-round threshold.
- Peer review clarifies OOB permutation importance and RF split sampling.
- A Version-of-Record/peer-review RF hyperparameter conflict was identified (`5 leaves` vs `minimum terminal node size=5`) and is intentionally left for author-code resolution.
- Source Data contain 45 worksheets, no formulas/external links, and support direct numerical checks of Fig. 1, Fig. S15 and Fig. S21.
- Literal reverse engineering of MFDI from printed equations reaches high correlation with published Source Data but does not match exactly; an implementation convention is still missing and will not be guessed.

## Repository layout

```text
config/
  paper_parameters.json

paper/
  PAPER_LOGIC.md
  PAPER_METHODS_MAP.md

docs/
  AUTHOR_ASSET_AUDIT_20260903.md
  PEER_REVIEW_METHOD_CLARIFICATIONS.md
  SOURCE_DATA_AUDIT.md
  RUN_ORDER.md
  FIGURE_REPRODUCTION_MATRIX.md
  REPRODUCTION_STATUS.md
  KNOWN_UNCERTAINTIES.md
  LICENSE_AND_PROVENANCE.md
  LOCAL_DOWNLOAD_CHECKLIST.md
  CODEX_HANDOFF.md

data/
  DATA_MANIFEST.md

scripts/
  fetch_official_assets.py
  verify_official_assets.py
  audit_source_data.py
  source_data_smoke.py

vendor/nature/README.md
vendor/codeocean/README.md
requirements.txt
```

## Immediate local smoke checks

Once the four Nature files are in a local directory:

```powershell
pip install -r requirements.txt
python scripts\verify_official_assets.py --dir D:\FlashDrought_Guo2026_Reproduction\00_author_assets\nature
python scripts\audit_source_data.py D:\FlashDrought_Guo2026_Reproduction\00_author_assets\nature\41467_2026_70417_MOESM4_ESM.xlsx
python scripts\source_data_smoke.py D:\FlashDrought_Guo2026_Reproduction\00_author_assets\nature\41467_2026_70417_MOESM4_ESM.xlsx
```

## Reproduction gates

- **G0A NATURE_ASSETS_VERIFIED**: PASS.
- **G0B CODE_OCEAN_CAPSULE_VERIFIED**: capsule obtained, hashes/file tree/environment/license inspected.
- **G1 AUTHOR_RUN_REPRODUCED**: official author workflow runs and principal numeric/figure outputs match Source Data/paper within documented tolerance.
- **G2 CORE_METHOD_REBUILT**: flash/slow event identification, MFDI/hotspots and resilience independently reconstructed.
- **G3 ATTRIBUTION_REBUILT**: four RF models + permutation importance + PDP reproduced.
- **G4 CMIP6_REBUILT**: SSP2-4.5 future analysis reproduced from the eight retained CMIP6 models.

Do not jump from Source Data plotting to a claim of full reproduction.

## Codex handoff

When local Codex execution starts, use [`docs/CODEX_HANDOFF.md`](docs/CODEX_HANDOFF.md) as the entry point. The first local task is to export and inventory Code Ocean, not to bulk-download ERA5-Land/GLDAS/CMIP6.
