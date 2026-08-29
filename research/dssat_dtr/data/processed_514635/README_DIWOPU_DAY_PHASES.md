# Dense Diwopu phase-separated daytime exponent diagnostic

Only daytime observations are fitted; night is excluded. `p>1` means a narrower/lower sine shoulder away from Tmax; `p<1` means broader/higher shoulder.

| Phase | DTR | p | Val RMSE p=1 -> p | Val Bias(p) |
|---|---|---:|---:|---:|
| day | 12-<13 | 0.940 | 1.480 -> 1.479 | 0.230 |
| day | 13-<14 | 0.951 | 1.525 -> 1.525 | 0.263 |
| day | 14-<14.5 | 0.910 | 1.707 -> 1.726 | 0.440 |
| day | 14.5-<16 | 0.866 | 2.305 -> 2.342 | 0.770 |
| day | 16-<18 | 0.827 | 2.886 -> 2.930 | 0.931 |
| pre | 12-<13 | 0.961 | 1.398 -> 1.409 | 0.421 |
| pre | 13-<14 | 0.971 | 1.508 -> 1.513 | 0.395 |
| pre | 14-<14.5 | 0.924 | 1.550 -> 1.608 | 0.757 |
| pre | 14.5-<16 | 0.835 | 2.034 -> 2.125 | 1.056 |
| pre | 16-<18 | 0.764 | 2.512 -> 2.550 | 0.976 |
| post | 12-<13 | 0.837 | 1.605 -> 1.531 | -0.032 |
| post | 13-<14 | 0.852 | 1.554 -> 1.505 | 0.091 |
| post | 14-<14.5 | 0.835 | 1.933 -> 1.845 | -0.024 |
| post | 14.5-<16 | 1.033 | 2.693 -> 2.696 | 0.198 |
| post | 16-<18 | 1.252 | 3.413 -> 3.343 | 0.524 |

A mechanism is retained only if the phase-specific p trend is coherent across adjacent DTR bins and improves independent validation, not merely calibration.
