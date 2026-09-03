# Codex handoff - Flash drought reproduction

This file is the local execution entry point once Codex quota is available.

## Objective

Reproduce Guo et al. (2026), *Nature Communications* 17:4050 with minimum unnecessary data download. First reproduce the author package, then independently rebuild only the method blocks worth learning.

## Current verified state

- Nature Supplementary Information: obtained and SHA256 locked.
- Nature Reporting Summary: obtained and SHA256 locked.
- Nature Transparent Peer Review: obtained and SHA256 locked.
- Nature Source Data XLSX: obtained, 45 sheets audited, SHA256 locked.
- Code Ocean DOI identified: `10.24433/CO.0939560.v1`.
- Code Ocean capsule archive: **still required**.
- GitHub already contains paper logic, method map, parameter lock, figure matrix, uncertainty ledger, Source Data checks and provenance documentation.

Read first:

1. `README.md`
2. `docs/REPRODUCTION_STATUS.md`
3. `docs/AUTHOR_ASSET_AUDIT_20260903.md`
4. `docs/PEER_REVIEW_METHOD_CLARIFICATIONS.md`
5. `docs/SOURCE_DATA_AUDIT.md`
6. `docs/KNOWN_UNCERTAINTIES.md`
7. `config/paper_parameters.json`
8. `docs/RUN_ORDER.md`

## Local root

Recommended:

```text
D:\FlashDrought_Guo2026_Reproduction\
```

Do not alter or delete the original user-downloaded Nature files. Maintain a read-only original-assets area and a separate working area.

## Task C0 - establish repository and assets

1. Clone/pull `2811899942a/Q`.
2. Work from `projects/flash-drought-resilience-reproduction`.
3. Place the four official Nature files in a local `00_author_assets\nature\` directory.
4. Run:

```powershell
python scripts\verify_official_assets.py --dir D:\FlashDrought_Guo2026_Reproduction\00_author_assets\nature
python scripts\audit_source_data.py D:\FlashDrought_Guo2026_Reproduction\00_author_assets\nature\41467_2026_70417_MOESM4_ESM.xlsx
python scripts\source_data_smoke.py D:\FlashDrought_Guo2026_Reproduction\00_author_assets\nature\41467_2026_70417_MOESM4_ESM.xlsx
```

Acceptance:

- exact Nature hashes PASS;
- workbook opens with 45 worksheets;
- source-data smoke checks PASS.

## Task C1 - obtain and freeze Code Ocean capsule

Open:

```text
https://doi.org/10.24433/CO.0939560.v1
```

Download/export the complete capsule, including environment metadata and process data if Code Ocean exposes them.

Preserve:

```text
00_author_assets\codeocean\CO.0939560.v1_original.*
```

Then create a recursive manifest containing:

- relative path;
- size;
- SHA256;
- extension;
- detected text/binary type.

Do not rename internal files before the manifest is captured.

## Task C2 - capsule audit before running

Identify:

- MATLAB scripts/functions;
- main entry script(s);
- input data directories;
- process/intermediate data already bundled;
- outputs expected by the authors;
- MATLAB toolbox dependencies;
- random seeds or `rng` calls;
- BEAST package/function;
- RF implementation/function and exact terminal-node/leaf parameter;
- MFDI implementation;
- percentile/calendar implementation;
- PDP confidence interval implementation;
- CMIP6 calendar handling.

Create a table:

```text
script | purpose | inputs | outputs | figure(s) | dependencies | runnable now? | blocker
```

Use this audit to update `docs/KNOWN_UNCERTAINTIES.md`. Do not infer missing parameters.

## Task C3 - smallest official rerun

Before any global raw-data download, locate the smallest author workflow that can run using bundled process data.

Priority:

1. Fig. 1 source/result generation;
2. Fig. 2 hotspot/MFDI result generation;
3. Fig. 3 resilience;
4. Fig. 4/5 RF/PDP.

For each successful target record:

- command/script;
- MATLAB version/toolboxes;
- runtime;
- input hashes;
- output hashes;
- numerical comparison against Source Data;
- visual comparison against paper;
- PASS/FAIL with tolerance.

## Task C4 - produce minimal upstream download list

Only after capsule audit, determine what is genuinely absent.

Do not bulk-download ERA5-Land/GLDAS/FluxSat/CMIP6 merely because the paper names them. If the capsule already contains processed 1-degree/pentad input, first reproduce the paper from that processed layer.

The eventual independent-rebuild list should specify exact:

- product short name/version;
- variable;
- time range;
- spatial range;
- temporal frequency;
- file naming pattern;
- expected data volume;
- authentication method;
- script that consumes it.

## Task C5 - GitHub return package

Do not commit large raw NetCDF/HDF/MAT archives.

Return to GitHub only auditable lightweight artifacts:

- capsule file manifest (CSV/JSON);
- environment/toolbox manifest;
- resolved method notes;
- run logs;
- figure comparison metrics;
- small CSV/Parquet event summaries;
- selected reproduced figures if redistribution/size permits;
- download scripts/query files;
- updated status/gates.

## Hard rules

1. No claim of exact reproduction from Source Data plotting alone.
2. No silent replacement of MATLAB parameters with Python/sklearn analogues.
3. If Version of Record and peer review conflict, inspect author code.
4. No raw-data mass download before capsule inventory.
5. No declaring G1 PASS solely because scripts run; outputs must be compared against Source Data/paper.
6. Preserve original author assets and hashes.
7. Errors should be diagnosed from first principles; do not repeatedly patch a broken pipeline when the author package can clarify the intended process.
