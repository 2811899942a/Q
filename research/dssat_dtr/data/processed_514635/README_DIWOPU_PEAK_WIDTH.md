# Dense Diwopu daytime peak-width exponent diagnostic

Baseline A/B/C are fixed at 1.849/0.740/0.242. Only `p` in `sin(theta)^p` is fitted separately within each 2000-2016 DTR bin.

| DTR | Mean DTR cal | p optimum | Cal RMSE p=1 -> p | Val RMSE p=1 -> p | Val Bias(p) |
|---|---:|---:|---:|---:|---:|
| <10 | 7.46 | 1.277 | 1.767 -> 1.735 | 1.704 -> 1.680 | 0.020 |
| 10-<12 | 10.52 | 1.008 | 1.525 -> 1.525 | 1.637 -> 1.636 | 0.157 |
| 12-<13 | 12.00 | 0.976 | 1.675 -> 1.674 | 1.605 -> 1.601 | 0.015 |
| 13-<14 | 13.00 | 0.981 | 1.695 -> 1.695 | 1.756 -> 1.753 | 0.043 |
| 14-<14.5 | 14.00 | 0.928 | 2.131 -> 2.123 | 1.826 -> 1.824 | 0.204 |
| 14.5-<16 | 15.00 | 0.902 | 2.524 -> 2.510 | 2.636 -> 2.656 | 0.461 |
| 16-<18 | 16.21 | 0.911 | 3.332 -> 3.322 | 3.251 -> 3.260 | 0.252 |
| 18-<20 | 18.38 | 0.818 | 3.081 -> 3.021 | 5.815 -> 5.770 | 0.028 |

Interpretation: a reproducible rise of p above 1 with DTR would directly support a DTR-dependent narrowing of the daytime thermal peak. Lack of a systematic p-DTR relationship would reject this mechanism before any source modification.
