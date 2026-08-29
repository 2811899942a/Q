# Final lower-bound DTRc audit completion checkpoint

Timestamp: 2026-08-29 23:14 CST
Branch: `research/dssat-dtr-matrix`
Workflow: `Shihezi M15 DTRc Final Lower-Bound Audit V2`
Run ID: `33259349242`
Status: SUCCESS

## Completion status
All planned execution stages completed successfully:
- checkout / environment setup PASS
- DSSAT builds PASS
- final lower-bound audit PASS
- output commit PASS
- post-job cleanup PASS

The result directory is populated with the expected audit products, including:
- `README_FINAL_LOWER_BOUND_AUDIT.md`
- `README_DTRC_FOURLEVEL_ABLATION.md`
- `alpha_calibration.csv`
- `temperature_metrics.csv`
- `temperature_strata.csv`
- `temperature_coverage.csv`
- `temperature_shape_qa.csv`
- `temperature_year_by_year.csv`
- `shihezi_threshold_coverage.csv`
- `shared_input_audit.csv`
- `crop_treatment_rows.csv`
- `crop_metrics.csv`
- `crop_contrasts.csv`
- `manifest.json`

Shared-input byte-equality gate is PASS for soil, both WTH files, cultivar and all eight MZX cases.

## Final lower-bound temperature results
Independent available observations within the nominal 2017-2024 validation window:

| Arm | DTRc C | alpha | May-Sep RMSE C | DTR>=15 RMSE C | Bias C | R2 | shape violations |
|---|---:|---:|---:|---:|---:|---:|---:|
| T13P0 | 13.0 | 5.6039 | 2.7881 | 4.6338 | +0.1018 | 0.8225 | 0 |
| T13P5 | 13.5 | 6.4080 | 2.7962 | 4.6344 | +0.1225 | 0.8217 | 0 |
| T13P8 | 13.8 | 6.7498 | 2.8015 | 4.6358 | +0.1397 | 0.8211 | 0 |
| T14P0 | 14.0 | 6.8051 | 2.8053 | 4.6391 | +0.1545 | 0.8207 | 0 |
| T14P8 | 14.8 | 7.8094 | 2.8223 | 4.6783 | +0.1981 | 0.8188 | 0 |

Under the prespecified primary-candidate rule (13.5/13.8/14.0 C only), the temperature-only provisional winner is 13.5 C. The 13.0 C arm remains an aggressive negative-control boundary and must not be promoted merely because it has the smallest aggregate RMSE.

## Crop propagation
RAW_N_OFF ALL8 RRMSE remains strongly high-biased for all lower-threshold variants; T14P8 remains lower than T13P0/T13P5/T13P8/T14P0 in this scenario.

Under `SRAD19P8_N_OFF`:
- T13P0: 25.532%
- T13P5: 25.497%
- T13P8: 24.012%
- T14P0: 24.288%
- T14P8: 25.038%

Thus the best downstream crop RRMSE in this diagnostic scenario is 13.8 C, while threshold selection remains temperature-only.

## Important data-coverage clarification
The nominal validation interval is called `2017-2024`, but the year-by-year audit contains usable records only for 2018 and 2020-2024 (six calendar years). There are five usable year groups for the DTR>=15 comparison. 2017 and 2019 do not appear in the year-by-year result because usable pointwise observations are absent from the current validation source chain.

Therefore future manuscript wording must say `available observations within 2017-2024` or explicitly list the valid years, not claim eight continuous complete validation years.

## Interpretation / stop rule
- The computation is complete; no planned output is missing because of workflow failure.
- Do not descend below 13.0 C without new mechanism evidence.
- Because 13.0 activates about 58-60% of the Shihezi crop season, it is retained as a lower-bound negative control rather than the default final parameter.
- Final freezing should weigh the prespecified primary set, year-by-year stability, high-DTR behavior, bias, cap frequency, physical QA and minimum-intervention principle.
