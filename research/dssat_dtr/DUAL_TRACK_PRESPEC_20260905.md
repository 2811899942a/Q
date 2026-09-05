# Regional DTR reconstruction and crop-response dual-track pilot

Date: 2026-09-05. Status at registration: DESIGN, before regional-model outputs.

## Objective and scope
Test whether a region-conditioned diurnal temperature reconstruction can improve the temperature-to-crop chain while retaining M15-13.5 and M15-13.8 as immutable comparators. The two interventions are separable: (A) radiation-weighted hourly evaluation of the existing PRFTC response; (B) a locally standardized DTR driver of the HTEMP sunset anchor. Their combination is a third arm. DSSAT 4.8.5.0 source 0b91373806786b600d89ccfcfff78fa2f82cb26b and data 79cb5db71bbca186add92a6a9695866a09c8b51d remain locked.

## Registered regional candidate family
DTR = Tmax - Tmin. z = (DTR - local seasonal mean) / local seasonal SD. The candidate K = 1 - exp(-beta * CLOUDS * max(z-q,0)) rescales the available sunset-to-minimum amplitude: Ts_new = Tmin + (Ts_original-Tmin)*(1-K). This is a pilot candidate family, not an asserted final universal formula. Beta is fitted only to observed temperatures. q in {0,0.5,1}; climatology is either growing-season pooled or seasonally varying. These six structures are selected using blocked year cross-validation entirely within dense-station 2000-2016 data. Regional profiles also use training-period data only. No crop outcome may choose temperature parameters or the candidate structure. Fixed-degree M15 controls identify whether normalization yields more than a units change. Seasonal profiles and the nonlinear bounded response make this candidate distinguishable from a mere affine reparameterization.

Observed near-sunset readings must be compared at their actual observation time, not treated as exact sunset. Temperature validation uses exactly matched primary-station timestamps and reports all-season, high-DTR, day and night errors. Preserve Tmin/Tmax, continuous sunset linkage, monotonic branches and valid bounds. Report paired year-block bootstrap 95% intervals; small year counts limit inference.

## Crop comparison
Preserve the existing Shihezi 2019/2020 four-irrigation-treatment input chain and observed yields. Compare original M0, H0TT, both frozen M15 arms, M15-13.8 + hourly PRFTC, regional HTEMP alone, and regional HTEMP + hourly PRFTC. Use original and SRAD19P8_N_OFF scenarios separately. These are reconstructed-input diagnostics: NASA POWER weather, common initial-water assumptions, and disabled nitrogen remain explicit. They do not establish full field validation or Urumqi regional performance. Recover the M15-13.8 vector/RMSE before interpreting changes. A coefficient of zero must be exactly neutral for crop coupling.

For each arm report yield errors by year/treatment and simulated phenology/biomass where outputs exist. Observed phenology/biomass must not be invented. Diagnose the previous KRT grid using leave-one-year-out selection; the two years are very few independent environments. No split by irrigation treatment may masquerade as independent weather-year validation.

## Promotion rule
Engineering success, aggregate diagnostic improvement, and scientific validation are distinct. A release requires temperature improvement over frozen controls, acceptable year-to-year stability, physical QA, crop improvement without material damage to other years, and ultimately a new independent site/year test. Historical 2017-2024 results have already informed model development and are now a legacy benchmark, not a fresh untouched final test. Preserve every candidate outcome, including failures. No automatic replacement of the frozen release; no tuning weather, management, cultivar or observed targets to manufacture gains.

## Innovation wording
Working claim: regional temperature-structure-conditioned HTEMP reconstruction with auditable propagation into CERES-Maize temperature exposure and crop response. Generic diurnal-model calibration, thermal-time functions, hourly temperature suitability and standardization all have prior literature. Novelty of the specific combination and patent claims require a claim-by-claim comparison; this pilot establishes feasibility evidence only.
