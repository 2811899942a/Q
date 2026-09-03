# A1.5 Simulation–Observation Mismatch Attribution

- Base commit: `1460acd61396988108d7c469eae5e1826be63a96`
- Scope: A1.5 diagnostic only; no new Real-SWAT run, no posterior training, and no A2 execution.
- Formal reference distribution: A0 observation-independent broad qsim, `N=4980`, development 2003–2016.
- Historical qobs-directed assets are a diagnostic contrast pool only and remain excluded from A1/A2 training.

## Scientific conclusion

`MISMATCH_CAUSE=MIXED`; recommended A2 method: `preconditioned RNPE + local simulation enrichment`.
A2 remains blocked by protocol (`A2_READY=NO`): The evidence supports more than one limitation: directed coverage changes the distance, but residual OOD and/or representation quality remain material.

## Provenance audit

The optimizer/reference manifest contains 7665 rows. Confirmed qobs-directed: 7664; synthetic/reference without qobs proof: 0; unknown: 1.

| Source family | confirmed | synthetic/reference | unknown |
|---|---:|---:|---:|
| Knowledge-guided calibration V1/V2 | 1348 | 0 | 1 |
| R1_1000 calibration | 728 | 0 | 0 |
| R2 calibration | 530 | 0 | 0 |
| R3_4096 calibration and sensitivity | 2993 | 0 | 0 |
| R4_FAST_2048 calibration | 2048 | 0 | 0 |
| historical_maximin_farthest_point | 17 | 0 | 0 |

The contrast pool has 53 readable existing qsim realizations: Knowledge-guided calibration V1/V2=22, R2 calibration=8, R3_4096 calibration and sensitivity=6, historical_maximin_farthest_point=17. Missing legacy files were not imputed or treated as qsim.

## PCA mismatch and Mahalanobis diagnostics

Distances use the frozen A1 Ridge PCA embedding, with preprocessing fitted only on the A1 broad-pool train split. Percentiles rank qobs distance against leave-one-out within-pool nearest-neighbour distances; they are descriptive and are not trust thresholds.

- qobs → broad: distance=30.697905, percentile=100.000%, rank=4981/4980, Mahalanobis=47.986541.
- qobs → confirmed directed: distance=30.751131, percentile=98.113%, rank=53/53, Mahalanobis=12973.934589.

## Hydrologic feature diagnostics

The feature vector contains 75 values per realization: per-gauge mean/std/CV, Q5/Q25/Q50/Q75/Q95, 12-month climatology, lag-1 autocorrelation, high/low-flow frequencies, and three pairwise gauge-ratio mean/median features.
qobs lies inside the broad featurewise Q05–Q95 envelope for 38.7% of features and inside the confirmed-directed envelope for 74.7%.

Top broad-reference standardized residuals:

- `ratio.01606000_over_01606500.mean`: z=-17.413956, qobs=0.500355, broad mean=0.664389.
- `ratio.01605500_over_01606000.mean`: z=15.727879, qobs=0.702598, broad mean=0.504671.
- `ratio.01606000_over_01606500.median`: z=-15.445596, qobs=0.514348, broad mean=0.663345.
- `ratio.01605500_over_01606500.median`: z=-6.552852, qobs=0.262480, broad mean=0.331918.
- `ratio.01605500_over_01606500.mean`: z=-5.758602, qobs=0.274312, broad mean=0.331188.
- `01605500.cv`: z=4.948229, qobs=1.608964, broad mean=0.565459.
- `01606000.cv`: z=4.561068, qobs=1.521732, broad mean=0.578624.
- `01606500.cv`: z=4.514289, qobs=1.487226, broad mean=0.559231.
- `01605500.lag1_acf`: z=-4.283696, qobs=0.637568, broad mean=0.911729.
- `01606500.std`: z=4.204951, qobs=33.480289, broad mean=13.484207.

## Existing-real-SWAT nearest-20 diagnostics

NSE/KGE/RMSE below are recomputed from the persisted development qsim against qobs; no SWAT executable was invoked in A1.5.

Best mean NSE among broad nearest 20: `0.4919189394`; best mean NSE among confirmed-directed nearest 20: `0.4992979169`.

| Pool | rank | simulation | NSE 055 | NSE 060 | NSE 065 | mean NSE |
|---|---:|---|---:|---:|---:|---:|
| broad | 1 | `DEEPCAL5K-SOBOL-0174` | 0.383461 | 0.568452 | 0.523845 | 0.491919 |
| broad | 2 | `DEEPCAL5K-SOBOL-0567` | 0.381397 | 0.491429 | 0.458553 | 0.443793 |
| broad | 3 | `DEEPCAL5K-SOBOL-1849` | 0.380376 | 0.494452 | 0.418607 | 0.431145 |
| broad | 4 | `DEEPCAL5K-SOBOL-4133` | 0.352044 | 0.491590 | 0.480045 | 0.441226 |
| broad | 5 | `DEEPCAL5K-SOBOL-2473` | 0.400842 | 0.517619 | 0.465933 | 0.461464 |
| broad | 6 | `DEEPCAL5K-SOBOL-2441` | 0.320810 | 0.466272 | 0.377988 | 0.388357 |
| broad | 7 | `DEEPCAL5K-SOBOL-0678` | 0.369593 | 0.518896 | 0.487853 | 0.458781 |
| broad | 8 | `DEEPCAL500-SOBOL-0077` | 0.374890 | 0.466893 | 0.419227 | 0.420337 |
| broad | 9 | `DEEPCAL5K-SOBOL-2701` | 0.337087 | 0.529368 | 0.496462 | 0.454305 |
| broad | 10 | `DEEPCAL5K-SOBOL-3589` | 0.362213 | 0.420298 | 0.388321 | 0.390277 |
| broad | 11 | `DEEPCAL5K-SOBOL-2125` | 0.370142 | 0.543169 | 0.534590 | 0.482634 |
| broad | 12 | `DEEPCAL100-SOBOL-0043` | 0.350411 | 0.578636 | 0.543862 | 0.490969 |
| broad | 13 | `DEEPCAL5K-SOBOL-2327` | 0.401789 | 0.546186 | 0.498400 | 0.482125 |
| broad | 14 | `DEEPCAL5K-SOBOL-1355` | 0.368715 | 0.519587 | 0.513514 | 0.467272 |
| broad | 15 | `DEEPCAL5K-SOBOL-0319` | 0.279903 | 0.409593 | 0.350784 | 0.346760 |
| broad | 16 | `DEEPCAL5K-SOBOL-0465` | 0.318695 | 0.458364 | 0.430549 | 0.402536 |
| broad | 17 | `DEEPCAL500-SOBOL-0211` | 0.332770 | 0.507050 | 0.486127 | 0.441982 |
| broad | 18 | `DEEPCAL5K-SOBOL-4405` | 0.300432 | 0.513207 | 0.489158 | 0.434266 |
| broad | 19 | `DEEPCAL500-SOBOL-0192` | 0.292981 | 0.444933 | 0.429420 | 0.389111 |
| broad | 20 | `DEEPCAL500-SOBOL-0287` | 0.301598 | 0.436436 | 0.387093 | 0.375042 |
| confirmed-directed | 1 | `archive-index:000014:worker_05` | 0.387671 | 0.563469 | 0.494218 | 0.481786 |
| confirmed-directed | 2 | `archive-index:000012:worker_03` | 0.363487 | 0.548089 | 0.499431 | 0.470336 |
| confirmed-directed | 3 | `archive-index:000015:worker_06` | 0.368619 | 0.555589 | 0.519398 | 0.481202 |
| confirmed-directed | 4 | `archive-index:000013:worker_04` | 0.415209 | 0.568606 | 0.514079 | 0.499298 |
| confirmed-directed | 5 | `archive-index:000037:PILOT-PROPOSAL-Random-42-0172` | 0.288753 | 0.522297 | 0.517952 | 0.443001 |
| confirmed-directed | 6 | `DEEPCAL100-HIST-FP-0010` | 0.353973 | 0.552590 | 0.512236 | 0.472933 |
| confirmed-directed | 7 | `DEEPCAL100-HIST-FP-0001` | 0.203973 | 0.386892 | 0.411595 | 0.334154 |
| confirmed-directed | 8 | `archive-index:000049:V2-PROPOSAL-BO-42-0051` | 0.365642 | 0.546135 | 0.493853 | 0.468543 |
| confirmed-directed | 9 | `DEEPCAL100-HIST-FP-0015` | 0.186434 | 0.379973 | 0.395839 | 0.320748 |
| confirmed-directed | 10 | `archive-index:000034:PILOT-PROPOSAL-BO-42-0094` | 0.257758 | 0.464086 | 0.411559 | 0.377801 |
| confirmed-directed | 11 | `DEEPCAL100-HIST-FP-0003` | 0.249450 | 0.287339 | 0.262771 | 0.266520 |
| confirmed-directed | 12 | `archive-index:000033:PILOT-PROPOSAL-BO-42-0034` | 0.152604 | 0.202094 | 0.272228 | 0.208975 |
| confirmed-directed | 13 | `archive-index:000038:COMMON-ANCHOR-20260910-0001` | 0.195293 | 0.396184 | 0.318224 | 0.303234 |
| confirmed-directed | 14 | `archive-index:000017:worker_08` | 0.370443 | 0.530468 | 0.487412 | 0.462774 |
| confirmed-directed | 15 | `archive-index:000007:worker_04` | -0.135153 | 0.528032 | 0.448641 | 0.280507 |
| confirmed-directed | 16 | `DEEPCAL100-HIST-FP-0004` | 0.228706 | 0.173173 | 0.222835 | 0.208238 |
| confirmed-directed | 17 | `archive-index:000016:worker_07` | 0.336600 | 0.531337 | 0.510514 | 0.459484 |
| confirmed-directed | 18 | `archive-index:000010:worker_07` | -0.147947 | 0.550041 | 0.455718 | 0.285937 |
| confirmed-directed | 19 | `archive-index:000005:worker_02` | -0.141623 | 0.528032 | 0.438456 | 0.274955 |
| confirmed-directed | 20 | `archive-index:000011:worker_08` | -0.160563 | 0.528198 | 0.436554 | 0.268063 |

## Interpretation and protocol boundary

Coverage flag=False; structural flag=True; representation flag=True. The labels are an attribution of this fixed diagnostic evidence, not a new training gate or trust threshold.

The A1 engineering gate remains separately recorded in `artifacts/a1/A1_GATE.json`. This A1.5 report does not change A1 results and does not authorize A2.
