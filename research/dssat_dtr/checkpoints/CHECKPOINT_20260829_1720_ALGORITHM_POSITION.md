# DSSAT temperature-method checkpoint — algorithm position

Time: 2026-08-29 17:20 CST
Branch: `research/dssat-dtr-matrix`

## Current scientific innovation type

Primary innovation: **process-model structural / process-representation innovation** inside DSSAT CERES-Maize phenology.

Secondary innovation: **Xinjiang mechanism-informed regional refinement** of DSSAT HMET hourly temperature under high-DTR conditions.

Current formulation:

1. On the pre-existing CERES extreme-temperature branch (`TMIN<TBASE OR TMAX>DOPT`), replace the internally synthesized symmetric sine hourly temperature with DSSAT HMET hourly `TGRO` and integrate clipped hourly thermal time:

`DTT_ext=(1/24)*SUM[min(max(TGRO_h,TBASE),DOPT)-TBASE]`

Normal-temperature days remain official CERES behavior.

2. When `DTR>14.8 C` and `CLOUDS>0`, apply frozen M15 to refine the HMET hourly trajectory before the DTT integration. Frozen M15 uses `alpha=7.8094` and keeps the official Parton-Logan night structure.

## Evaluation hierarchy

1. Hourly temperature physical accuracy and transferability: RMSE, bias, R2, physical-curve violations, high-DTR subset.
2. Source-code integrity: normal-day invariance, existing thresholds/clipping retained, official DSSAT build/run.
3. Mechanism: change in extreme-day and seasonal DTT.
4. Causal crop propagation: M0/H0TT/M15W/M15TT decomposition.
5. Real calibrated predictive accuracy: compare phenology/yield errors using the same local cultivar/soil/management project.

## Current strongest quantitative result

Independent cross-station validation of M15 (source calibration: Diwopu 51463599999, 2000-2016; target validation: 51463099999, 2017-2024):

- May-Sep hourly temperature RMSE: 2.9469 -> 2.8223 C, improvement 4.23%.
- High-DTR (`DTR>=15 C`) RMSE: 5.1215 -> 4.6783 C, improvement **8.65%**.
- High-DTR bias: 1.2167 -> 0.3777 C.
- High-DTR R2: 0.5559 -> 0.6210.
- Complete-curve physical violations: 0/130.

This is currently the clearest demonstrated advantage of the Xinjiang local correction.

## Crop-side causal result under proxy Anningqu cultivar

- Generic HMET-hourly coupling changes HWAM in 8/10 scenarios.
- Local M15 changes HWAM after controlling generic coupling in 4/10 scenarios; max absolute local yield change 2 kg/ha.
- Total M15TT-M0 HWAM changes range from -17 to +9 kg/ha in the tested proxy-cultivar scenarios.
- Mechanism audit shows seasonal total DTT changes of about +0.69 to +4.25 C d across the 10 sowing windows; generic hourly coupling is the dominant contribution.

## New validation resource from Guo Lipeng 2025

Guo Lipeng's Shihezi University thesis provides a real 2019-2020 Shihezi field case for cultivar Xinyu 66, including calibrated CERES-Maize coefficients:

- P1 = 104.7
- P2 = 1.824
- P5 = 957.2
- G2 = 671
- G3 = 15.82
- PHINT = 42.97

This removes the proxy-cultivar barrier. The next decisive experiment is the identical real-case comparison M0 / H0TT / M15TT against observed phenology and yield, without retuning DTRc or alpha to crop outputs.

## Decision

Carry forward the two-layer method. Treat 8.65% high-DTR hourly-temperature RMSE improvement as the current strongest validated result. Do not claim crop predictive improvement until the Xinyu 66 real-case reconstruction is completed.
