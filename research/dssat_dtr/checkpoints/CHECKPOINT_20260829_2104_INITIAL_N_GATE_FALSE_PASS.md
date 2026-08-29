# CHECKPOINT 2026-08-29 21:04 CST — Initial-N model-read audit false PASS withdrawn

## Finding

The first `Shihezi Initial N Model Read Audit` completed and its script labeled the distinct-value gate PASS. Direct inspection of the preserved raw consolidated input shows that this PASS criterion was inadequate.

Example MINN30:

Intended FileX row:

```text
1 20 0.237 0.95 0.95
```

DSSAT consolidated `DSSAT48.INP` actually contains rows such as:

```text
5. 0.237 0.00 50.00
15. 0.237 0.00 50.00
20. 0.237 0.00 50.00
```

For the five target scenarios the earlier README reported implausible model-read pairs such as:
- written 0.952 / 0.952 -> apparent 0 / 50;
- written 1.904 / 1.904 -> apparent 1 / 31;
- written 2.855 / 2.855 -> apparent 2 / 62.

Therefore the values were distinct but not equal to the intended SNH4/SNO3 inputs.

## Root cause

The V4 source FileX uses DSSAT fixed columns for initial conditions, e.g.:

```text
 1    20  .237    1.0    1.0
```

Field structure is approximately:
- factor: width 2;
- ICBL: width 6;
- SH2O: width 6;
- SNH4: width 7;
- SNO3: width 7.

The V1 diagnostic rewrote the row with variable spacing and a leading zero in SH2O, shifting fixed-column boundaries. DSSAT consequently parsed the intended N numbers incorrectly.

## Scientific consequence

Withdraw all 30/60/90/120/150 kg/ha initial-mineral-N sensitivity results from scientific interpretation. The observed plateaus/nonmonotonic jumps were produced under malformed model-read initial N.

## Correction

Redo the model-read gate with exact-width rows:

```text
factor(2) + ICBL(6) + SH2O(6) + SNH4(7) + SNO3(7)
```

and require, for every target:
1. generated DSSAT48.INP SNH4 matches written SNH4 within rounding tolerance;
2. generated SNO3 matches written SNO3 within rounding tolerance;
3. all five targets remain ordered in the intended direction;
4. only after these checks pass may a corrected sensitivity be interpreted.

No scientific parameter changes are involved.
