# Urumqi DTR-triggered two-parameter cooling shape

- Fixed DTRc: **14.5 C**
- Calibrated lambda: **3.00**
- Calibrated shape p: **0.20**
- Optimum at search boundary: **YES**
- Formula: `Tnew = TPL - lambda*(DTR-14.5)+*sin(pi*q)^p`, peak<time<sunset.
- Peak, sunset, low-DTR and nighttime predictions are unchanged by construction.

## Independent validation
- May-Sep RMSE: **2.9469 -> 2.8709 C** (2.58% improvement).
- DTR>=15 RMSE: **5.1215 -> 4.8627 C** (5.05% improvement).
- DTR>=15 MAE: **3.7612 -> 3.6480 C**.
- DTR>=15 Bias: **1.2167 -> 0.4947 C**.
- DTR>=15 R2: **0.5559 -> 0.5577**.
- Afternoon 14-18 RMSE/Bias: official **4.0106/2.3338**, M4 **3.7840/1.8468 C**.
- Night RMSE: official **2.3306**, M4 **2.3306 C**.

Interpret p physically as the temporal concentration of the extra post-peak cooling. If p is interior and validation improvement exceeds the one-parameter pulse without harming night/low-DTR, this is the first structurally defensible local candidate for source-level DSSAT testing.
