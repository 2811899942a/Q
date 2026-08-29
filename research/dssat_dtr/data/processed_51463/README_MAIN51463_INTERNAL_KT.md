# Main 51463 internal astronomical clearness-index screen

`Ra` is computed from latitude + DOY using FAO-56 extraterrestrial radiation. `Kt = SRAD/Ra`. This requires no clear-sky radiation input and can be computed inside DSSAT from existing weather/astronomical variables.

- Calibration mean Kt = **0.5772**
- Formal DTR trigger = **14.8 C**

## Independent high-DTR validation: daily RMSE prediction
| Model | RMSE | R2 |
|---|---:|---:|
| DTR | 2.6093 | -0.1292 |
| DTR+SRAD+INT | 1.9042 | 0.3986 |
| DTR+KT | 1.9760 | 0.3524 |
| DTR+KT+INT | 1.8252 | 0.4474 |
| DTR+CLEAR+INT | 1.7842 | 0.4720 |

`DTR+Kt+interaction` gain over DTR-only = **30.05%**.
Its RMSE is **+2.30%** relative to the NASA clear-sky-ratio interaction model (positive means worse).

For afternoon-bias prediction, `DTR+Kt+interaction` improves high-DTR RMSE by **nan%** relative to DTR-only.

Decision: if Kt retains most of the CLEAR-model gain, use Kt in the source-level prototype because it is internally computable and does not require a new weather input.
