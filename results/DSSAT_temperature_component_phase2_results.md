# DSSAT CERES-Maize Temperature Component Sensitivity — Phase 2

Date: 2026-09-05
Branch: `research/dssat-kt-sensitivity`
Workflow run: `33941735746`
Status: `PASS`

## Objective

Separate three temperature pathways before finalizing a Urumqi regional temperature parameter:

1. high-temperature forcing: increase daily TMAX only;
2. low-temperature forcing: decrease daily TMIN only;
3. thermal accumulation: multiply daily CERES-Maize DTT after the official DTT calculation and before SUMDTT/CUMDTT accumulation.

Benchmark remains official DSSAT v4.8.5.0 / CERES-Maize / UFGA8201 with six treatments.

## Numerical closure

Official-to-DTTx1.00 closure: **PASS** for HWAM, ADAT and MDAT.

Official baseline:

- mean HWAM = 7109.67 kg/ha
- HWAM RMSE = 970.523 kg/ha
- Willmott d = 0.979845
- ADAT MAE = 1.0 d
- MDAT MAE = 0.0 d

## Core results

### High-temperature forcing (TMAX only)

| Perturbation | Change in mean HWAM | HWAM RMSE | ADAT MAE | MDAT MAE |
|---|---:|---:|---:|---:|
| TMAX +1 C | -472.67 kg/ha | 1042.315 | 3 d | 4 d |
| TMAX +2 C | -786.50 kg/ha | 1185.438 | 3 d | 5 d |
| TMAX +3 C | -1597.67 kg/ha | 1703.749 | 5 d | 7 d |
| TMAX +4 C | -2515.67 kg/ha | 2462.487 | 6 d | 9 d |

High TMAX forcing gives a strong, nonlinear negative yield response and accelerates phenology.

### Low-temperature forcing (TMIN only)

| Perturbation | Change in mean HWAM | HWAM RMSE | ADAT MAE | MDAT MAE |
|---|---:|---:|---:|---:|
| TMIN -1 C | +569.50 kg/ha | 1184.037 | 6 d | 5 d |
| TMIN -2 C | +1149.33 kg/ha | 1867.097 | 8 d | 8 d |
| TMIN -3 C | +983.17 kg/ha | 2192.156 | 10 d | 11 d |
| TMIN -4 C | +1705.00 kg/ha | 2756.138 | 12 d | 15 d |

The positive mean-yield response under lower Tmin is accompanied by strongly delayed phenology and sharply worse observation error. It therefore cannot be interpreted directly as a beneficial low-temperature physiological effect. A large part of this response is consistent with altered thermal accumulation and season duration.

### Thermal accumulation (DTT only)

| Perturbation | Change in mean HWAM | HWAM RMSE | ADAT MAE | MDAT MAE |
|---|---:|---:|---:|---:|
| DTT x0.85 | +1666.00 kg/ha | 2685.735 | 12 d | 18 d |
| DTT x0.90 | +897.33 kg/ha | 2128.250 | 10 d | 12 d |
| DTT x0.95 | +553.17 kg/ha | 1169.007 | 6 d | 6 d |
| DTT x1.00 | 0 | 970.523 | 1 d | 0 d |
| DTT x1.05 | -521.33 kg/ha | 1014.497 | 3 d | 5 d |
| DTT x1.10 | -1494.33 kg/ha | 1519.025 | 5 d | 9 d |
| DTT x1.15 | -1923.50 kg/ha | 2001.013 | 7 d | 12 d |

DTT is a high-leverage temperature pathway. A ±5% perturbation already changes mean yield by approximately 0.52–0.55 t/ha and shifts anthesis/maturity by several days.

## Decision after Phase 1 + Phase 2

Phase-1 PRFT-only KT screen produced a maximum RMSE improvement of only 0.033%, so a standalone photosynthetic-response exponent is too weak as the final innovation.

Phase 2 shows that the thermal-time pathway has strong leverage on both phenology and yield, while TMAX also has a strong nonlinear yield effect. The final regional parameter should therefore be centered on thermal accumulation / phenological progression, with explicit high- and low-temperature exposure modifiers rather than acting only on PRFT.

Recommended provisional structure for the next test:

```text
DTT_adj = DTT_original * [1 + K_RT * E_T(stage)]

E_T(stage) = wH(stage)*EH + wL(stage)*EL + wG(stage)*EG
```

where:

- `K_RT` is a single Regional Thermal Adaptation / Sensitivity Coefficient to be calibrated for the target region;
- `EH` is normalized high-temperature exposure;
- `EL` is normalized low-temperature exposure;
- `EG` is thermal-accumulation deviation;
- weights are determined from sensitivity analysis and may vary by growth stage.

The single scalar `K_RT` preserves the teacher's desired transfer logic: when moving to another region, local temperature characteristics and observations determine the regional coefficient and exposure weights while the model structure remains fixed.

## Important interpretation boundary

UFGA8201 is being used here as a reproducible mechanism benchmark. Values derived here are not Urumqi calibration coefficients. The Urumqi innovation claim must ultimately be tested with Urumqi/Xinjiang weather plus observed maize phenology and yield.

## Reproducibility

- Workflow: `.github/workflows/dssat-kt-sensitivity.yml`
- Phase-1 runner: `scripts/run_dssat_kt_screen.py`
- Phase-2 runner: `scripts/run_dssat_temperature_component_screen.py`
- Phase-1 table: `results/DSSAT_KT_phase1_screen.csv`
- Phase-2 table: `results/DSSAT_temperature_component_phase2_screen.csv`
