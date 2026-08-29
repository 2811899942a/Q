# Dense Diwopu station-specific PL calibration

- Calibration objective: all May-Sep 2000-2016 hourly observations only.
- Optimized parameters: **A=1.849, B=0.740, C=0.242**.
- Official parameters: A=2.0, B=2.2, C=1.0.
- Optimizer success: **True**; evaluations: **774**.

## Independent 2017-2024 validation
- All May-Sep RMSE: official **1.853 C** -> Diwopu-PL **1.777 C**.
- DTR 14.5-18 RMSE: official **3.128 C** -> Diwopu-PL **2.897 C**.
- DTR 14.5-18 Bias: official **-0.250 C** -> Diwopu-PL **0.150 C**.
- DTR 14.5-18 R2: official **0.800** -> Diwopu-PL **0.817**.

If station-specific A/B/C substantially improves ordinary conditions but a large, time-structured high-DTR residual remains, that independently reproduces the parameter-transfer + structural-error decomposition seen at 51463.
