# M15-V2 phenology propagation diagnostic — prespecification

Date: 2026-08-30
Branch: `research/dssat-m15-temp-accuracy-v2`

Purpose: determine whether the already-observed CERES DTT differences propagate into actual simulated anthesis/silking and maturity timing in the frozen Shihezi crop cases.

No temperature or crop parameter is fitted or changed.

## Arms
- `M15_13P5`: frozen 13.5 C M15, p=1, B=2.2.
- `M15_13P8`: frozen 13.8 C robustness arm, p=1, B=2.2.
- `R1_P05`: p=0.5, B=2.2.
- `R3_P05_B105`: p=0.5, Bnight=1.05.

All use the exact same `SRAD19P8_N_OFF` crop/weather/soil/management inputs and locked DSSAT source/data commits used in the crop-propagation tests.

## Cases
Probe W1 and W4 for 2019 and 2020. This checks both irrigation extremes while keeping the diagnostic compact. If phenology dates differ by treatment, expand to all eight treatments before drawing a mechanism conclusion.

## Required evidence
For every arm/case retain the raw `Summary.OUT` and `PlantGro.OUT` produced by DSSAT and extract all available phenology date/stage fields without assuming field names in advance.

Primary comparisons:
- `R1_P05 - M15_13P5`
- `R3_P05_B105 - R1_P05`
- `M15_13P8 - M15_13P5`

Interpretation:
- If Round 1 leaves phenology dates unchanged while Round 3 shifts anthesis/maturity, the DTT-to-phenology pathway explains the distinct crop response.
- If both leave phenology dates unchanged, investigate other HMET-derived temperature-sensitive growth/respiration pathways.
- If irrigation treatment changes the phenology response, expand the probe to all eight cases.

This diagnostic cannot alter the current temperature winner (`DTRc=13.5`, alpha=6.407985..., p=0.5, Bnight=1.05, gamma=1).
