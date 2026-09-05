# M19 innovation position and prior-art boundary

Status: working research-position document, 2026-09-05. This is not a legal patentability opinion and must not be used to claim that no prior patent exists.

## Prior art that constrains the claim

1. Parton-Logan diurnal temperature reconstruction is established prior art: daytime truncated sine + nighttime exponential cooling.
2. Site-specific and generic regional calibration of Parton-Logan parameters is established. A representative study is *Generic calibration of a simple model of diurnal temperature variations for spatial analysis of accumulated degree-days*, International Journal of Biometeorology 62 (2018) 621-630, DOI 10.1007/s00484-017-1471-5. It calibrates/compares generic and site-specific PL parameters across Swiss stations.
3. Hourly-temperature reconstruction models have been compared across diverse agro-ecological regions; regional suitability by itself is not novel. Representative example: *Identifying appropriate prediction models for estimating hourly temperature over diverse agro-ecological regions of India*, Scientific Reports (2023).
4. Solar radiation and diurnal temperature generation have been jointly considered in earlier weather-generation/microclimate studies. Therefore the presence of SRAD alone cannot support novelty.
5. DSSAT temperature stress, thermal-time modification, heat indices and Xinjiang maize heat response already have published precedents. Generic claims such as "add a high-temperature factor", "modify thermal time", "use HDD", or "make DSSAT suitable for Xinjiang" are too broad.
6. Public patent searching found DSSAT local genetic-parameter calibration, weather-data correction/downscaling, heat/disaster indices and crop-risk workflows. Representative retrieved families include CN116628978B, CN118586743A and other DSSAT-localization patents. This search has not identified a fully isomorphic chain to M19, but the conclusion must remain: **no fully isomorphic public result was found in the current search**, not "no patent exists".

## Current defensible research contribution

The working contribution is the full mechanism chain:

**region-relative seasonal DTR anomaly -> radiation-state activation -> physically constrained HTEMP intraday-shape correction -> TAIRHR/TGRO -> CERES-Maize phenology/biomass/yield propagation**.

The proposed transferable regional parameter is:

`K_RT = the local seasonally standardized DTR anomaly trigger threshold, in standard-deviation units`.

For M19:

`z_DTR = (DTR - local seasonal mean DTR) / local seasonal SD(DTR)`

`E = max(z_DTR-K_RT,0) * max(Kt0-Kt,0) / 0.1`

`S = 1-exp(-E/gain_scale)`

`q_new = (1-S)*q_official + S*q_official^P_TARGET`

Current Urumqi mechanism-screen value: `K_RT = 1.40 SD`.

## Why this position is stronger than simple PL calibration

- K_RT is expressed in standardized local-climate units instead of an absolute DTR threshold, allowing the same model structure to be transferred while the trigger is recalibrated to local thermal variability.
- Radiation state gates the DTR anomaly, so identical absolute DTR can cause different corrections under different atmospheric/radiative states.
- The correction is applied inside DSSAT's hourly weather chain after official HTEMP and before downstream crop use; neutral/inactive conditions retain the official solution.
- The correction is constrained to physically valid Tmin/Tmax anchors and monotonic shoulders.
- The research design explicitly tests whether the meteorological correction propagates into crop-model state/output variables, rather than evaluating hourly temperature reconstruction in isolation.

## Claims that should not be made

Avoid:
- "we invented the Parton-Logan regional calibration";
- "DSSAT previously had no temperature sensitivity parameter";
- "solar radiation has never been used in hourly-temperature reconstruction";
- "DTR has never been studied for crops";
- "no similar patent exists";
- using current proxy-cultivar Anningqu propagation as final yield-accuracy validation.

## Evidence still required before publication-level claim

1. Complete source-level M19 compilation and crop propagation A/B.
2. Fresh Urumqi/Xinjiang hourly-weather validation separated from the model-development years.
3. Observed local maize phenology and yield validation with a calibrated target cultivar.
4. Sensitivity/uncertainty analysis of K_RT and fixed structural constants.
5. Cross-site transfer test: freeze the formula and structural constants, rebuild local DTR climatology, calibrate only K_RT, and evaluate on independent data.
6. Final targeted literature and patent search immediately before manuscript/patent drafting.
