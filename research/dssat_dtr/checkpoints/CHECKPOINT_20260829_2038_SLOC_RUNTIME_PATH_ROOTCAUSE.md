# CHECKPOINT 2026-08-29 20:38 CST — SLOC runtime-path root cause

## What the dedicated SLOC audit found

Run `33251858968` completed successfully and preserved both the edited soil files and DSSAT's consolidated `DSSAT48.INP`.

The generated LOWOM/HIGHOM `SH.SOL` files are different, yet:

- LOWOM HWAM = 8339 kg/ha;
- HIGHOM HWAM = 8339 kg/ha;
- NI#M/NICM/NUCM/NLCM/NMINC are identical;
- `LOWOM_DSSAT48.INP` and `HIGHOM_DSSAT48.INP` are byte-identical;
- DSSAT48.INP diff length = 0.

## Exact model-read evidence

The consolidated DSSAT input states:

```text
SOILS          SH.SOL       ///tmp/run_M0/Soil/
```

although the LOWOM/HIGHOM diagnostic executions were launched from copied scenario roots.

This confirms the copied DSSAT installation retained the canonical CMake installation prefix and continued reading the soil file from `/tmp/run_M0/Soil/SH.SOL`.

There is a second formatting issue in the canonical custom soil profile: DSSAT48.INP shows `SLOC=-99.0` in the model-read soil layers even though the text `SH.SOL` contains numeric SLOC values. The custom whitespace layout does not satisfy DSSAT's fixed-column soil parser for SLOC. The consolidated site longitude is also visibly malformed (`485.990`), further confirming fixed-column alignment problems in the custom soil text.

## Scientific consequence

The previous LOWOM/HIGHOM zero-response result cannot be interpreted as biological insensitivity to soil organic carbon. The requested SLOC perturbation did not enter DSSAT's model-read soil state.

All LOWOM/HIGHOM OM sensitivity results are therefore classified as **engineering-invalid for OM attribution** until the canonical soil file is corrected and `DSSAT48.INP` proves that SLOC changed.

## One-time correction

A corrected audit must:

1. edit the canonical `/tmp/run_M0/Soil/SH.SOL` in place, avoiding copied-install path ambiguity;
2. write the soil profile using official DSSAT v4.8.5 fixed-width columns, patterned after official `.SOL` files;
3. repair SITE latitude/longitude alignment at the same time;
4. run LOWOM and HIGHOM with identical management;
5. require `DSSAT48.INP` to contain the requested numeric SLOC values and different LOWOM/HIGHOM consolidated soil blocks;
6. only after that gate passes, compare nitrogen state and HWAM.

No crop, temperature, genotype, irrigation or fertilizer parameter changes are allowed in this correction.
