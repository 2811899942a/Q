# Extreme-temperature interaction diagnostic

Thresholds are diagnostic values established before this fit: DTRc=14.5 C, hot Tmax>33.5 C (May-Sep P90), cold Tmin<9.6 C (May-Sep P10).

| Model | Validation all RMSE | Validation high-DTR RMSE | High-DTR MAE | High-DTR Bias |
|---|---:|---:|---:|---:|
| DTR | 2.9685 | 4.7954 | 3.9976 | 0.8416 |
| DTR+HOT | 2.9861 | 4.8162 | 4.0063 | 0.7295 |
| DTR+COLD | 2.9692 | 4.7966 | 3.9985 | 0.8457 |
| DTR+HOT+COLD | 2.9874 | 4.8184 | 4.0081 | 0.7357 |

Best independent high-DTR predictor: **DTR**. Improvement over DTR-only residual predictor: **0.00%**.

Decision: add hot/cold extreme triggers to the HTEMP structural correction only if they produce a material independent-validation gain beyond DTR excess alone. Otherwise keep the source modification parsimonious and DTR-driven.
