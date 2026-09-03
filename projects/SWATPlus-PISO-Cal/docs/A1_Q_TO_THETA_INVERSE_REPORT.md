# A1 Q-to-theta inverse-calibration report — A1.1 scientific correction

## Scope and engineering gate

This is a result correction on base commit `ea045ecdd7b9635ca48f185a8e13fccc0df3badb`. The original A1 outputs remain preserved. No A2 work was started.

The inverse experiment used only the A0 observation-independent broad pool: `theta[4980,14]`, `qsim[4980,3,5114]`, fixed split `3984/498/498`, seed `20260902`, development period 2003-2016. The 7665 optimizer/reference rows, 27 unknown rows, 2017-2020 locked validation, and 2021-2024 final-test periods were not loaded.

The independent engineering/data-integrity result remains `A1_GATE=A1_PASS`: A1 completed, 30 closure cases completed, and six Transformer qobs fresh-SWAT cases completed. A1.1 adds scientific diagnostics and does not change that engineering gate.

## Corrected metric nomenclature

In neural training, the stored trial field `best_val` is the validation MSE in normalized 14-D theta space. It must not be called NRMSE. The corrected table is [a1_1_model_summary.csv](../artifacts/a1/a1_1_model_summary.csv); the historical [a1_model_summary.csv](../artifacts/a1/a1_model_summary.csv) is retained unchanged as an original A1 artifact.

For neural models, `val_NRMSE_sqrtMSE = sqrt(val_MSE)` as requested. PCA+Ridge used its original validation NRMSE selection metric, so its MSE column is intentionally blank rather than being relabeled.

| Model | Completed trials | Selection metric | val_MSE | val_NRMSE = sqrt(MSE) | Synthetic test NRMSE | Test mean R² |
|---|---:|---|---:|---:|---:|---:|
| PCA+Ridge | 1 | validation NRMSE | — | 0.184023 | 0.183368 | 0.497862 |
| CNN | 4 | validation MSE | 0.075191 | 0.274209 | 0.273254 | 0.094513 |
| TCN | 4 | validation MSE | 0.075794 | 0.275306 | 0.274737 | 0.083719 |
| BiLSTM | 4 | validation MSE | 0.079659 | 0.282240 | 0.282934 | 0.043746 |
| Transformer | 14 | validation MSE | 0.074279 | 0.272543 | 0.271659 | 0.105702 |

## Formal ranking

`BEST_INVERSE_OVERALL=PCA+Ridge`: synthetic test NRMSE `0.1833680494`.

`BEST_NEURAL=Transformer`: synthetic test NRMSE `0.2716594012`; frozen configuration is width 32, 14-day patch, dropout 0.10, learning rate 0.0007. The original Top2 freeze was retained in [frozen_top2.json](../artifacts/a1/frozen_top2.json), with Top2 validation MSE `0.0748516247` and corrected sqrt-MSE `0.2735902496`.

## 14-D parameter recoverability

The original Top1 Transformer per-parameter results are preserved in [a1_parameter_recoverability.csv](../artifacts/a1/a1_parameter_recoverability.csv). Its mean synthetic-test NRMSE is `0.2716594012`; 6/14 parameters have non-negative test R² (`latq_co`, `lat_ttime`, `epco`, `petco`, `deep_seep`, `perco`). Thus individual parameter recovery is heterogeneous rather than uniformly identifiable.

## Ridge qobs inference and fair fresh-SWAT comparison

The frozen Ridge was applied to the real development-period qobs using the same train-fitted preprocessing and PCA. The resulting parameter vector is in [a1_1_ridge_qobs_theta.json](../artifacts/a1/a1_1_ridge_qobs_theta.json):

```text
[-13.88545799, 0.00000000, 180.00000000, 0.30526468, 0.00000000,
  1.11819446, 0.03675902, 1.11179554, 0.14865686, 0.40000000,
  0.05000000, 0.10574347, 0.00001000, 1.10000002]
```

One fresh SWAT+ rev.62 run through `SouthBranchLegacyAdapter` was completed for this Ridge theta over 2003-2016. The three-station NSE values are:

| Candidate | 01605500 NSE | 01606000 NSE | 01606500 NSE | Mean NSE |
|---|---:|---:|---:|---:|
| Ridge qobs | 0.195703 | 0.298069 | 0.278483 | **0.257418** |
| Transformer best qobs seed_5 | 0.215445 | 0.374091 | 0.362830 | **0.317455** |

The full Ridge metrics are [ridge_qobs_fresh_swat.json](../artifacts/a1/a1_1/ridge_qobs/ridge_qobs_fresh_swat.json), and the original five-seed Transformer plus median comparison remains in [a1_fresh_swat_summary.csv](../artifacts/a1/a1_fresh_swat_summary.csv).

## Corrected 30-case synthetic forward closure

The Top1 Transformer was applied to the fixed 30 test cases. For every case, a fresh SWAT+ run generated `fresh_qsim(theta_pred)`, which was compared only with that case's original archived `qsim(theta_true)` from the A0 tensor. Real qobs was not used as the closure reference.

All 30/30 cases completed under W6. Every per-case JSON contains the three-station NSE, KGE, and RMSE; the compact per-case table is [summary.csv](../artifacts/a1/a1_1/closure/summary.csv), and the aggregate is [summary.json](../artifacts/a1/a1_1/closure/summary.json).

| Closure summary | Mean | Median | Minimum |
|---|---:|---:|---:|
| Mean NSE across three stations | 0.871796 | 0.927278 | 0.563738 |

Station-level mean NSE/KGE/RMSE:

| Gauge | Mean NSE | Mean KGE | Mean RMSE (m3/s) |
|---|---:|---:|---:|
| 01605500 | 0.889343 | 0.853783 | 1.348135 |
| 01606000 | 0.868027 | 0.854285 | 2.851822 |
| 01606500 | 0.858019 | 0.853038 | 4.192305 |

## qobs simulation-mismatch diagnostic

This is a diagnostic only; no trust threshold was set or applied. The real qobs was transformed with the train-fitted log1p/scaling and projected through the frozen Ridge PCA. Its nearest-neighbor distance to the 4980 broad qsim points in PCA space was `30.6979046`; the broad-pool leave-one-out NN reference mean and SD were `4.8247577` and `2.9532651`. The qobs distance ranked at the `100.0` percentile. An equivalent standardized PCA distance was `47.2185059`.

The descriptive label is `QOBS_MISMATCH=HIGH`; it is not an operational acceptance/rejection threshold. Full values are in [A1_1_AUDIT.json](../artifacts/a1/A1_1_AUDIT.json).

## Scientific conclusion

`INVERSE_LEARNABILITY=PARTIAL`. PCA+Ridge is the best overall inverse model on synthetic test NRMSE, while Transformer is the best neural model and has the best previously evaluated Transformer qobs mean NSE (`0.3174554569`). However, qobs lies at the extreme end of the broad simulation distribution in the train-fitted PCA diagnostic, and only 6/14 parameters show non-negative test R². The inverse mapping is therefore scientifically informative but not sufficiently validated for an automatic next-stage calibration.

`A2_READY=NO`. A1.1 is complete and the workflow stops here.
