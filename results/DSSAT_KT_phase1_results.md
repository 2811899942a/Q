# DSSAT CERES-Maize KT Phase-1 Mechanism Screen

Date: 2026-09-05
Branch: `research/dssat-kt-sensitivity`
Workflow run: `33941472202`
Status: `PASS`

## 1. Purpose

Test whether a newly introduced continuous temperature-response-strength coefficient `KT` produces an identifiable crop response in a clean, reproducible DSSAT benchmark before introducing Urumqi-specific high-temperature, low-temperature and thermal-time exposure terms.

## 2. Frozen benchmark

- DSSAT source: official `DSSAT/dssat-csm-os`, tag `v4.8.5.0`
- DSSAT data: official `DSSAT/dssat-csm-data`, tag `v4.8.5.0`
- Crop model: CERES-Maize
- Experiment: `UFGA8201.MZX`
- Treatments: 6
- Validation targets: `results/DSSAT_UFGA8201_observed_targets.csv`
- Outputs: HWAM, ADAT, MDAT

The workflow compiles the unmodified official source and the modified source separately, runs the official baseline, then runs the KT grid. `KT=0` must reproduce official HWAM/ADAT/MDAT exactly.

## 3. Phase-1 implementation

The official CERES-Maize photosynthetic temperature factor is calculated as:

```fortran
PRFT = CURV('LIN',PRFTC(1),PRFTC(2),PRFTC(3),PRFTC(4),TAVGD)
PRFT = AMAX1(PRFT,0.0)
PRFT = MIN(PRFT,1.0)
```

Phase 1 adds the following experimental response-strength transformation:

```text
PRFT_new = PRFT_original^(1 + KT)
```

`KT=0` leaves the official response unchanged. Positive KT strengthens temperature limitation when `0 < PRFT < 1`; negative KT weakens it.

Screened values:

`-0.75, -0.50, -0.25, 0.00, +0.25, +0.50, +0.75, +1.00`

## 4. Numerical results

| Case | HWAM RMSE (kg/ha) | Willmott d | Delta RMSE vs official | ADAT MAE (d) | MDAT MAE (d) |
|---|---:|---:|---:|---:|---:|
| Official | 970.523 | 0.979845 | 0.000% | 1.0 | 0.0 |
| KT=-0.75 | 970.697 | 0.979841 | -0.018% | 1.0 | 0.0 |
| KT=-0.50 | 970.682 | 0.979841 | -0.016% | 1.0 | 0.0 |
| KT=-0.25 | 970.538 | 0.979845 | -0.002% | 1.0 | 0.0 |
| KT=0.00 | 970.523 | 0.979845 | 0.000% | 1.0 | 0.0 |
| KT=+0.25 | 970.360 | 0.979851 | +0.017% | 1.0 | 0.0 |
| KT=+0.50 | **970.202** | **0.979855** | **+0.033%** | 1.0 | 0.0 |
| KT=+0.75 | **970.202** | **0.979855** | **+0.033%** | 1.0 | 0.0 |
| KT=+1.00 | 970.928 | 0.979829 | -0.042% | 1.0 | 0.0 |

Official-to-KT0 numerical closure: **PASS**.

Treatment-level official HWAM (kg/ha):

`T1=2293, T2=2293, T3=8207, T4=11854, T5=7718, T6=10293`

At the best phase-1 cases (`KT=+0.50/+0.75`), only T4 and T6 shift materially at DSSAT integer output precision:

- T4: 11854 -> 11853 kg/ha
- T6: 10293 -> 10291 kg/ha
- T1/T2/T3/T5: unchanged

ADAT is 1982133 for all six treatments under every KT value; MDAT is 1982185 for all six treatments under every KT value.

## 5. Interpretation

1. The new parameter is computationally well-defined and attributable: KT=0 closes exactly to the official DSSAT result.
2. A PRFT-only response-strength coefficient has extremely weak leverage in this benchmark. The best yield-RMSE improvement is only 0.033%, with treatment-level yield changes of only a few kg/ha.
3. The phase-1 insertion does not influence thermal-time phenology, so ADAT and MDAT are unchanged across the KT grid. This is consistent with the insertion point.
4. Therefore a standalone PRFT exponent coefficient is not sufficient as the final model innovation.
5. The parameter concept should be retained and expanded so that its value is driven by explicit high-temperature, low-temperature and thermal-time exposure, with growth-stage sensitivity. This follows the intended Urumqi regional-adaptation logic and creates a mechanistically stronger target for sensitivity analysis.

## 6. Phase-2 direction

Construct a temperature exposure term using separate components:

- high-temperature exposure `EH`
- low-temperature exposure `EL`
- thermal-time / GDD deviation `EG`
- optional diurnal-temperature-range diagnostic `EDTR`
- growth-stage-dependent weights or sensitivities

The resulting regional temperature response factor should be tested at three candidate insertion levels:

1. photosynthetic temperature response (`PRFT`),
2. grain-filling temperature response (`RGFIL`),
3. thermal-time/phenology pathway (`DTT/GDD`), followed by a combined model only if component tests justify it.

Phase 2 must quantify sensitivity first, then freeze the mathematical form. Urumqi-specific calibration requires local weather plus observed phenology/yield and must not use the UFGA optimum as the Urumqi coefficient.

## 7. Reproducibility

Workflow: `.github/workflows/dssat-kt-sensitivity.yml`
Runner: `scripts/run_dssat_kt_screen.py`
Full table: `results/DSSAT_KT_phase1_screen.csv`
