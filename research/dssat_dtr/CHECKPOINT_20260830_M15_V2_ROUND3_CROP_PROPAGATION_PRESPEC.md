# M15-V2 Round 3 crop propagation — prespecification

Date: 2026-08-30
Branch: `research/dssat-m15-temp-accuracy-v2`

## Frozen temperature candidate entering crop test

Temperature-only Round 3 promoted:

- `DTRc = 13.5 C`
- `alpha = 6.407985379809223`
- post-peak `p = 0.5` (`R -> sqrt(R)`)
- active-regime nighttime `Bnight = 1.05`

Independent target-station May-Sep RMSE improved from Round-1 2.7631 C to 2.7247 C; DTR>=15 RMSE improved from 4.5408 C to 4.4456 C; 0/6 target years worsened; physical violations remained zero.

No crop result may retune any temperature parameter.

## Crop arms

All source and data locks remain identical to the frozen v1 evidence chain.

1. `H0TT`: official HTEMP + audited CERES TGRO extreme-DTT coupling.
2. `M15_13P5`: frozen M15-13.5 (`alpha=6.4080`, `p=1`, `B=2.2`).
3. `M15_13P8`: frozen M15-13.8 (`alpha=6.7498`, `p=1`, `B=2.2`).
4. `R1_P05`: M15-13.5 with `p=0.5`, `B=2.2`.
5. `R3_P05_B105`: M15-13.5 with `p=0.5`, `Bnight=1.05`.

`R1_P05` versus `R3_P05_B105` isolates exactly one active-regime nighttime-B source change. Round-1 crop evidence already showed `R1_P05` and `M15_13P5` have identical eight-treatment yield results.

## Crop inputs

- Shihezi Guo 2025 reconstruction, 2019-2020, W1-W4 each year.
- Scenario `SRAD19P8_N_OFF` only.
- Weather after identical SRAD scaling, soil, cultivar, irrigation, management and all crop files must be byte-identical across all five arms.

## Hard reproduction gate

This run must reproduce:

- H0TT ALL8 RRMSE 26.9147158%.
- M15_13P5 ALL8 RRMSE 25.4973651%.
- M15_13P8 ALL8 RRMSE 24.0122042%.
- R1_P05 ALL8 RRMSE 25.4973651% and treatment-level HWAM equality to M15_13P5.

Failure invalidates the run.

## Prespecified downstream classification

- `ROUND3_CROP_STRONG`: R3 ALL8 RRMSE < R1_P05 and <= M15_13P8, with >=4/8 treatment absolute-error wins versus R1_P05.
- `ROUND3_CROP_PARTIAL`: R3 ALL8 RRMSE < R1_P05 but > M15_13P8.
- `ROUND3_NO_CROP_GAIN`: R3 ALL8 RRMSE >= R1_P05.

Also report 2019/2020 RRMSE, all eight HWAM changes, treatment wins, MAE and bias. Crop classification remains downstream evidence and cannot alter the temperature-only promotion decision.
