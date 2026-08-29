# Urumqi DTR-threshold hot-shoulder mechanism test

- Fixed local threshold: **14.5 C**
- Fitted dynamic-A gamma: **0.575 h per C excess DTR**
- Analytic post-peak alpha with official A: **2.850**
- Analytic post-peak alpha after dynamic A: **2.519**

## Independent validation 2017-2024, DTR>=15 C

| Model | RMSE | Improvement | MAE | Bias | R2 |
|---|---:|---:|---:|---:|---:|
| M0_OFFICIAL | 5.1215 | 0.00% | 3.7612 | 1.2167 | 0.5559 |
| M1_DYNAMIC_A | 4.9249 | 3.84% | 3.6595 | 0.3958 | 0.5796 |
| M2_POSTPEAK | 4.8629 | 5.05% | 3.6419 | 0.6260 | 0.5597 |
| M3_DYNAMIC_A_POSTPEAK | 4.8558 | 5.19% | 3.6701 | -0.5022 | 0.5639 |

## Scientific decision

M1 tests whether high-DTR days need a DTR-dependent peak-delay parameter. M2 tests excessive post-peak persistence alone. M3 tests whether both mechanisms are complementary. DTR<=14.5 C remains identical to official DSSAT in all modified models.
