# CHECKPOINT 2026-08-29 20:25 CST — SLOC cache-clean V3 engineering failure

## Run

Workflow: `Shihezi Soil SLOC Cache Clean V3`
Run: `33252302371`
Status: FAIL before LOWOM/HIGHOM DSSAT comparison.

## Exact failure

The V3 wrapper attempted to inject cache deletion into the fixed-width V2 Python script and produced:

```text
IndentationError: unexpected indent
```

The canonical V4 reconstruction completed before this error. No SLOC sensitivity result was generated.

## Stronger runtime-path correction

Review of the prior model-read audit shows copied DSSAT installations retain absolute canonical paths such as:

```text
SOILS SH.SOL ///tmp/run_M0/Soil/
```

Therefore deleting cache files inside a copied scenario root is insufficient: the executable can still read the unmodified canonical soil file.

The next audit will avoid copied roots completely:

1. keep `/DSSAT48 -> /tmp/run_M0`;
2. save the original canonical `/tmp/run_M0/Soil/SH.SOL` and W2 FileX;
3. write fixed-column LOWOM or HIGHOM SLOC directly into canonical `SH.SOL`;
4. remove every canonical `DSSAT48.INP` before each run;
5. run the same W2/N129 case;
6. require INFO.OUT / consolidated input to show different model-read organic carbon in the intended direction;
7. restore canonical inputs after each comparison.

This is an input-path correction only. M15, Xinyu66, weather, irrigation and N total are unchanged.
