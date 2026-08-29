# Main Urumqi 51463 DTR x solar-radiation screening

- Station: **51463099999**, 87.6167 E, 43.7833 N
- Matched May-Sep days: **2867**
- Calibration: 2000-2016; validation: 2017-2024
- Formal DTR trigger: **14.8 C**, from calibration only
- SRAD source: NASA POWER daily LST at the station coordinate

## Daily RMSE prediction, independent high-DTR validation
| Model | High-DTR RMSE | High-DTR R2 |
|---|---:|---:|
| DTR | 2.6093 | -0.1292 |
| DTR+SRAD | 2.0742 | 0.2864 |
| DTR+CLEAR | 1.9331 | 0.3802 |
| DTR+SRAD+INT | 1.9042 | 0.3986 |
| DTR+CLEAR+INT | 1.7842 | 0.4720 |
| FULL | 1.8558 | 0.4287 |

Best daily-RMSE model: **DTR+CLEAR+INT**, improvement over DTR-only error prediction: **31.62%**.

Best afternoon-bias model: **DTR+CLEAR+INT**, improvement over DTR-only prediction: **33.51%**.

## High-DTR validation SRAD strata
| Group | N | Mean DTR | Mean SRAD | Daily RMSE | Afternoon RMSE | Afternoon Bias |
|---|---:|---:|---:|---:|---:|---:|
| LowSRAD | 32 | 16.73 | 12.02 | 7.058 | 10.248 | 10.136 |
| MidSRAD | 58 | 16.78 | 21.72 | 4.280 | 4.871 | 4.690 |
| HighSRAD | 33 | 16.24 | 29.30 | 2.428 | 1.324 | 0.837 |

Decision rule: only promote SRAD into the Urumqi HTEMP formula if it adds material independent-validation information beyond DTR and the high-DTR strata show a coherent residual shift.
