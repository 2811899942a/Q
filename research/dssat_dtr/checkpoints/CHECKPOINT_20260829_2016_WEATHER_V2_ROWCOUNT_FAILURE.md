# CHECKPOINT 2026-08-29 20:16 CST — Weather-gap V2 row-count gate failure

## Status

GitHub Actions run `33251367639` completed with failure before any weather-sensitivity result was accepted.

## Exact failure

The audited V2 workflow stopped at:

```text
RuntimeError: Only 184 WTH rows changed in /tmp/weather_v2_RAIN_MATCH/Weather/SHIH1901.WTH
```

The V4-reconstructed Shihezi WTH file contains 184 valid daily data records. The V2 workflow used an arbitrary engineering guard requiring at least 300 rows, so it rejected a structurally valid 184-day weather file before the M0 scenario comparison began.

## Scientific consequence

- No weather-effect result is produced by this failed V2 run.
- The failure says nothing about rainfall or solar-radiation sensitivity.
- Existing V1 weather scenarios remain withdrawn from attribution because their requested edits never appeared in `Summary.OUT`.

## Correction

Replace the arbitrary `>=300` guard with a structural invariant:

1. BASE WTH valid-row count is read first for each year.
2. Each edited scenario must retain exactly the same valid-row count as its BASE WTH.
3. Edited scenario hash must differ from BASE when a change is requested.
4. The active `/DSSAT48/Weather/...` file hash must equal the audited scenario file hash.
5. After DSSAT execution, `Summary.OUT` SRADA/PRCP must move consistently with the requested WTH modification; otherwise the run fails.

This gives a stronger and data-driven propagation audit without assuming a calendar-length weather file.

## Next action

Patch the workflow and rerun immediately. No scientific parameter, M15 coefficient, Xinyu66 coefficient, or crop-management value is changed.
