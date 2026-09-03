# Source Data audit

Official file audited: `41467_2026_70417_MOESM4_ESM.xlsx`.

## Workbook structure

- 45 worksheets.
- 0 Excel formula cells detected.
- 0 external workbook links detected.
- 0 defined names detected.
- Values are therefore suitable for independent numerical validation without relying on Excel recalculation.

### Main-figure sheets

`Figure1a-c`, `Figure1d-f`, `Figure1g-i`, `Figure2a`, `Figure2b`, `Figure2c`, `Figure3a`, `Figure3b`, `Figure4a`, `Figure4b-k`, `Figure5a`, `Figure5b-k`.

### Supplementary sheets

The workbook contains source values for S1-S15, S17, S19, S21 and Tables S1-S2. Schematic-only figures such as S16/S18/S20 do not require numeric source sheets.

## Independent checks already completed

### Fig. 1 interannual trends

Using ordinary least-squares slopes on the 74 yearly source values (1950-2023) in `Figure1g-i` gives:

| Metric | OLS slope from Source Data | Published rounded slope |
|---|---:|---:|
| flash-drought count anomaly | 6.6290 yr-1 | 6.63 yr-1 |
| severity anomaly | 0.01211 %-points yr-1 | 0.01 yr-1 |
| onset-speed anomaly | 0.01836 %-points pentad-1 yr-1 | 0.02 yr-1 |

This is a strong source-value consistency check. The published significance values use Mann-Kendall/Sen statistics rather than the OLS fit alone.

`FigureS1` independently contains both flash and slow drought annual series. Its flash-drought series yields the same OLS slopes as the main Fig. 1 anomaly sheets after centering.

### Fig. S2 flash-drought ratio

The 1950-2023 ratio-anomaly source series yields an OLS slope of approximately **0.1361 percentage points yr-1**. The paper reports a Sen slope of about **0.142**, so the difference is expected because the estimators are different.

### Fig. S15 CMIP6 screening

The Source Data provide the exact Taylor-diagram inputs for nine candidates:

- `STD`;
- `RMSD`;
- `COR`.

`CMCC-CM2-SR5` has the largest supplied STD (about 9.709) and RMSD (about 6.351), even though its correlation is high (about 0.821). The final paper excludes this model and retains the other eight. The source values are consistent with that stated screening rationale.

### Fig. S21 VIF

The `FigureS21a` sheet stores VIF values for the 15 final predictors under four RF models. All supplied final values are below 5, consistent with the Methods statement that factors with `VIF > 5` were removed.

The largest values among the retained predictors are associated with radiation and VPD in several configurations; this confirms that the final set can still be correlated while satisfying the authors' stated threshold.

### Fig. S21 RF accuracy source values

`FigureS21b-e` stores observed and RF-estimated GPP resilience for four model groups, with sample sizes matching the Supplementary caption:

- flash drought / hotspots: n=437;
- slow drought / hotspots: n=486;
- flash drought / non-hotspots: n=370;
- slow drought / non-hotspots: n=722.

Simple SSE-based R2 values computed directly from these pairs are approximately 0.681-0.713, while squared correlations are approximately 0.825-0.854. The exact accuracy metric displayed in the figure must therefore be read from the author plotting/model code rather than assumed from the plotted pairs.

## MFDI reverse-engineering status

The workbook provides all four grid-level MFDI ingredients:

- flash drought ratio (`FigureS2a`);
- count (`Figure1a-c`);
- severity (`Figure1a-c`);
- onset speed (`Figure1a-c`);

and the published grid-level MFDI (`FigureS4a`).

A straightforward literal implementation of Eqs. 3-7 using global mean/SD, positive T-score orientation and `MFDI = Mz + Sz*cv` produces a result highly correlated with the supplied MFDI (correlation ~0.98) but does **not** match it exactly (mean absolute error ~3.8 index units). This means at least one implementation detail is absent from the compact printed equations or involves preprocessing/clipping/masking conventions.

Therefore:

- do not publish an independently reconstructed MFDI as exact;
- use Source Data for figure-level reproduction now;
- wait for Code Ocean to resolve exact MFDI preprocessing.

This is an example where source-value reverse engineering narrows the uncertainty without pretending the missing implementation step is known.

## What Source Data can reproduce without raw climate archives

The workbook is sufficient to reconstruct or validate much of the **published presentation layer**:

1. Fig. 1 source-value maps/distributions/time series;
2. Fig. 2 hotspot mask, MFDI distributions and trends;
3. Fig. 3 resilience difference/map and grouped distributions;
4. Fig. 4-5 feature-importance points and partial-dependence curves;
5. most Supplementary numerical plots;
6. Tables S1-S2;
7. Taylor-diagram source metrics;
8. VIF and RF accuracy checks.

It is not sufficient to independently regenerate:

- ERA5-Land + GLDAS soil-moisture pentads;
- event catalogues;
- GPP/SIF anomaly histories and recovery-event selection;
- the fitted RF objects;
- BEAST turning points;
- future CMIP6 soil-moisture event detection.

Those belong to Code Ocean / upstream-data reconstruction stages.
