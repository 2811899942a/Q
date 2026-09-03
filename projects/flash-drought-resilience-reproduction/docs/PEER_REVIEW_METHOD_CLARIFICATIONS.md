# Peer-review method clarifications

This file records reproduction-relevant details found in the official Transparent Peer Review file that are clearer than the final article. Treat these as author-supplied clarification, while keeping conflicts with the Version of Record visible.

## 1. Soil-moisture preprocessing

The authors clarified during review that flash/slow drought identification is based on **relative changes in soil-moisture percentiles**.

They state that, for each grid cell:

1. ERA5-Land soil moisture at 0-7, 7-28 and 28-100 cm is depth weighted to 0-1 m:
   `SM = 0.07*SM1 + 0.21*SM2 + 0.72*SM3`;
2. the ERA5-Land 0-1 m series is averaged with GLDAS_CLSM 0-1 m soil moisture;
3. the resulting soil moisture is aggregated to pentad means;
4. it is then converted to percentiles **after deseasonalization and detrending**;
5. event identification operates on changes in those percentile values.

The peer-review record also explicitly says the authors added the preprocessing code for aggregated pentad-mean soil moisture to the revised code package. This makes the Code Ocean capsule the preferred source for exact calendar/window behavior.

## 2. Flash and slow drought state rules

The reviewed revision describes the following operational logic:

### Flash drought

- starts from soil moisture above the 40th percentile and develops toward/below the 20th percentile;
- onset decline rate is at least 5 percentile points per pentad;
- after crossing below the 20th percentile, onset ends when the decline rate falls below 5 percentile points per pentad;
- event terminates when soil moisture rises above the 20th percentile;
- event duration must be at least 4 pentads.

### Slow drought

- starts from above the 40th percentile and develops toward/below the 20th percentile;
- development includes slower decline than the flash-drought criterion;
- after crossing below the 20th percentile, onset ends when soil moisture begins to increase;
- event terminates when soil moisture rises above the 20th percentile;
- event duration must be at least 4 pentads.

The final Version of Record slightly refines the slow-drought wording to require **at least one pentad** with decline rate below 5 percentile points. Exact state-machine edge cases still require code inspection.

## 3. Growing-season definition

The peer-review response provides an important implementation detail omitted from the final compact Methods description:

- growing seasons are identified using multiyear-average GPP at pentad scale;
- start/end of season use a threshold of `minimum GPP + 30% of annual amplitude`;
- if minimum GPP exceeds **10 g C m-2 d-1**, the pixel is treated as having a year-round growing season;
- the authors used GPP as the primary vegetation index for growing-season definition and checked consistency with an LAI product during revision.

The final paper reports GPP-based growing-season identification and supplementary SIF verification. The exact code path remains authoritative.

## 4. Random-forest implementation clarification and conflict

The final article says each RF had `300 binary trees with 5 leaves`.

The peer-review response is more specific and states that the revised method used:

- 300 binary trees;
- one covariate chosen at random from the full predictor set for the splitting rule;
- **minimal terminal node size = 5**;
- permutation importance on Out-of-Bag samples.

This creates an important wording conflict: `5 leaves` is not the same hyperparameter as `minimum terminal node size = 5` in common RF implementations. Do not silently choose one. The released MATLAB code must resolve which parameter was actually set.

The authors also state that the RF parameter choice was checked using loss curves.

## 5. Permutation importance

The peer-review response clarifies the exact intended interpretation:

- each tree uses bootstrap samples;
- unselected observations form the OOB samples;
- for a predictor, its OOB values are randomly shuffled;
- feature importance is derived from the increase/degradation in OOB prediction error caused by the shuffle;
- larger degradation means greater importance.

The authors adopted this approach specifically to improve comparability of importance values across the four RF models.

## 6. Collinearity control

The revised workflow uses VIF and removes predictors with `VIF > 5` before final attribution modeling.

The Source Data `FigureS21a` sheet shows all 15 retained final predictors below 5 in each of the four RF configurations. Radiation and VPD are among the largest VIF values, but remain below the stated threshold in the supplied final data.

## 7. CO2 fertilization beta

In response to reviewer concerns, the authors clarify that beta is estimated at drought-event/spatiotemporal scale from **detrended and deseasonalized GPP and CO2 concentration** using `dProductivity/dCO2`.

The intent is to represent comparatively fast event-relevant variation rather than a century-scale physiological adaptation coefficient. Exact numerical estimation/windowing still requires code inspection.

## 8. Spatial-scale sensitivity test

The peer-review record reports a robustness rerun at:

- 0.5-degree spatial resolution;
- 8-day temporal resolution;

compared with the formal study's 1-degree / 5-day analysis. The authors report consistent qualitative findings for resilience and driver responses. This sensitivity run was not retained in the concise final manuscript figures, so reproducing it is optional and should not be part of the first-pass gate.

## 9. CMIP6 selection

The review response confirms the final CMIP6 procedure:

- initial candidate set: 9 ESMs;
- daily `mrso`, `r1i1p1f1`, SSP245;
- nearest-neighbor remapping to 1 degree;
- 5-day mean soil moisture;
- Taylor-diagram evaluation;
- `CMCC_CM2_SR5` excluded;
- final retained set: ACCESS-CM2, BCC-CSM2-MR, MIROC6, MPI-ESM1-2-HR, MPI-ESM1-2-LR, MRI-ESM2-0, NorESM2-LM, NorESM2-MM.

Calendar harmonization and exact Taylor-diagram implementation still require author code.

## 10. Reproduction policy derived from the review record

When the Version of Record and peer-review response differ in wording, record the conflict and resolve it from the executable author code. Do not choose the interpretation that merely makes reproduction easier.
