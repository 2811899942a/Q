# DSSAT-DTR checkpoint — propagation results after extreme-DTT coupling

Time: 2026-08-29 16:25 CST
Branch: `research/dssat-dtr-matrix`

## 1. Standard water-path propagation is essentially negligible

Stage A2R (`WATER=Y, NITRO=N, EVAPO=R, PHOTO=R`, Water-6 67.5 mm sowing irrigation) completed successfully after the fixed-column MZX repair.

Result commit: `488189613f28f0d848aab841b2ed8435347ec82a`

Across 10 Anningqu year × sowing-date scenarios:
- 9/10 M0 vs M15 scenarios were identical in all checked crop/process outputs.
- Only ANQH2105 changed, and only marginally: CWAM +1 kg/ha.
- HWAM: 0 change in all 10.
- ETCM: 0 change in all 10.
- SWXM: 0 change in all 10.

Conclusion: do not continue tuning water/ET switches to force M15 crop response. The standard CERES water pathway does not materially consume the frozen hourly M15 signal.

## 2. Extreme-day DTT coupling creates real crop response

Completed three-arm real-DSSAT workflow:
- M0: official DSSAT v4.8.5.
- M15W: frozen weather-layer M15 only.
- M15TT: M15W plus `WEATHER%TGRO` routed into the existing CERES extreme-day DTT integration.

Result commit: `9d8d3d166c3cb7f72d0b24c2d66c61c67043d5d2`

Weather-only M15W again changed almost nothing (1/10 summary cases, same ANQH2105 marginal CWAM change).

M15TT relative to M15W produced crop-output changes in 10/10 scenarios.
HWAM changes (kg/ha):
- 2021 Apr21 +1
- 2021 Apr26 0
- 2021 May06 +2
- 2021 May16 -1
- 2021 May26 -17
- 2022 Apr21 0
- 2022 Apr26 +1
- 2022 May06 -2
- 2022 May16 -1
- 2022 May26 +9

CWAM changes ranged about -10 to +30 kg/ha. One 2021 sowing case showed a one-day maturity shift in the current parser representation.

This is propagation evidence, not yet model-accuracy evidence.

## 3. Mechanism audit quantifies the thermal cause

Pure-equation audit directly translated DSSAT v4.8.5 DAYLEN, SOLAR, HTEMP and CERES extreme-day DTT.
Result commit: `0363aa69e75c2131bec0042cef7619f49c34a581`

For each public Anningqu sowing-season window:
- Complete proposed hourly extreme-DTT method adds about +0.69 to +4.25 C d relative to the original CERES sine-hour approximation.
- Generic official-HMET hourly coupling contributes about +1.35 to +4.36 C d.
- Frozen local M15 correction contributes about -0.11 to -0.82 C d after controlling the generic hourly method.
- Largest local single-day effect: 2021-06-08 (Tmax 37, Tmin 20, DTR 17, cloudiness 0.253), local delta DTT = -0.780 C d.

Thus most of the new crop response is expected to come from replacing the CERES internal symmetric sine hourly approximation with DSSAT HMET hourly temperature. M15 adds a smaller, physically targeted Xinjiang high-DTR correction on the subset of overlapping extreme/high-DTR days.

## 4. Four-arm causal design remains the publication-grade attribution

Formal arms:
- M0 = official CERES sine extreme DTT.
- H0TT = official HMET/TGRO -> extreme DTT.
- M15W = weather M15 only, original CERES sine DTT.
- M15TT = weather M15 + TGRO extreme DTT.

Contrasts:
- GENERIC = H0TT - M0.
- WEATHER = M15W - M0.
- LOCAL = M15TT - H0TT.
- TOTAL = M15TT - M0.

The first completed four-arm workflow ran all simulations but used a simple whitespace parser for fixed-width `Summary.OUT`. Its committed table contains impossible/misaligned fields (e.g. HWAM=-99 and shifted date values) and is explicitly INVALID FOR SCIENTIFIC INTERPRETATION.

Invalid parse-only result commit: `2cd1651d47a933ee9f1527d2582b65768505e69d`.
Do not cite its numerical contrasts.

A robust H0TT-only causal rerun is active using the same fixed-column parser logic as the successful three-arm run. Once H0TT is obtained, it can be combined with already valid M0/M15TT values without rebuilding all four arms.

## 5. Observation/calibration gate

Tang et al. (2024, Sustainability 16, 4571) provides real Anningqu 2021-2022 field experiments with five sowing dates, six maize hybrids, irrigation gradients, phenology/yield traits, and measured yield methodology.

Current DSSAT scenario still uses official proxy cultivar `IB0035 McCurdy 84aa`. The public Tang hybrids (e.g. Xinyu 65, KWS3376, KWS9384, Huamei No.1, Xinyu 102, Heyu 187) do not yet have locally calibrated CERES genetic coefficients in this workflow.

Therefore:
- current source experiments can establish mechanism and propagation;
- a claim of improved DSSAT predictive accuracy needs real local cultivar calibration/observations or the user's existing calibrated Xinjiang DSSAT project.

## Immediate next gate

1. Finish robust H0TT causal decomposition.
2. Quantify GENERIC vs LOCAL effects on HWAM/CWAM and phenology.
3. Decide whether the complete hourly extreme-DTT formulation has sufficient response magnitude to carry forward.
4. For formal accuracy validation, ingest the user's existing calibrated DSSAT maize project or obtain defensible local cultivar coefficients/observed phenology and yield.
5. Keep M15 DTRc=14.8 and alpha=7.8094 frozen; do not tune them against crop outputs.
