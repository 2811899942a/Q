# DSSAT-DTR checkpoint — causal decision after robust H0TT control

Time: 2026-08-29 16:30 CST
Branch: `research/dssat-dtr-matrix`

## Robust causal control completed

Workflow: `.github/workflows/anningqu-h0tt-causal-fast-v2.yml`
Run: `33243002200`
Result directory: `research/dssat_dtr/data/anningqu/h0tt_fast_causal_v2/`

The H0TT control was built from official DSSAT v4.8.5.0 HMET with only the generic crop-side `TGRO -> existing CERES extreme-day DTT` coupling. It was parsed with the same robust fixed-column logic as the valid three-arm workflow.

Definitions:
- M0 = official DSSAT/CERES extreme-day sine-hour approximation.
- H0TT = official HMET hourly TGRO routed into the existing extreme-day DTT branch.
- M15TT = frozen Xinjiang M15 hourly correction plus the same TGRO routing.
- GENERIC = H0TT - M0.
- LOCAL = M15TT - H0TT.
- TOTAL = M15TT - M0.

## Crop response decomposition

### Grain yield HWAM

| Scenario | GENERIC kg/ha | LOCAL M15 kg/ha | TOTAL kg/ha |
|---|---:|---:|---:|
| 2021 Apr21 | +1 | 0 | +1 |
| 2021 Apr26 | -2 | +2 | 0 |
| 2021 May06 | 0 | +2 | +2 |
| 2021 May16 | -1 | 0 | -1 |
| 2021 May26 | -18 | +1 | -17 |
| 2022 Apr21 | 0 | 0 | 0 |
| 2022 Apr26 | +2 | -1 | +1 |
| 2022 May06 | -2 | 0 | -2 |
| 2022 May16 | -1 | 0 | -1 |
| 2022 May26 | +9 | 0 | +9 |

- GENERIC hourly coupling changes HWAM in 8/10 cases.
- LOCAL M15 changes HWAM in 4/10 cases.
- Maximum absolute LOCAL HWAM change is only 2 kg/ha.

### Phenology

- GENERIC coupling changes MDAT in 1/10 cases (one-day scale).
- LOCAL M15 changes MDAT in 0/10 cases.
- PDAT/EDAT/ADAT are unchanged by LOCAL M15 in these scenarios.

### Biomass/process variables

CWAM shows larger GENERIC changes than LOCAL changes. Examples:
- 2021 Apr21: GENERIC +23, LOCAL -15, TOTAL +8 kg/ha.
- 2021 Apr26: +21, -14, +7.
- 2021 May06: +9, -16, -7.
- 2022 May26: +33, -3, +30.

ETCM/EPCM/ESCM/SWXM remain unchanged under these contrasts in the current Water6 reconstruction.

## Scientific decision

1. The standard water/ET propagation route is closed as a primary optimization path. It produced effectively zero M15 response.
2. The CERES extreme-day DTT source location is a valid and source-supported coupling point. Replacing its internally synthesized symmetric sine hourly temperature with DSSAT HMET hourly TGRO produces real crop responses and has a clear physical interpretation.
3. The dominant crop-side effect comes from the GENERIC hourly coupling, not from the locally calibrated M15 high-DTR correction.
4. The frozen M15 local correction remains useful as a targeted refinement of the hourly temperature trajectory on overlapping high-DTR/extreme-temperature days, but its independent crop-output effect is small under the current Anningqu proxy-cultivar reconstruction.
5. DTRc=14.8 C and alpha=7.8094 must remain frozen. They must not be retuned against yield/phenology to enlarge crop response.

## Recommended model formulation to carry forward

Use a two-layer formulation:

**Layer 1 — subdaily CERES thermal-time improvement**

On the pre-existing CERES extreme branch (`TMIN<TBASE OR TMAX>DOPT`):

`DTT_ext = (1/24) * SUM[min(max(TGRO_h,TBASE),DOPT)-TBASE]`

where `TGRO_h` is the DSSAT HMET hourly temperature. Normal-temperature days remain unchanged.

**Layer 2 — Xinjiang high-DTR refinement**

For DTR>14.8 C and CLOUDS>0, use the frozen M15 sunset/night correction to refine HMET TGRO before Layer 1 integration.

This formulation cleanly separates a broadly applicable hourly thermal-time correction from the Xinjiang-specific high-DTR calibration.

## Accuracy-validation gate

Current Anningqu simulations use proxy cultivar IB0035. Therefore these results establish source mechanics and propagation, not improvement in predictive accuracy for local maize cultivars.

The next scientifically useful calculation requires one of:
1. the user's existing calibrated Xinjiang DSSAT maize project, including cultivar coefficients and observed phenology/yield; preferred;
2. defensible local cultivar coefficients plus observed sowing/anthesis/maturity/yield for one or more Anningqu/Urumqi seasons.

Once available, run M0/H0TT/M15TT under the identical calibrated project and compare MAE/RMSE/bias for phenology and yield. This is the correct gate for deciding whether the new extreme-day hourly thermal-time formulation provides a publishable predictive advantage.

Do not spend additional cycles tuning M15 itself before this validation gate.
