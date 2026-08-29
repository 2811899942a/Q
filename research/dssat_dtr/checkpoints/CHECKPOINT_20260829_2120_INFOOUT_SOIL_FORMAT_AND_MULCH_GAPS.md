# CHECKPOINT 2026-08-29 21:20 CST — INFO.OUT exposes fixed-column soil error and missing plastic mulch

## New direct model-read evidence
The SLOC read-audit saved `LOWOM_INFO.OUT`, which reports exactly what frozen DSSAT v4.8.5 actually used for soil and management.

### 1. Custom SLOC values were misread because soil layer fixed columns were destroyed
The intended LOWOM custom topsoil organic carbon was about 0.0861% C.

DSSAT `INFO.OUT` instead reports the model-read soil profile:
- 0–20 cm OC about **1.34%**
- 20–40 cm OC about **1.35%**
- 40–60 cm OC about **1.39%**
- 60–80 cm OC about **1.43%**
- 80–100 cm OC about **1.25%**

These values do not equal the intended LOWOM or HIGHOM SLOC values. The soil hydraulic values, clay/silt and bulk density are read, but the OC field is coming from shifted/misplaced fixed-width characters.

Root cause: both nitrogen V2 and HIGHOM code modified soil rows with `line=' '.join(tokens)`. DSSAT's frozen soil reader is fixed-column sensitive, so rewriting the whole row destroyed field alignment. This explains why LOWOM/HIGHOM yielded exactly the same result and why `DSSAT48.INP` did not reflect the intended SLOC change.

Therefore the previous OM sensitivity results are invalid as OM tests. The finite-N yield response itself remains useful as evidence that NITRO=Y matters, but its absolute nitrogen dynamics use a misread OC profile.

### 2. Current real-case reconstruction is not representing plastic mulch
The same `INFO.OUT` explicitly reports:

`Simulating flat surface with no plastic mulch.`

Guo (2025) source-confirmed management is a mulched drip-irrigation system:
- 1 plastic film / 2 drip lines / 4 maize rows
- film width 1.45 m
- narrow/wide rows 30/60 cm
- drip line spacing 90 cm.

Thus current M0 differs from the real field experiment in a second major management process: plastic mulch is absent from DSSAT simulation. This can affect soil evaporation, soil temperature/water balance and therefore yield/stress response.

## Engineering/scientific decision
Do not mix both corrections in one run.

### Immediate next step: repair soil fixed-width propagation only
- Rebuild `SH.SOL` using a validated official DSSAT soil-layer fixed-width formatter.
- Preserve every non-SLOC field exactly.
- Create one LOWOM and one HIGHOM W2/N129 case.
- Verify `INFO.OUT` model-read OC equals the intended values.
- Only then judge OM sensitivity.

### Following step: plastic mulch reconstruction
Once soil input is demonstrably correct, separately determine the official DSSAT v4.8.5 FileX mulch/residue management representation compatible with CERES-Maize and reproduce the PE film treatment without inventing target-fitted parameters.

## Important consequence
Current M0 mismatch cannot be attributed only to weather or fertilizer. At least two reconstruction defects are now directly documented by DSSAT itself:
1. soil organic-C fixed-column misread;
2. no plastic mulch despite a mulched field experiment.

A third already known mismatch is that only 9/10 irrigation events are applied because the sowing-date irrigation is skipped.

## Formal accuracy gate
Guo source-confirmed target remains:
- yield RRMSE <10%;
- W2-W4 yield ARE <5%;
- W1 2020 ARE about 13.19%.
No M0/H0TT/M15TT real-yield comparison is scientifically admissible until the M0 reconstruction is compatible with the source management and passes this gate.

## Rules
- No genotype or M15 retuning.
- No N/OM/mulch parameter target fitting.
- One correction at a time with model-read audit.
- Checkpoint every material result/failure/method switch before continuation.
