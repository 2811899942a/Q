# Known Uncertainties - Do Not Guess

The following items are intentionally unresolved at repository initialization. They must be answered from the official Supplementary Information / Source Data / Code Ocean capsule before exact reimplementation.

1. **Soil-moisture percentile construction.** The paper states pentad SM is converted to percentiles, but the exact empirical reference sample/calendar-window treatment is not specified in enough detail in the main text.
2. **Pentad calendar handling.** Treatment of leap days, partial terminal pentads, and growing-season boundary pentads must be taken from code.
3. **Event state-machine edge cases.** Exact handling of equality at 40/20 percentile, missing pentads, temporary reversals during onset, and immediately adjacent events needs code confirmation.
4. **MFDI sign convention.** Eqs. 3 and 7 are written using `+/-`. The exact implemented branch must be read from the released code.
5. **BEAST configuration.** Package/language, priors, seasonality/trend options and change-point settings are not fully specified in the main article.
6. **Aridity-index source and preprocessing.** Main text states classes and thresholds but does not fully identify the exact gridded aridity input implementation used for the 29-region partition.
7. **Growing-season extraction implementation.** The 30% seasonal-amplitude criterion is given; curve smoothing/fitting details and boundary handling require code/Supplementary confirmation.
8. **Drought-event filtering for resilience.** The paper gives the >2-year separation rule and anomaly sign conditions; event selection edge cases require code confirmation.
9. **Definition of `Ya` in executable form.** Exact indexing/window boundaries must be taken from author code.
10. **CO2 fertilization beta.** Numerical estimation window/regression/smoothing details are not fully specified in the main text.
11. **Random-forest implementation.** Main text gives 300 trees, 5 leaves, OOB permutation importance and PDP, but software/library, random seeds, split rules and exact `5 leaves` parameter mapping require capsule inspection.
12. **PDP confidence intervals.** The mechanism used for 95% CI requires code confirmation.
13. **CMIP6 preprocessing.** Calendar harmonization, temporal stitching and exact Taylor metrics/selection threshold require code confirmation.
14. **Rehosting license for Code Ocean contents.** The capsule is publicly citable, but its explicit code/data license must be read before mirroring the author's files into a public GitHub repository.

A reproduction result cannot be marked PASS while any uncertainty materially affecting that result remains unresolved.
