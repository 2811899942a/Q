# CHECKPOINT 2026-08-29 20:56 CST — Initial mineral-N V1 nonmonotonic response

## V1 completed

Workflow: `Shihezi M0 Initial Mineral N Diagnostic`
Run: `33253069980`
Status: engineering PASS; scientific interpretation held pending model-read audit.

Common diagnostic state:
- corrected canonical HIGHOM soil OC;
- SRAD ~19.8 MJ m-2 d-1;
- N193 fertilizer bracket;
- frozen Xinyu66 and irrigation;
- only FileX initial SNH4/SNO3 changed.

RRMSE results:

|Initial-N target kg/ha|2019 RRMSE %|2020 RRMSE %|
|---:|---:|---:|
|30|11.738|33.568|
|60|26.078|27.550|
|90|11.738|33.566|
|120|11.738|31.272|
|150|11.738|33.566|

## Why no scientific conclusion is allowed yet

The response is strongly nonmonotonic and contains exact plateaus:
- 2019 30/90/120/150 kg/ha all return mean HWAM 10784 kg/ha;
- 2020 30/90/150 kg/ha return essentially identical mean HWAM ~14540 kg/ha;
- the 60 kg/ha case returns ~8.16 t/ha and is close to the prior corrected HIGHOM + SRAD19P8 + N193 matrix output.

This pattern is inconsistent with a straightforward continuous initial-mineral-N sensitivity and is characteristic of a fixed-column/model-read issue or a different unit interpretation.

The V1 input audit proves only that the intended FileX values were written:
- 30 kg/ha target -> SNH4=SNO3 ~0.952
- 60 -> ~1.904
- 90 -> ~2.855
- 120 -> ~3.807
- 150 -> ~4.759

It did not preserve and verify DSSAT's consolidated model-read initial-condition values.

## Required next step

Run a dedicated model-read audit using 2020 W2 for all five values. For each scenario save:
1. edited FileX initial-condition section;
2. generated `DSSAT48.INP` initial-condition section;
3. Summary.OUT HWAM / NICM / NUCM / NMINC;
4. exact consolidated SNH4/SNO3 values and layer count.

No initial-N sensitivity conclusion or source-gap ranking change is allowed until that gate passes.
