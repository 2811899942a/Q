# Urumqi two-sided DTR-triggered hot-shoulder narrowing

- DTR trigger: **>14.5 C**
- Fitted pre-peak shoulder coefficient: **alpha_pre=13.333**
- Fitted post-peak shoulder coefficient: **alpha_post=2.850**
- Calibration: 2000-2016 May-Sep
- Independent validation: 2017-2024 May-Sep

The correction is zero at solar noon, official modeled Tmax time, and sunset; therefore the daily Tmax anchor is retained.

## Independent validation DTR>=15 C

| Model | RMSE | MAE | Bias | R2 |
|---|---:|---:|---:|---:|
| Official | 5.1215 | 3.7612 | 1.2167 | 0.5559 |
| Two-sided shoulder | 4.6567 | 3.5922 | -0.0954 | 0.5485 |

RMSE improvement: **9.07%**.
