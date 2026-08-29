# Diwopu DTR residual after station-specific PL calibration

- Parameters fixed from 2000-2016 all-May-Sep calibration: **A=1.849, B=0.740, C=0.242**.
- Diagnostics below use untouched **2017-2024** data.
- Best segmented breakpoint in calibrated daily RMSE: **12.7 C**.
- RMSE slope below breakpoint: **-0.0267 C/C**; above: **0.3632 C/C**.

## Independent validation by DTR

| DTR | Official RMSE | Calibrated RMSE | Calibrated Bias | Calibrated R2 |
|---|---:|---:|---:|---:|
| <10 | 1.733 | 1.704 | 0.298 | 0.929 |
| 10-<12 | 1.692 | 1.637 | 0.169 | 0.928 |
| 12-<13 | 1.707 | 1.605 | -0.028 | 0.938 |
| 13-<14 | 1.905 | 1.756 | 0.006 | 0.931 |
| 14-<14.5 | 1.899 | 1.826 | 0.050 | 0.921 |
| 14.5-<16 | 2.808 | 2.636 | 0.233 | 0.852 |
| 16-<18 | 3.555 | 3.251 | 0.027 | 0.756 |
| 18-<20 | 6.624 | 5.815 | -0.507 | 0.255 |
| >=20 | 5.105 | 4.509 | -0.491 | 0.595 |

If calibrated RMSE remains low and flat below the breakpoint but rises sharply above it, the dense second station independently supports a DTR-dependent structural limitation beyond fixed A/B/C parameter transfer.
