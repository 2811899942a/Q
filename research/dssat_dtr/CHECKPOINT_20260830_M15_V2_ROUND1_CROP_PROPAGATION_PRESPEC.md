# M15-V2 Round 1 crop propagation — prespecification

Date: 2026-08-30
Branch: `research/dssat-m15-temp-accuracy-v2`

## Frozen temperature result entering this test

Round-1 temperature-only screening froze:

- `DTRc = 13.5 C`
- `alpha = 6.407985379809223`
- post-peak power exponent `p = 0.500`
- target-station May-Sep RMSE: 2.796223546 -> 2.7631 C
- target-station DTR>=15 RMSE: 4.634433256 -> 4.5408 C
- target years worse than p=1: 0/6
- physical shape violations: 0

The exponent is frozen before this crop run. Crop output cannot retune `p`, `DTRc`, or `alpha`.

## Crop arms

All arms use DSSAT v4.8.5.0 source commit `0b91373806786b600d89ccfcfff78fa2f82cb26b` and data commit `79cb5db71bbca186add92a6a9695866a09c8b51d`.

1. `H0TT`: official HTEMP plus the already-audited CERES extreme-temperature `TGRO` substitution.
2. `M15_13P5`: frozen M15 `DTRc=13.5`, `alpha=6.4080`, `p=1` plus the same extreme-temperature patch.
3. `M15_13P8`: frozen robustness M15 `DTRc=13.8`, `alpha=6.7498`, `p=1` plus the same extreme-temperature patch.
4. `V2_P05`: same `DTRc=13.5`, same `alpha=6.4080`, with the single post-peak change `R -> sqrt(R)` (`p=0.5`), plus the same extreme-temperature patch.

The direct `M15_13P5` vs `V2_P05` contrast therefore isolates only the new post-peak cooling shape.

## Inputs and crop case

- Shihezi 2019-2020 eight treatment cases from the frozen Guo 2025 reconstruction.
- Scenario: `SRAD19P8_N_OFF` only, the current project deployment scenario.
- Weather, soil, cultivar, management, irrigation and all crop inputs must be byte-identical across the four arms after the identical SRAD scaling.
- Real fertilizer / initial mineral N remain unavailable; `N_OFF` is retained exactly as in the frozen evidence chain.

## Hard reproduction gate

Before interpreting V2 crop output, the run must reproduce the frozen ALL8 crop metrics within numerical tolerance:

- `H0TT`: RMSE 2977.2722 kg/ha; RRMSE 26.9147158%.
- `M15_13P5`: RMSE 2820.48666 kg/ha; RRMSE 25.4973651%.
- `M15_13P8`: RMSE 2656.20001 kg/ha; RRMSE 24.0122042%.

Failure invalidates the crop propagation run.

## Downstream classification fixed before running V2 crop output

Crop output is independent validation and does not change the temperature parameter.

- `CROP_PROPAGATION_STRONG`: V2 ALL8 RRMSE < M15_13P5 and <= M15_13P8, with at least 4/8 treatment-level absolute-error wins versus M15_13P5.
- `CROP_PROPAGATION_PARTIAL`: V2 ALL8 RRMSE < M15_13P5 but > M15_13P8.
- `NO_CROP_GAIN`: V2 ALL8 RRMSE >= M15_13P5.

Also report RMSE, MAE, bias, 2019/2020 RRMSE, treatment-level wins, and the change in simulated yield for every treatment.

No classification may be used to retrospectively modify the Round-1 temperature selection.
