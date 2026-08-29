# M10 final robustness validation

No parameters were refitted. M10 parameters were frozen before this analysis.

## 2017-2024 high-DTR year consistency

| Year | High-DTR days | Official RMSE | M10 RMSE | Improvement |
|---|---:|---:|---:|---:|
| 2020 | 25 | 5.182 | 4.574 | 11.73% |
| 2021 | 33 | 5.098 | 4.246 | 16.70% |
| 2022 | 19 | 4.796 | 4.193 | 12.57% |
| 2023 | 22 | 4.977 | 4.288 | 13.83% |
| 2024 | 24 | 5.457 | 4.767 | 12.63% |

M10 improves high-DTR RMSE in **5/5 validation years with high-DTR observations**.

## Paired day-block bootstrap (DTR>=15 C)

- Validation days: **123**; points: **975**
- Observed RMSE: **5.1215 -> 4.4196 C**
- Observed improvement: **13.71%**
- Bootstrap median improvement: **13.65%**
- 95% CI improvement: **[10.76%, 16.54%]**
- 95% CI absolute RMSE reduction: **[0.521, 0.890] C**
- Bootstrap probability RMSE improvement >0: **100.00%**

Stopping criterion: if annual consistency is broad and the paired day-block bootstrap CI remains above zero, M10 is accepted as the current statistical prototype and formula search should stop until crop/DSSAT propagation testing.
