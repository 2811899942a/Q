# Reproduction Status

Last initialized: 2026-09-03

## Gate summary

| Gate | State | Evidence |
|---|---|---|
| G0 AUTHOR_ASSETS_VERIFIED | BLOCKED | official URLs identified; remote binary assets/capsule not materialized in current runtime; capsule rehosting license not yet verified |
| G1 AUTHOR_RUN_REPRODUCED | NOT_STARTED | requires G0 |
| G2 CORE_METHOD_REBUILT | NOT_STARTED | requires exact implementation details from G0/G1 |
| G3 ATTRIBUTION_REBUILT | NOT_STARTED | requires G2 + processed predictors |
| G4 CMIP6_REBUILT | NOT_STARTED | later stage |

## Completed initialization checks

- PASS: correct paper identified: Nature Communications 17:4050 (2026), DOI `10.1038/s41467-026-70417-z`.
- PASS: supplied PDF inspected and key figures/method pages visually checked.
- PASS: official paper states Source Data are provided with the article.
- PASS: official paper states main-result code is at Code Ocean DOI `10.24433/CO.0939560.v1`.
- PASS: direct official Springer Nature URLs for Supplementary Information and Source Data have been identified and encoded in the fetch script.
- PASS: data/method/figure/run-order documentation initialized.
- PASS: uncertainties that would otherwise invite guessing are explicitly logged.

## Current blockers

1. Current execution runtime cannot directly materialize the remote Springer binary attachments; DNS/download access is unavailable from the container and the browser retrieval interface exposes the link but not the binary file bytes.
2. Code Ocean DOI/capsule cannot be materialized through the currently available download interface, so the capsule's explicit license and complete file tree remain unverified.
3. Because repository `2811899942a/Q` is public, author files will not be blindly mirrored until capsule/source-data redistribution terms are confirmed.

## Next executable action

Run `scripts/fetch_official_assets.py` from a normal network-enabled machine (or Codex host), export the Code Ocean capsule from its public page, then place/export it according to `vendor/codeocean/README.md`. Immediately compute hashes and update G0.
