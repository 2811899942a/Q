# Diwopu DTR × solar-radiation mechanism screening

- Dense NOAA temperature days merged with NASA POWER daily solar radiation: **3790** May-Sep days.
- Calibration 2000-2016; independent validation 2017-2024.
- DTR excess trigger for this screen fixed from calibration-only Diwopu breakpoint: **12.8 C**.
- Radiation variables: ALLSKY surface shortwave and ALLSKY/CLRSKY clearness ratio.

## Independent prediction of daily HTEMP RMSE
| Model | Validation RMSE | High-DTR RMSE | High-DTR R2 |
|---|---:|---:|---:|
| DTR | 0.9305 | 1.1901 | 0.1588 |
| DTR+SRAD | 0.8357 | 1.0687 | 0.3216 |
| DTR+CLEAR | 0.8113 | 1.0595 | 0.3333 |
| DTR+SRAD+INT | 0.8144 | 0.9588 | 0.4540 |
| DTR+CLEAR+INT | 0.7813 | 0.9025 | 0.5162 |
| FULL | 0.7798 | 0.8959 | 0.5233 |

Best high-DTR explanatory model: **FULL**; gain over DTR-only error prediction: **24.72%**.

## High-DTR validation days stratified by calibration SRAD tertiles
| Group | N | Mean DTR | Mean SRAD | Mean daily RMSE | Mean afternoon RMSE | Afternoon Bias |
|---|---:|---:|---:|---:|---:|---:|
| LowSRAD | 46 | 14.22 | 19.18 | 2.899 | 2.896 | 1.849 |
| MidSRAD | 67 | 14.13 | 25.44 | 1.686 | 1.377 | -0.164 |
| HighSRAD | 84 | 14.17 | 29.69 | 1.435 | 1.254 | -0.645 |

Retain SRAD as a source-level HTEMP driver only if it adds material independent-validation explanatory power beyond DTR and yields a coherent physical stratification.
