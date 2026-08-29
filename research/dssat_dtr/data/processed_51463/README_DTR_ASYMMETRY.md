# Urumqi 51463 — DTR-driven asymmetric HTEMP residual diagnosis

## Purpose

This is a **mechanism-discovery** analysis. No new DSSAT formula has been fitted. The test asks whether Urumqi observations support the local hypothesis that increasing DTR changes the *temporal allocation* of temperature error: stronger morning underestimation together with stronger afternoon overestimation.

## Analysis windows

- Morning: local apparent solar time **05:00-09:59**.
- Afternoon: **14:00-18:59**.
- Night: **20:00-04:59**.
- Main crop-relevant window: **May-Sep**.

## Key DTR relationships in May-Sep

### Morning bias vs DTR
- n days = **2865**
- Pearson r = **-0.2599**
- Spearman rho = **-0.2992**
- OLS slope = **-0.1254 C bias per 1 C DTR**

A negative slope means the model becomes increasingly cold-biased in the morning as DTR increases.

### Afternoon bias vs DTR
- n days = **2864**
- Pearson r = **0.2402**
- Spearman rho = **-0.065**
- OLS slope = **0.2508 C bias per 1 C DTR**

A positive slope means the model becomes increasingly warm-biased in the afternoon as DTR increases.

### Sampled peak-checkpoint timing error vs DTR
- Pearson r = **-0.0599**
- Spearman rho = **-0.0299**
- OLS slope = **-0.062 h per 1 C DTR**

This timing diagnostic is deliberately called a **sampled peak-checkpoint error**, because ISD provides about eight real observations per day rather than a continuous observed Tmax timestamp.

## DTR-bin contrast in May-Sep

- DTR <8 C: morning=-0.0588 C; afternoon=1.6633 C; gap=1.7222 C; daily_RMSE=1.6455 C; n=291
- DTR 15-<18 C: morning=-1.2254 C; afternoon=4.2938 C; gap=5.5192 C; daily_RMSE=3.9534 C; n=183
- DTR >=20 C: morning=-1.8314 C; afternoon=12.5755 C; gap=14.4069 C; daily_RMSE=9.2847 C; n=9

Automated mechanism verdict: **ASYMMETRIC_DTR_SIGNAL_SUPPORTED**.

## Extreme-temperature diagnostic thresholds (May-Sep empirical distribution)

These are diagnostic quantiles, not yet maize physiological thresholds:

- TMAX P90 = **33.50 C**
- TMAX P95 = **34.70 C**
- TMIN P10 = **9.60 C**
- TMIN P05 = **7.70 C**

The file `extreme_temperature_diagnostics.csv` compares hot-tail, cold-tail, non-extreme, and high-DTR days using the same morning/afternoon residual metrics. This tells us whether a future source-level correction should be activated broadly by DTR or only under extreme high/low temperature regimes.

## Scientific use rule

Do not yet claim a new mechanism from the automated verdict alone. A locally defensible DSSAT modification requires that the residual asymmetry is (1) monotonic or at least threshold-like across DTR bins, (2) present in the maize season, (3) not explained solely by a handful of >=20 C DTR days, and (4) stronger than or complementary to the hot/cold extreme-temperature signal.
