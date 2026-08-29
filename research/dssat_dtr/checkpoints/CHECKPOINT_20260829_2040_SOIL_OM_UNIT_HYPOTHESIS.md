# CHECKPOINT 2026-08-29 20:40 CST — Soil organic-matter unit/decimal inconsistency identified

## New source inconsistency
Guo (2025) Table 2-1 labels soil organic matter as `g/kg` and reports layer values:
- 0–20 cm: 1.485
- 20–40 cm: 1.410
- 40–60 cm: 1.264
- 60–80 cm: 1.307
- 80–100 cm: 1.022

If interpreted literally, topsoil OM is only 1.485 g/kg (=0.1485% OM), extremely low for this cultivated Shihezi field.

A later public experiment from the **same Shihezi University modern water-saving irrigation station** and the **same cultivar Xinyu66** reports pre-sowing topsoil organic matter = **14.12 g/kg** in 2021. A roughly ten-fold natural increase between the 2019–2020 trial and 2021 is agronomically implausible.

## Working hypothesis
The Guo table may contain a unit/decimal mismatch: values such as `1.485` may represent **percent organic matter**, equivalent to 14.85 g/kg, rather than 1.485 g/kg.

Under this interpretation, DSSAT organic carbon for the top layer is approximately:
`SLOC = 1.485% OM / 1.724 = 0.861% organic C`,
not the `0.0861%` organic C used in nitrogen diagnostic V2.

The same factor-of-ten applies to all layers.

## Why this matters
Nitrogen diagnostic V2 used literal `g/kg` interpretation and therefore extremely low soil organic carbon. This suppresses mineralization and can create excessive N stress, potentially explaining why even the N193 diagnostic still underpredicts observed yield (mean ~9.4 t/ha versus observed ~11.0 t/ha).

## Scientific status
This is a **source-supported root-cause hypothesis**, not a correction silently imposed on Guo's data. The exact 2019–2020 soil OM unit remains ambiguous because the paper itself labels g/kg.

## Next diagnostic
Run M0 2020 with all V2 inputs unchanged except compare two soil-OM interpretations under fixed, independently motivated N scenarios:
1. LOW_OM: Guo values interpreted literally as g/kg (current V2; SLOC ~0.086% top layer).
2. HIGH_OM: Guo numeric values interpreted as percent OM (SLOC ~0.861% top layer).

Use N129 (same-station later practice clue) and optionally N193 only as sensitivity brackets. Do NOT optimize OM or N to yield. Record NICM, NUCM, yield and RRMSE.

If HIGH_OM strongly improves M0 reproduction while remaining consistent with the independent 2021 same-field 14.12 g/kg measurement, prioritize the percent-OM interpretation for the next defensible reconstruction, but still label the source ambiguity explicitly.

## Other unresolved inputs
- exact 2019–2020 fertilizer management unavailable publicly;
- exact CMA 2019–2020 station weather still unrecovered; NOAA 51356 ends in 1997;
- first planting-date irrigation is omitted in current DSSAT schedule;
- exact initial soil water/mineral N remains unknown.

## Continuity rule
Checkpoint written before new diagnostic, as required by user.
