# Decision gates — A-basin formal sequence

## Optional P0: published-method implementation check

Public DL4SWAT data may be used for a clean-room CNN sanity check. P0 is optional and does not block A-basin work. Failure means inspect implementation ambiguity; it does not authorize changing the A-basin study area.

## Gate A0: South Branch takeover and equivalence

Required PASS:

- formal study area = A_SOUTH_BRANCH_POTOMAC;
- SWAT+ rev.62 project located and hashed;
- exact 14D parameter dictionary/bounds/write semantics frozen from existing workflow;
- gauge order = 01605500/ch12, 01606000/ch17, 01606500/ch18;
- 2003–2016 observed development data aligned;
- existing formal objective snapshotted and hashed;
- broad and observed-directed archives separated;
- one formal theta produces equivalent old/new daily three-gauge outputs and identical objective;
- locked validation/final test remain unopened.

Fail action: repair takeover/audit only. No deep-learning training.

## Gate A1: deterministic inverse baseline on A basin

At least one encoder must produce a valid 14D theta from real development Qobs and a successful fresh Real-SWAT+ run. Report synthetic parameter error and real observed objective separately.

A1 is informative even if it does not beat DDS. Do not rescue a weak encoder by adding architectures beyond the frozen four-model screen.

## Gate A2: posterior validity on held-out A-basin simulations

Required:

- acceptable SBC behavior;
- empirical 50/80/95% coverage reported;
- TARP reported;
- posterior predictive checks consistent with held-out simulator outputs;
- no systematic boundary collapse;
- posterior samples inside frozen prior bounds.

Fail action: simplify density/embedding once. Persistent failure terminates posterior branch.

## Gate A3: real-observation misspecification safety

Establish support/OOD diagnostics using controlled mismatch experiments. Posterior trust schedule is frozen here before seeing A4 method-comparison outcomes. Real Qobs never supplies a fictitious true theta label.

## Gate A4: fresh Real-SWAT+ pilot

Methods share identical 14D bounds, inherited objective, common initial points, paired seeds, runner, and accounting.

Primary comparison: PISO-Cal vs TuRBO.

PISO-Cal passes if either:

1. it reaches the same predeclared target mean NSE with at least 25% fewer fresh Real-SWAT+ evaluations than the strongest baseline; or
2. at the same 198-evaluation budget, median final mean NSE improves by at least 0.02 without reducing worst-gauge NSE by more than 0.03.

Three paired seeds are required for the pilot. A single-seed win is not a PASS.

Fail action: stop PISO-Cal mechanism development. Retain A-basin inverse-calibration reproduction and strongest baseline result.

## Gate A5: final confirmation

Only after A4 PASS:

- five paired seeds;
- up to 300 evaluations per method/seed;
- pre-registered comparison statistics;
- method and hyperparameters frozen;
- open 2017–2020 locked validation once;
- report validation before opening 2021–2024 final test once.
