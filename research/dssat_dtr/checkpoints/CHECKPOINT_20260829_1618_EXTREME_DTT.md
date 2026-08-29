# DSSAT-DTR checkpoint — extreme-day thermal-time coupling

Time: 2026-08-29 16:18 CST
Branch: `research/dssat-dtr-matrix`

## Frozen state

- DSSAT source/data remain frozen at v4.8.5.0 commits `0b91373806786b600d89ccfcfff78fa2f82cb26b` and `79cb5db71bbca186add92a6a9695866a09c8b51d`.
- Weather-layer M15 remains frozen: DTRc=14.8 C, alpha=7.8094, CLOUDS-modulated sunset-anchor correction.
- Do not tune an M17 temperature formula to force crop response.

## What was learned after Stage A

Stage A potential growth (WATER=N, NITRO=N) gave 0/10 M0-M15 core crop-output changes despite clear M15 thermal activation. Source audit now explains this: CERES-Maize phenology receives daily TMAX/TMIN, while HMET computes the M15-modified hourly `WEATHER%TGRO` separately.

## Rejected hourly ET paths

1. `EVAPO=Z / PHOTO=L` reached ETPHOT but failed in ETINP because official CERES-Maize `MZCER048.SPE` has no `!*PHOT` parameter block required by ETPHOT.
2. `EVAPO=H` uses hourly air temperature but its TRANS pathway requires maize PHSV/PHTV, absent from the official species file.
3. Anningqu WTH has only SRAD/TMAX/TMIN/RAIN. Humidity/dew point/wind are not invented for Penman variants.

Stage A2R therefore uses the standard supported `WATER=Y, NITRO=N, EVAPO=R, PHOTO=R` pathway. An initial A2R run failed only because diagnostic title strings were lengthened inside a fixed-column MZX. Commit `d745dda6` removes all title edits and changes only the fixed-width METHODS row with byte-length verification. Reruns are active.

## Key CERES source finding

Official `MZ_PHENOL.for` already switches to a 24-step thermal-time calculation when:

`TMIN < TBASE OR TMAX > DOPT`

For the current proxy ecotype IB0001, TBASE=8 C and both TOPT/ROPT=34 C, so DOPT=34 C throughout vegetative/reproductive stages.

In this existing extreme branch the official code synthesizes each hourly temperature as:

`TH_i = (TMAX+TMIN)/2 + (TMAX-TMIN)/2 * sin(pi*i/12)`

then clips TH to [TBASE,DOPT] and accumulates DTT over 24 steps.

## New relationship under test

Keep the official extreme-day branch and all thresholds. Replace only its synthetic hourly `TH_i` with the HMET hourly temperature already carried as `WEATHER%TGRO(i)`:

`DTT_ext = (1/24) * sum_i [min(max(TGRO_i,TBASE),DOPT)-TBASE]`

Normal-temperature days remain unchanged. Cultivar/ecotype coefficients, TBASE/DOPT, official clipping and all other CERES logic remain unchanged.

Generic source patch:
`research/dssat_dtr/dssat485/apply_extreme_dtt_tgro_patch.py`

## Trigger-frequency evidence

Across the ten public Anningqu 2021/2022 sowing-calendar windows, the official CERES extreme branch occurs on about 15.3%-25.5% of crop-season days. The high-temperature contribution is concentrated mainly in June-August (e.g. July 2021: 16 days Tmax>34 C; June 2022: 10 days Tmax>34 C).

The direct overlap between the frozen M15 DTR>14.8 trigger and the CERES extreme branch is sparse (typically 1 day per window; 2 in 2021 sowing A). Therefore local M15 crop contribution may be small and must not be amplified by retuning DTRc.

## Causal design upgraded to four arms

1. `M0`: official DSSAT v4.8.5.0.
2. `H0TT`: official HMET/TGRO coupled to the existing CERES extreme-DTT branch, no M15 weather correction.
3. `M15W`: frozen M15 weather correction, original CERES extreme-DTT sine curve.
4. `M15TT`: frozen M15 weather correction plus identical TGRO extreme-DTT coupling.

Contrasts:
- `H0TT - M0` = generic hourly-coupling contribution.
- `M15W - M0` = weather-only propagation.
- `M15TT - H0TT` = clean Xinjiang-specific M15 contribution under identical crop coupling.
- `M15TT - M0` = total proposed extreme-day hourly-temperature method.

Formal workflow:
`.github/workflows/anningqu-extreme-dtt-four-arm.yml`

## Acceptance rule

A source/crop response is only propagation evidence. Crop-model improvement requires comparison with observations and the direction criterion `|new-observed| < |M0-observed|` for defensible observed phenology/yield variables. The current IB0035 cultivar is a proxy, so strong publication claims remain gated by cultivar/observation calibration evidence.

## Immediate next work

1. Verify fixed-width-safe Stage A2R rerun and read ET/soil-water/crop deltas.
2. Verify the extreme-DTT source patch compiles and all four arms complete real DSSAT runs.
3. Quantify generic, local-M15 and total effects on ADAT/MDAT/HWAM/CWAM and process variables.
4. If crop response is nonzero and directionally plausible, compare against Tang public observations while clearly separating proxy-cultivar limitations.
5. If local `M15TT-H0TT` is near zero, retain that as an honest mechanism result and evaluate the complete `M15TT-M0` method without retuning the frozen weather formula.
