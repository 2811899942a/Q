# Code Ocean access audit - 2026-09-03

## Official citation

The Version of Record explicitly states that the code used to generate the main results is deposited at:

`https://doi.org/10.24433/CO.0939560.v1`

This DOI is therefore retained as the canonical citation in provenance records.

## Access status

- User-side access to the DOI resolver currently returns **HTTP 403**.
- The current ChatGPT web retrieval path also cannot materialize the DOI/capsule.
- Exact-DOI GitHub code search returned no verified mirror of the capsule.
- Broader prior searches by exact DOI/title did not identify a verified alternate public archive that can be treated as the author's capsule.

Status: **EXTERNAL_ACCESS_BROKEN**.

The DOI citation is real because it is printed in the published article. Reachability of the cited Code Ocean object is currently insufficient for reproduction. These are separate facts and must be recorded separately.

## Important Code Ocean identifier rule

Do **not** infer a public Code Ocean capsule URL by inserting `0939560` into a `/capsule/<id>/...` URL. Code Ocean DOI identifiers and public capsule URL identifiers are not guaranteed to be the same. Guessing such a URL would create false provenance.

## Reproduction policy change

The inaccessible Code Ocean capsule is no longer a hard prerequisite for the independent method rebuild.

Two tracks are now separated:

### Track A - author-package rerun

State: `BLOCKED_EXTERNAL` until the Code Ocean capsule becomes reachable or the authors provide the code by another verified route.

Purpose: exact author-script/environment rerun.

### Track B - independent reconstruction

State: `READY_TO_START`.

Grounding already available:

- Version of Record;
- official Supplementary Information;
- official Reporting Summary;
- official Transparent Peer Review;
- official 45-sheet Source Data workbook;
- machine-readable paper parameters and numerical smoke targets in this repository.

Track B may proceed with GEE/source-side preprocessing while preserving unresolved implementation details as explicit sensitivity/verification items.

## Real data sources for Track B

### 1. Nature Source Data - already obtained

`41467_2026_70417_MOESM4_ESM.xlsx`

Role: authoritative published source values for figures/statistical comparisons. This is the first validation target for every reconstructed module.

### 2. ERA5-Land - GEE preferred

Earth Engine collection:

`ECMWF/ERA5_LAND/DAILY_AGGR`

Role: 1950-2023 climate variables and the three soil-water layers. GEE performs the paper's 0-1 m weighting and 1-degree reduction server-side.

### 3. GLDAS CLSM - exact historical chain requires care

NASA historical daily Catchment LSM product identified for the long historical segment:

`GLDAS_CLSM025_D.2.0`

Documented historical coverage reaches from 1948 into 2014. The paper claims a GLDAS_CLSM contribution through 2023, so the continuation after the GLDAS-2.0 segment must remain an explicit unresolved dataset-stitching item until a verified author/source definition is recovered.

Do not substitute the convenient GEE GLDAS-2.2 CLSM product beginning in 2003 for the full 1950-2023 paper chain without a documented validation experiment.

Preferred handling: NASA GES DISC server-side subset/OPeNDAP for the required soil-moisture/SWE fields, reduced before local transfer.

### 4. Other inputs

Use the exact source links listed in `data/DATA_MANIFEST.md`: FluxSat GPP, CSIF, FLUXNET2015, MCD12C1, HWSD, canopy height, rooting depth, tree density, NOAA CO2 and the eight retained CMIP6 SSP245 `mrso` models.

## Scientific claim policy

Until Track A becomes possible:

- `AUTHOR_RUN_REPRODUCED` cannot be marked PASS.
- `CORE_METHOD_REBUILT` can be evaluated independently against Nature Source Data and published targets.
- Any code-dependent convention that cannot be uniquely recovered must be reported as a sensitivity branch, not silently guessed.

This preserves reproducibility without allowing an inaccessible third-party capsule to stop all progress.
