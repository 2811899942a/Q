# Paper Methods Map

| Module | Inputs | Core operation | Primary outputs | Paper target |
|---|---|---|---|---|
| 0-1 m soil moisture | ERA5-Land SM1/2/3 + GLDAS_CLSM | ERA5 depth weighting; mean of ERA5 and GLDAS | daily 1° SM | historical drought engine |
| Pentad percentile | daily combined SM | 5-day mean -> percentile | pentad percentile SM | drought identification |
| Flash/slow event engine | pentad percentile SM | 40/20 thresholds + 5 pp/pentad rate rules + >=4 pentads | event table | Fig.1/S1/S2/S16 |
| Drought metrics | event table | counts, severity, onset speed, ratio | grid metrics/time series | Fig.1 |
| Change point | annual anomalies | BEAST | turning points | Fig.1g-i |
| Land-atmosphere coupling | pentad SM + VPD | corr(SM,VPD)*sd(VPD) | CSI_SM-VPD | Fig.S9 |
| Eco-climate partition | SM/ET, T/ET, aridity, land cover | limitation index + aridity classes + vegetation classes | 29 regions | Fig.S17 |
| MFDI | ratio, counts, severity, onset speed | standardized composite | MFDI | Fig.2/S4 |
| Growing season | FluxSat GPP | min + 30% seasonal-amplitude threshold | pixel growing season | Fig.S19 |
| Resilience | drought event + GPP/SIF | <=2 yr recovery after max negative anomaly | resilience | Fig.3/S5/S6 |
| Attribution | resilience + 15 predictors | VIF -> 4 RFs -> OOB permutation importance -> PDP | importance/response curves | Fig.4-5/S7/S8/S21 |
| CMIP6 | 9 initial ESMs, SSP245 mrso | Taylor evaluation -> remove CMCC_CM2_SR5 -> 8 models -> 1°/pentad | future event metrics | Fig.S10/S15 |

## Equations explicitly supported by the manuscript

### ERA5-Land 0-1 m soil moisture

`SM = 0.07*SM1 + 0.21*SM2 + 0.72*SM3`

### Land-atmosphere coupling

`CSI_SM-VPD = corr(SM, VPD) * sigma(VPD)`

Smaller values denote stronger coupling in the paper's convention.

### Standardization for MFDI components

`z_ij = 100 +/- ((x_ij - M_xj)/S_xj)*10`

### Coefficient of variation

`cv_i = S_zi / M_zi`

### Generalized MFDI form

`MFDI = M_zi +/- S_zi*cv_i`

The manuscript leaves the sign in generalized form. The exact sign used in this study must be taken from the released code before implementation.

### Vegetation resilience

`Resilience = Ya - Ym`

### CO2 fertilization effect

`beta = d(Productivity)/d(CO2)`

### Water-use efficiency

`WUE = Productivity / Evapotranspiration`
