# Extreme-DTR mechanism validation prespecification

Timestamp: 2026-08-29 CST
Branch: `research/dssat-dtr-matrix`

## Scientific purpose

The frozen M15 correction was developed specifically for the Xinjiang large-diurnal-temperature-range regime. The next validation must therefore test whether the M15 advantage strengthens as DTR becomes more extreme, and whether the crop-output response can be attributed to those extreme-DTR days.

This file is committed **before** the new crop ablation results are generated, so the thresholds below are not chosen after inspecting yield outcomes.

## Frozen temperature algorithm

No M15 parameter is changed:
- `DTRc = 14.8 C`
- `alpha = 7.8094`
- original DSSAT HTEMP retained when DTR <= 14.8 C or CLOUDS <= 0
- pre-peak branch and Tmax anchor unchanged
- corrected post-peak-to-sunset branch
- official exponential night structure retained

## Prespecified DTR strata

Temperature validation will use objective DTR strata already aligned with the frozen failure regime:
- `<15 C`
- `15-<18 C`
- `18-<20 C`
- `>=20 C`

The primary contrast is the monotonic strengthening of M15 benefit as DTR increases. Existing independent 2017-2024 Urumqi validation must be used; no M15 fitting is allowed.

For Shihezi 2019-2020 crop exposure, report all growing-season days and objective extreme subsets:
- M15 trigger days: `DTR > 14.8 C`
- strong extreme days: `DTR >= 18 C`
- very strong extreme days: `DTR >= 20 C`
- top 10 DTR days per year may be listed only as illustrative case days; statistical conclusions must use all days in the prespecified strata.

## Crop-output ablation

Run identical crop inputs under the same hourly/DTT framework with four temperature arms:
1. `H0TT`: official hourly temperature + extreme-day 24-h DTT, no M15 correction.
2. `M15_FULL`: frozen M15 on all `DTR > 14.8 C` days.
3. `M15_18PLUS`: apply the **same frozen M15 correction magnitude based on DTR-14.8** only on days `DTR >= 18 C`.
4. `M15_20PLUS`: apply the **same frozen M15 correction magnitude based on DTR-14.8** only on days `DTR >= 20 C`.

The 18/20 C arms are diagnostic ablations only; they do not redefine the final M15 threshold. The DTRc=14.8 C used in the correction amplitude remains frozen.

## Shared-input scenarios

To avoid confounding by unresolved fertilizer information, the primary crop ablation is restricted to nitrogen-disabled common inputs:
- `RAW_N_OFF`: source-traceable raw NASA POWER reconstruction.
- `SRAD19P8_N_OFF`: radiation sensitivity case scaled to the thesis-described growing-season mean near 19.8 MJ m-2 d-1.

No N129/N193 proxy scenario is needed for the primary mechanism claim.

## Decision logic

Strong support for the Xinjiang-extreme-weather mechanism requires both:
1. independent hourly-temperature RMSE improvement is larger in the 18-20 and >=20 C strata than in ordinary DTR conditions;
2. extreme-day-only crop ablations reproduce a material fraction of the full M15-vs-H0TT yield shift under identical shared inputs.

Do not retune M15, cultivar coefficients, radiation, soil, irrigation, or any crop parameter based on the ablation outcome.
