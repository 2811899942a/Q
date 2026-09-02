# Decision gates

## Gate R0: public reproduction

Pass when the clean-room CNN reproduces the published qualitative ranking and produces a valid SWAT parameter set from observed ARW discharge. Exact headline metrics are reported as replication targets, not guaranteed acceptance thresholds, because the original study used a very large architecture search.

Fail action: fix data interpretation, preprocessing, or environment. Do not start South Branch SBI.

## Gate R1: South Branch deterministic inverse baseline

Pass when at least one encoder produces fresh Real-SWAT+ performance that reaches the existing DeepCal/DDS neighborhood and does not collapse at any gauge.

Fail action: retain the reproduction result and stop encoder expansion. Diagnose observation support and parameter reachability.

## Gate R2: posterior validity on synthetic held-out targets

Required:

- simulation-based calibration approximately uniform;
- acceptable empirical coverage at 50%, 80%, and 95%;
- posterior predictive checks reproduce held-out simulator outputs;
- no systematic boundary collapse;
- posterior samples remain inside prior support.

Fail action: simplify the density estimator or observation embedding. Do not run observed-target sequential experiments.

## Gate R3: real-observation misspecification safety

The real observation receives an embedding-space OOD percentile. Posterior influence is reduced automatically when the percentile exceeds 0.95 or 0.99. A posterior-only result is never accepted without Real-SWAT+ verification.

## Gate R4: fresh Real-SWAT+ pilot

For DDS, TuRBO, and PISO-Cal, use identical 14D bounds, objectives, seeds, common initial designs, and 198-evaluation budgets.

PISO-Cal passes when either:

1. it reaches the same target NSE using at least 25% fewer fresh Real-SWAT+ evaluations than the strongest baseline; or
2. at the same budget, median final mean NSE improves by at least 0.02 without reducing the worst-gauge NSE by more than 0.03.

The median advantage must occur across three paired seeds.

Fail action: stop PISO-Cal development. Retain the best published-method reproduction and baseline comparison.

## Gate R5: final confirmation

Only after Gate R4 passes:

- five paired seeds;
- 300 evaluations per method and seed;
- pre-registered statistics;
- locked validation opened once after final method freeze;
- final test opened once after validation reporting.
