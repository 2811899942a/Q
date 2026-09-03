# Author Asset Audit - 2026-09-03

## Scope

The user supplied a ZIP containing the four Springer Nature article assets for Guo et al. (2026), *Nature Communications* 17:4050, DOI `10.1038/s41467-026-70417-z`.

The archive was inspected locally before any reproduction claims were made.

## Verified files

| File | Role | Size (bytes) | SHA256 | Audit state |
|---|---|---:|---|---|
| `41467_2026_70417_MOESM1_ESM.pdf` | Supplementary Information | 13,259,266 | `40f77c118e541b71b1c5eca8a979d1c6b14dc8ce008c23ea42de67be8948967b` | PASS |
| `41467_2026_70417_MOESM2_ESM.pdf` | Nature Portfolio Reporting Summary | 82,633 | `903c4a1a64f40d8a78a9eed562d5b87b7d004e29dd5b654596b329b7944d3a4a` | PASS |
| `41467_2026_70417_MOESM3_ESM.pdf` | Transparent Peer Review file | 5,479,393 | `085a5ed84a899436a3a1d3e6cd4eabb573e864cc8decc694284a15dddeb56ea7` | PASS |
| `41467_2026_70417_MOESM4_ESM.xlsx` | Source Data workbook | 5,429,017 | `1bbbe011e8ad7841703c3b80a5e815295b8aeb5ec8c216fba183eaad6a07c924` | PASS |

## Supplementary Information audit

- PDF opens and renders correctly.
- Length: 26 pages.
- Contains **Figure S1 through Figure S21** and **Table S1 through Table S3**.
- Critical methodological illustrations are present:
  - Fig. S15: CMIP6 model screening Taylor diagram;
  - Fig. S16: explicit flash/slow drought event-definition schematic;
  - Fig. S17: energy/water limitation, climate-zone and vegetation-type partitions;
  - Fig. S18: vegetation productivity recovery/resilience schematic;
  - Fig. S19: GPP/SIF growing-season length;
  - Fig. S21: VIF and random-forest model accuracy checks.
- Table S3 confirms the eight retained SSP245 CMIP6 models and `mrso`, `r1i1p1f1`.

## Reporting Summary audit

The Reporting Summary provides two important reproducibility facts:

1. all analyses and visualization were performed in **MATLAB R2020b**;
2. the authors state that the **main process data and code** are available through Code Ocean DOI `10.24433/CO.0939560.v1`.

It also describes the gridded data as public and states that the work is reproducible from the supplied datasets and code.

## Transparent Peer Review audit

The peer-review file is highly useful for reproduction because it records method clarifications that are more explicit than the final article. Key items are extracted separately in `PEER_REVIEW_METHOD_CLARIFICATIONS.md`.

A particularly important statement is that the authors supplied preprocessing code for producing aggregated pentad-mean soil moisture in the revised Code Ocean version. Therefore, independent reimplementation of that preprocessing should wait for the capsule audit when possible.

## Source Data workbook audit

- Workbook opens normally with `openpyxl`.
- **45 worksheets** are present.
- **0 formula cells** were detected: values are stored as source values rather than live Excel calculations.
- **0 external workbook links** and **0 defined names** were detected.
- The workbook includes source values for main figures, supplementary figures and Tables S1-S2.
- It includes large grid-level sheets with 12,036 data rows for several global maps.
- `FigureS15` contains the Taylor-diagram metrics for all nine candidate CMIP6 models.
- `FigureS21a` contains VIF values for the 15 random-forest candidate predictors under the four attribution models.
- `FigureS21b-e` contains observed and estimated GPP-resilience values used for RF accuracy evaluation.

The workbook is therefore sufficient for **source-value validation and figure-level numerical checks**, but it is not sufficient by itself to regenerate the upstream soil-moisture/GPP processing chain.

## Current gate consequence

`G0` is now split:

- `G0A_NATURE_ASSETS_VERIFIED = PASS`
- `G0B_CODE_OCEAN_CAPSULE_VERIFIED = BLOCKED`

The only major author-package item still absent is the Code Ocean capsule itself. Large upstream ERA5-Land/GLDAS/FluxSat/CMIP6 downloads should remain deferred until the capsule file tree is inspected.
