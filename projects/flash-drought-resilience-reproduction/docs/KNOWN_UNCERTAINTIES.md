# Known Uncertainties - Do Not Guess

Status legend: `RESOLVED`, `PARTIAL`, `OPEN`, `CONFLICT`.

The official Supplementary Information, Reporting Summary, Transparent Peer Review and Source Data have now been audited. Items below have been updated accordingly. Code Ocean remains the authoritative source for executable edge cases.

1. **Soil-moisture preprocessing before percentiles - PARTIAL.** Peer review explicitly states that the combined soil-moisture pentad series is converted to percentiles **after deseasonalization and detrending**. The exact percentile reference sample/calendar-window treatment still requires code.
2. **Pentad calendar handling - OPEN.** Leap day, final partial pentad, missing days, and growing-season boundary handling require code.
3. **Event state-machine edge cases - OPEN.** Equality at 40/20 percentile, missing pentads, temporary reversals and immediately adjacent events require code.
4. **MFDI implementation - OPEN.** The printed formulas are now visually confirmed as `zij = 100 +/- ((xij-Mxj)/Sxj)*10` and `MFDI = Mzi +/- Szi*cvi`. Literal reconstruction from the four Source Data ingredients is highly correlated (~0.98) with published grid MFDI but does not match exactly (MAE ~3.8). A preprocessing/sign/clipping/masking convention remains unresolved.
5. **BEAST configuration - OPEN.** Package/options/priors/change-point settings require code.
6. **Aridity-index source and preprocessing - OPEN.** Threshold classes are known; exact gridded aridity product/processing used for the 29-region partition still needs code/package inspection.
7. **Growing-season extraction - PARTIAL.** Peer review resolves the main algorithm: multiyear-average pentad GPP, SOS/EOS at minimum + 30% annual amplitude, and pixels with minimum GPP >10 g C m-2 d-1 treated as year-round. Exact smoothing/fitting/boundary behavior still needs code.
8. **Drought-event filtering for resilience - PARTIAL.** >2-year event separation and anomaly sign conditions are stated; edge cases remain code-dependent.
9. **Executable definition of `Ya` - OPEN.** Exact post-effect indexing/window boundaries require code.
10. **CO2 fertilization beta - PARTIAL.** Peer review clarifies event/spatiotemporal beta from detrended+deseasonalized GPP and CO2 using `dProductivity/dCO2`; numerical window/regression implementation remains open.
11. **Random-forest hyperparameter mapping - CONFLICT.** Version of Record says `300 binary trees with 5 leaves`; peer-review response says `300 trees`, one covariate sampled for split rule, and `minimum terminal node size = 5`. These are not equivalent hyperparameters. Released MATLAB code must decide the executable truth.
12. **Permutation importance - RESOLVED conceptually.** Author response explicitly describes OOB permutation/shuffle error degradation as the importance measure. Exact MATLAB function/options/random seed remain code-dependent.
13. **VIF screen - RESOLVED.** `VIF > 5` predictors were removed; Source Data `FigureS21a` confirms all 15 final predictor VIF values are below 5 for all four models.
14. **PDP confidence intervals - OPEN.** Method used to obtain 95% confidence bands requires code.
15. **CMIP6 model set/remapping - PARTIAL.** Nine candidates, eight retained models, SSP245, `mrso`, `r1i1p1f1`, nearest-neighbor 1-degree remapping and pentad means are confirmed. Calendar harmonization/stitching and exact Taylor implementation remain open.
16. **Source Data RF accuracy metric - OPEN.** Observed/estimated pairs are present. SSE-R2 and squared correlation differ, so the plotted/claimed accuracy metric must be identified from author MATLAB code rather than assumed.
17. **Code Ocean license/file tree - OPEN.** Capsule is public/citable but explicit redistribution terms and complete contents are not yet inspected.

A reproduction result cannot be marked exact/PASS while an `OPEN` or `CONFLICT` item materially affects that result.
