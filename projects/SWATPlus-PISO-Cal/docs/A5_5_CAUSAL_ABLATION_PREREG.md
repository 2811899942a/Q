# A5.5 causal ablation preregistration

Frozen at `2026-09-05T10:18:00.8542903Z` from Git commit `f0fe3a3ec86b98a688a958487a614c6513bf5da1` (`f0fe3a3`). The frozen A2 region SHA-256 is `b118b549611cf9c065090d1617267ccfa66d86f5f204628a0566393ea3e76d2d`.

This preregistration is created before inspecting or interpreting A6 scientific results. A6 must finish and be committed/pushed before A5.5 execution begins. A6 and A5.5 must not run concurrently.

## Scientific questions

A5.5 tests whether the frozen A2 region adds value beyond:

1. a single frozen A2-centre point warm start (`DDS_POINT_AI`); and
2. a generic 16-point global initialization (`DDS_RANDOM_SOFT`).

The existing `DDS_GLOBAL` and `DDS_SOFT_AI` ten-seed A5 results are reused directly and are not recalculated. Existing `DDS_HARD_AI` A3 evidence is auxiliary mechanism evidence only and is not pooled with the ten-seed confirmatory statistics.

## Frozen arms

All arms use the identical paired seeds `20260906` through `20260915`, 250 evaluations per seed, SWAT+ rev.62, the 2000–2002 warm-up, the 2003–2016 development objective, the same formal 14-D bounds, the same three gauges (`01605500`, `01606000`, `01606500`), and DDS sigma `0.2`.

`DDS_GLOBAL` is standard sequential DDS over the complete formal normalized `[0,1]^14` box. `DDS_SOFT_AI` is the frozen A5 rule: evaluation 1 is the frozen A2 centre, evaluations 2–16 are random samples inside the frozen A2 region, and evaluation 17 onward is standard sequential DDS over the complete formal box.

`DDS_POINT_AI` is a fresh arm: evaluation 1 is the frozen A2 centre, and evaluations 2–250 are standard sequential DDS over the complete formal box. Its evaluation-1 objective comes from that one fresh Real-SWAT development evaluation. It uses no A2/A3/A4/A5 objective, historical optimizer trace, or historical best theta.

`DDS_RANDOM_SOFT` is a fresh arm: evaluations 1–16 are a deterministic scrambled Sobol design with 16 points, 14 dimensions, paired seed as the Sobol seed, normalized `[0,1]^14`, and mapping to the complete formal bounds. The implementation is `scipy.stats.qmc.Sobol(d=14, scramble=True, seed=paired_seed).random_base2(m=4)`. Evaluations 17–250 are standard sequential DDS over the complete formal box, initialized from the best development objective among the first 16 fresh evaluations. It does not use the A2 centre, A2 region, Transformer/Ridge predictions, historical best theta, or A5 results.

The two new arms therefore require exactly `10 × 250 + 10 × 250 = 5000` fresh Real-SWAT development evaluations. A6 validation results cannot affect any A5.5 candidate, DDS state, method setting, or interpretation rule.

## Primary evaluation

For all four arms, retain the A5 anytime metrics: the best-so-far development mean NSE curve over evaluations 1–250, trapezoidal AUC normalized by 249 evaluations, best NSE at evaluations 25, 50, 100, 150, 200, and 250, and evaluations-to-first-reaching thresholds 0.50, 0.52, 0.54, and 0.55.

At each node and for final-best results, report ten-seed mean, median, sample standard deviation, paired SOFT_AI-minus-comparator or POINT_AI/RANDOM_SOFT-minus-GLOBAL delta, deterministic paired bootstrap 95% CI, and wins/ties. Bootstrap uses 20,000 paired-seed resamples with the seeds recorded in `artifacts/a5_5/A5_5_PREREG.json`.

The prespecified AUC comparisons are:

- `POINT_AI - GLOBAL`;
- `SOFT_AI - POINT_AI`;
- `RANDOM_SOFT - GLOBAL`;
- `SOFT_AI - RANDOM_SOFT`.

The 250-evaluation final-best paired comparisons are reported for the same pairs.

## Frozen causal decision rules

`REGION_GUIDANCE_VALUE=CONFIRMED` if the `SOFT_AI - POINT_AI` paired AUC delta mean is positive and its bootstrap 95% CI lower bound is positive. It is `SUPPORTED` if the mean is positive but the CI crosses zero, and `NOT_SUPPORTED` otherwise.

`AI_INFORMATION_VALUE=CONFIRMED` uses the same rule for `SOFT_AI - RANDOM_SOFT`; positive mean with a CI crossing zero is `SUPPORTED`, otherwise it is `NOT_SUPPORTED`.

`POINT_WARMSTART_VALUE` is a descriptive report of `POINT_AI - GLOBAL`; it does not alter any arm.

For the `STRONG` condition, SOFT_AI 250-evaluation final accuracy has no stable degradation when its paired final-best mean delta is not below `-0.005` and its paired bootstrap 95% CI is not wholly below zero. `ABLATION_RESULT=STRONG` requires both `REGION_GUIDANCE_VALUE=CONFIRMED` and `AI_INFORMATION_VALUE=CONFIRMED`, plus that final-accuracy condition. `ABLATION_RESULT=PARTIAL` applies when at least one value is `CONFIRMED`, or both are `SUPPORTED`; otherwise it is `NONE`.

No rule may be changed after observing A6 or A5.5 results. In particular, the A2 region, DDS sigma, bounds, objective, seeds, initialization definitions, and final-test boundary remain fixed.

## Data and recovery boundary

A5.5 reads only development observations from 2003–2016 and never reads the 2021–2024 final-test period. Every successful Real-SWAT evaluation is recorded with a flushed/fsynced ledger row, followed by an atomic per-run checkpoint and atomic heartbeat. A resume after interruption may use only deterministic no-SWAT replay from the formal ledger and may not rerun completed evaluations. BIOS, driver, power-plan, CPU-power, overclock, and undervolt changes are prohibited.

The preregistration JSON is the machine-readable authoritative copy of these rules.
