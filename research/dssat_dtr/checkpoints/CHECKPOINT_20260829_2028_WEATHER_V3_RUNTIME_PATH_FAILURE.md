# CHECKPOINT 2026-08-29 20:28 CST — Weather-gap V3 runtime-path failure

## Status

Workflow: `Shihezi M0 Weather Gap Diagnostic V3`
Run: `33251591460`
Conclusion: engineering failure at the post-run propagation gate; no weather sensitivity result accepted.

## What V3 successfully proved

V3 fixed the previous arbitrary 300-row guard. The canonical Shihezi V4 model rebuilt successfully, and the scenario WTH files retained the exact valid-row count of the BASE files. The workflow also created independent physical scenario roots and audited the active `/DSSAT48/Weather/...` file path/hash before execution.

Thus the requested WTH files were physically modified and present at the path that the workflow expected to be active.

## Exact failure

After DSSAT execution, the hard propagation gate stopped the workflow with:

```text
RuntimeError: POST-RUN FAIL: RAIN_MATCH PRCP unchanged for 2019
```

The same phenomenon seen in weather V1 therefore persists: the edited rainfall file is visible in the scenario filesystem, while `Summary.OUT` still reports the BASE crop-period precipitation.

## Most likely engineering cause

The DSSAT installation produced by CMake can retain installation-prefix paths in `DSSATPRO.v48`. The canonical M0 installation prefix is `/tmp/run_M0`. Copying that installed tree to `/tmp/weather_v2_*` can leave path configuration still pointing to the original `/tmp/run_M0/Weather`, even when `/DSSAT48` itself points to the copied scenario root.

This is a runtime-path hypothesis and will be directly audited in V4. It is not treated as established until `DSSATPRO.v48` is inspected during the run.

## Scientific consequence

- RAIN_MATCH, SRAD_19P8 and WEATHER_BOTH still have no valid crop-response result.
- The unchanged PRCP does not support a conclusion of rainfall insensitivity.
- No M0/H0TT/M15TT accuracy claim changes.

## V4 correction

Eliminate copied-install path ambiguity entirely:

1. rebuild the canonical `/tmp/run_M0` installation;
2. save original `/tmp/run_M0/Weather/SHIH1901.WTH` and `SHIH2001.WTH` bytes;
3. inspect and save the active DSSATPRO weather/path configuration;
4. for each weather scenario, restore the original files and edit the canonical `/tmp/run_M0/Weather/...` files **in place**;
5. audit hash, valid-row count, SRAD mean and rainfall total immediately before DSSAT execution;
6. keep `/DSSAT48 -> /tmp/run_M0` throughout;
7. run M0 and require `Summary.OUT` SRADA/PRCP to change in the requested direction;
8. restore the original WTH files after the diagnostic.

This design guarantees that even an absolute `/tmp/run_M0/Weather` path inside DSSATPRO sees the edited file.

## Frozen rules

No crop, genotype, M15, irrigation, nitrogen, soil or observed-yield value changes in this correction.
