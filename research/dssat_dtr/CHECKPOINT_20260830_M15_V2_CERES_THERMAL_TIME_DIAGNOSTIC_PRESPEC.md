# M15-V2 CERES thermal-time sensitivity diagnostic — prespecification

Date: 2026-08-30
Branch: `research/dssat-m15-temp-accuracy-v2`

## Purpose

Explain the downstream mechanism behind two already-frozen observations:

1. Round 1 (`p=0.5`, `Bnight=2.2`) improved independent hourly-temperature RMSE but produced exactly the same eight Shihezi yields as frozen M15-13.5.
2. Round 3 (`p=0.5`, `Bnight=1.05`) further improved independent hourly-temperature RMSE and reduced Shihezi ALL8 yield RRMSE from 25.497365% to 23.983874%.

This is a diagnostic only. It does not select or retune any temperature parameter.

## Locked DSSAT mechanism

Use DSSAT v4.8.5.0 source commit `0b91373806786b600d89ccfcfff78fa2f82cb26b`.

The exact `IB0001` ecotype row must be parsed from `Data/Genotype/MZCER048.ECO` at runtime. The current locked source gives TBASE=8 C, TOPT=34 C and ROPT=34 C, so the Shihezi cultivar has the same 34 C development optimum before and after anthesis.

The already-audited CERES patch changes only the out-of-range DTT branch from the synthetic sinusoid to the DSSAT `TGRO(1:24)` hourly temperatures. The source logic to reproduce is:

- if `TMAX < TBASE`, DTT=0;
- else if `TMIN > DOPT`, DTT=`DOPT-TBASE`;
- else if `TMIN < TBASE` or `TMAX > DOPT`, clip every TGRO hour to `[TBASE,DOPT]`, sum `(TH-TBASE)/24`;
- otherwise DTT=`(TMAX+TMIN)/2-TBASE`.

DSSAT HMET generates `TGRO(H)` at `HS=H*24/TS`; with TS=24 this is exactly H=1,...,24 h.

## Arms

Use the same `SRAD19P8_N_OFF` Shihezi weather transformation and compare:

- `H0TT`: official Parton-Logan hourly curve.
- `M15_13P5`: DTRc=13.5 C, alpha=6.407985379809223, p=1, B=2.2.
- `M15_13P8`: DTRc=13.8 C, alpha=6.749813473189908, p=1, B=2.2.
- `R1_P05`: DTRc=13.5 C, alpha=6.407985379809223, p=0.5, B=2.2.
- `R3_P05_B105`: DTRc=13.5 C, alpha=6.407985379809223, p=0.5, Bnight=1.05.

No crop observations or yield values are read by the diagnostic script.

## Diagnostic windows

For each year use the exact Shihezi simulation planting-to-horizon window already embedded in the frozen input workflow:

- 2019: 2019-05-03 through 2019-10-25.
- 2020: 2020-05-05 through 2020-10-25.

Also report May-Sep separately so the diagnostic is comparable with the temperature-validation convention.

## Required outputs

For every day and arm report:

- TMAX, TMIN, DTR, scaled SRAD, CLOUDS;
- active/inactive M15 status;
- whether CERES takes the normal or out-of-range DTT branch;
- 24 hourly TGRO values;
- raw hourly mean;
- clipped `[8,34] C` mean;
- CERES DTT;
- hours below TBASE and above DOPT before clipping;
- degree-hours below TBASE and above DOPT.

For each year/window report:

- cumulative DTT;
- number of days with non-zero DTT difference;
- mean/max absolute daily DTT difference;
- cumulative DTT difference for `R1_P05 - M15_13P5` and `R3_P05_B105 - R1_P05`;
- clamp-hour and degree-hour changes.

## Interpretation fixed before seeing the numbers

- If `R1_P05` materially changes hourly temperature but barely changes CERES DTT relative to M15-13.5, its zero crop response is consistent with thermal-time filtering of the post-peak shape improvement.
- If Round 3 changes DTT much more strongly than Round 1, the nighttime-decay improvement has a direct CERES thermal-time propagation pathway.
- If Round 3 crop improvement is large while DTT changes remain negligible, thermal time is insufficient to explain the crop response and the next diagnostic must inspect other HMET-derived temperature-sensitive growth/respiration variables and actual phenology outputs.

No threshold for a new model is introduced here. The current best temperature model remains frozen throughout this diagnostic.
