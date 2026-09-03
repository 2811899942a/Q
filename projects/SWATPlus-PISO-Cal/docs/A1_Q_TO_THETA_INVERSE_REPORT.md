# A1 Q-to-theta inverse-calibration report

## Result and scope

`A1_GATE=A1_PASS`. A1 completed on CPU at 2026-09-03 04:24:13 +08:00 in 7.5356 wall-clock hours. The only inverse-training source was the A0 observation-independent broad pool: `theta[4980,14]`, `qsim[4980,3,5114]`, with fixed split `3984/498/498` and seed `20260902`. The 7665 optimizer/reference rows, 27 unknown rows, 2017-2020 locked validation, and 2021-2024 final-test periods were not loaded.

Runtime hardware was CPU-only: AMD Ryzen 7 8745HS, 8 physical cores, 16 logical cores, and 8 PyTorch threads. Flow inputs were log1p-transformed and standardized using training simulations only. BiLSTM used temporal compression to 128 steps. Transformer used patch embedding at 7/14/28-day patch sizes; no 5114-token full attention was used. Fresh SWAT evaluations reused `SouthBranchLegacyAdapter`, SWAT+ rev.62, development period 2003-2016, and W6 parallelism.

## Complete model comparison

The compact machine-readable table is [a1_model_summary.csv](../artifacts/a1/a1_model_summary.csv). `test_nrmse` and `test_mean_r2` below refer to the single synthetic test evaluation of each architecture's best completed configuration; no locked calendar-period data was used.

| Model | Completed trials | Best validation NRMSE | Synthetic test NRMSE | Synthetic test mean R² |
|---|---:|---:|---:|---:|
| PCA+Ridge | 1 | 0.184023 | 0.183368 | 0.497862 |
| CNN | 4 | 0.075191 | 0.273254 | 0.094513 |
| TCN | 4 | 0.075794 | 0.274737 | 0.083719 |
| BiLSTM | 4 | 0.079659 | 0.282934 | 0.043746 |
| Transformer | 14 | 0.074279 | 0.271659 | 0.105702 |

## Frozen Top1 and Top2

Top1 was Transformer, 32 channels, 14-day patch, dropout 0.10, learning rate 0.0007, with validation NRMSE `0.0742794424`. Top2 was the same Transformer family with the 14-day patch, learning rate `0.000595`, and validation NRMSE `0.0748516247`. The frozen definitions are in [frozen_top2.json](../artifacts/a1/frozen_top2.json).

For the five-seed freeze, Top1 validation NRMSE was mean ± SD `0.0748776659 ± 0.0006999950`; Top2 was `0.0754482061 ± 0.0008012864`. The Top1 synthetic test output is [synthetic_test.json](../artifacts/a1/synthetic_test.json).

## 14-D parameter recoverability

The complete per-parameter table is [a1_parameter_recoverability.csv](../artifacts/a1/a1_parameter_recoverability.csv). Top1 mean test NRMSE was `0.2716594012`. The recoverability pattern was heterogeneous: 6/14 parameters had non-negative test R² (`latq_co`, `lat_ttime`, `epco`, `petco`, `deep_seep`, `perco`), while the remaining parameters had weak or negative R² under this inverse mapping.

## qobs distribution diagnostics

The development qobs tensor was `[3,5114]`, finite and nonnegative, with global min/max/mean/median/SD `0.242675/526.693359/13.714896/6.031488/24.103708 m3/s`. Gauge means were `5.511676`, `13.121106`, and `22.511908 m3/s`; gauge SDs were `8.867219`, `19.964849`, and `33.477016 m3/s`. Full diagnostics are in [a1_qobs_distribution_diagnostics.json](../artifacts/a1/a1_qobs_distribution_diagnostics.json).

## Synthetic forward closure

All 30/30 synthetic forward-closure cases completed successfully through fresh SWAT+ runs. Per-case JSON outputs are under `artifacts/a1/closure/`; the run summary records `forward_closure_completed=30`.

## qobs inference and six fresh Real-SWAT evaluations

The six qobs theta candidates (five Top1 seeds plus ensemble median) are in [qobs_inference.json](../artifacts/a1/qobs_inference.json). The six fresh Real-SWAT three-gauge NSE results are in [a1_fresh_swat_summary.csv](../artifacts/a1/a1_fresh_swat_summary.csv).

| Candidate | 01605500 NSE | 01606000 NSE | 01606500 NSE | Mean NSE |
|---|---:|---:|---:|---:|
| qobs_seed_1 | 0.207496 | 0.277297 | 0.281066 | 0.255286 |
| qobs_seed_2 | 0.198630 | 0.357608 | 0.343907 | 0.300048 |
| qobs_seed_3 | 0.191963 | 0.304750 | 0.297486 | 0.264733 |
| qobs_seed_4 | 0.183400 | 0.270056 | 0.260527 | 0.237994 |
| qobs_seed_5 | 0.215445 | 0.374091 | 0.362830 | **0.317455** |
| qobs_ensemble_median | 0.214274 | 0.355857 | 0.338682 | 0.302938 |

## Scientific interpretation and gate

`INVERSE_LEARNABILITY=PARTIAL`: the aggregate inverse signal is useful (Top1 synthetic test mean NRMSE `0.271659`), but full 14-D unique recovery is not established because only 6/14 parameters have non-negative test R². This interpretation is separate from the execution/data-integrity gate: the prescribed A1 workflow completed, all 30 closure cases completed, all six fresh SWAT cases completed, and therefore `A1_PASS` is retained.

No A2 work was started.
