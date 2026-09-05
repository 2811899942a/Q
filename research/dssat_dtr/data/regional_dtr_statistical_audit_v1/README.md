# Regional DTR supplementary statistical audit

The formal DTR cohort restores the frozen classification rule; temperature and crop parameters are unchanged.

|Model|Group|N|RMSE C|MAE C|Bias C|
|---|---|---:|---:|---:|---:|
|HTEMP_ORIGINAL|MaySep|5917|2.946890|1.913532|0.336824|
|M15_13P5|MaySep|5917|2.796224|1.840588|0.122534|
|M15_13P8|MaySep|5917|2.801549|1.841583|0.139694|
|REGIONAL|MaySep|5917|2.771266|1.841367|-0.030707|
|HTEMP_ORIGINAL|DTR_GE15_FORMAL|975|5.121513|3.761192|1.216685|
|M15_13P5|DTR_GE15_FORMAL|975|4.634433|3.362484|0.083587|
|M15_13P8|DTR_GE15_FORMAL|975|4.635762|3.358276|0.130214|
|REGIONAL|DTR_GE15_FORMAL|975|4.654672|3.379539|0.033005|

## Paired year-block intervals
|Comparator|Group|Delta RMSE C|95% low|95% high|
|---|---|---:|---:|---:|
|M15_13P5|MaySep|-0.024957|-0.037872|-0.014101|
|M15_13P8|MaySep|-0.030282|-0.045993|-0.017092|
|M15_13P5|DTR_GE15_FORMAL|0.020239|0.007631|0.036478|
|M15_13P8|DTR_GE15_FORMAL|0.018910|0.006318|0.031440|

## Parameter interval
{
  "model": "REG_SEASONAL_Q0",
  "beta_estimate": 1.1085040032549534,
  "beta_CI95_low": 0.9903167916863979,
  "beta_CI95_high": 1.244801195668089,
  "n_resamples": 400,
  "n_year_blocks": 17,
  "conditional_on_selected_structure_and_q": true,
  "profile_refitted_inside_resample": true,
  "selection_used_crop_outcomes": false,
  "legacy_benchmark_is_fresh_final_test": false
}

Intervals characterize the existing station/year sample and are conditional on the selected formula family; they do not constitute independent final validation.
