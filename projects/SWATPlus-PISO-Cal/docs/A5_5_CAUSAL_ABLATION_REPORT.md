# A5.5 causal ablation report

`A5_5_GATE=PASS`; `ABLATION_RESULT=PARTIAL`.

This preregistered experiment tests whether the frozen A2 region adds value beyond a single A2-centre point warm start and beyond a generic 16-point global initialization. The preregistration was frozen before A6 result review and was not changed after A6.

## Scope and frozen design

New arms are `DDS_POINT_AI, DDS_RANDOM_SOFT` with ten paired seeds `20260906–20260915`, 250 evaluations per seed, SWAT+ rev.62, warm-up 2000–2002, development objective 2003–2016, formal 14-D bounds, and DDS sigma 0.2. The new arms required exactly `5000` fresh development Real-SWAT evaluations.

DDS_POINT_AI uses the frozen A2 centre at evaluation 1 and exact global DDS from evaluation 2 onward. DDS_RANDOM_SOFT uses 16 deterministic scrambled Sobol points in normalized formal 14-D space, seeded by the paired seed, then exact global DDS from evaluation 17 onward using the best first-16 development objective as incumbent.

A5 DDS_GLOBAL and DDS_SOFT_AI rows are reused from the complete A5 results ledger and are not recalculated. DDS_HARD_AI is cited only as auxiliary A3 mechanism evidence and is not pooled with this ten-seed confirmatory comparison.

## Anytime and final summaries

AUC is the A5 best-so-far development mean-NSE curve integrated over evaluations 1–250 and normalized by 249. Values below are ten-seed summaries; all paired deltas are right arm minus left arm.

| arm | AUC mean | AUC median | AUC std | final-best mean NSE | final-best median | final-best std |
|---|---:|---:|---:|---:|---:|---:|
| DDS_GLOBAL | 0.496446 | 0.496650 | 0.014862 | 0.532901 | 0.534119 | 0.017689 |
| DDS_POINT_AI | 0.496642 | 0.500270 | 0.016052 | 0.524825 | 0.524552 | 0.017886 |
| DDS_RANDOM_SOFT | 0.500761 | 0.501376 | 0.007217 | 0.532212 | 0.533740 | 0.013765 |
| DDS_SOFT_AI | 0.510007 | 0.507630 | 0.013817 | 0.536573 | 0.534590 | 0.013816 |

### Best-so-far development mean NSE at frozen nodes

| arm | eval 25 | eval 50 | eval 100 | eval 150 | eval 200 | eval 250 |
|---|---:|---:|---:|---:|---:|---:|
| DDS_GLOBAL | 0.432741 | 0.491079 | 0.510939 | 0.522408 | 0.528693 | 0.532901 |
| DDS_POINT_AI | 0.459676 | 0.489873 | 0.504149 | 0.512314 | 0.517775 | 0.524825 |
| DDS_RANDOM_SOFT | 0.452902 | 0.495864 | 0.512872 | 0.521824 | 0.527012 | 0.532212 |
| DDS_SOFT_AI | 0.472898 | 0.501498 | 0.517847 | 0.527081 | 0.534094 | 0.536573 |

### Evaluations to threshold

| arm | 0.50 median | 0.52 median | 0.54 median | 0.55 median |
|---|---:|---:|---:|---:|
| DDS_GLOBAL | 80 | 116.5 | 103.5 | 111 |
| DDS_POINT_AI | 67 | 136 | 142 | 174 |
| DDS_RANDOM_SOFT | 56.5 | 127 | 226 | 248 |
| DDS_SOFT_AI | 51.5 | 86 | 130 | 185.5 |

## Prespecified paired comparisons

Bootstrap uses 20,000 paired-seed resamples with the seeds frozen in the preregistration.

| comparison (right-left) | AUC delta mean | AUC 95% CI | AUC wins/ties/losses | final delta mean | final 95% CI | final wins/ties/losses |
|---|---:|---|---|---:|---|---|
| DDS_POINT_AI - DDS_GLOBAL | -0.000196 | [-0.015710, 0.014430] | 6/0/4 | 0.008076 | [-0.009413, 0.025449] | 7/0/3 |
| DDS_SOFT_AI - DDS_POINT_AI | 0.013365 | [-0.000083, 0.027769] | 7/0/3 | 0.011748 | [-0.001959, 0.028415] | 7/0/3 |
| DDS_RANDOM_SOFT - DDS_GLOBAL | 0.004316 | [-0.005373, 0.014338] | 6/0/4 | -0.000689 | [-0.017607, 0.016243] | 5/0/5 |
| DDS_SOFT_AI - DDS_RANDOM_SOFT | 0.009245 | [0.000656, 0.019430] | 8/0/2 | 0.004361 | [-0.007019, 0.017401] | 5/0/5 |

## Causal ablation decision

`REGION_GUIDANCE_VALUE=SUPPORTED`. This compares SOFT_AI against POINT_AI.
`AI_INFORMATION_VALUE=CONFIRMED`. This compares SOFT_AI against RANDOM_SOFT.
`ABLATION_RESULT=PARTIAL`. SOFT_AI 250-evaluation final no-stable-degradation check: `True`.

POINT_WARMSTART_VALUE is report-only and is not used to retune any arm.

## Data leakage and recovery audit

| item | result |
|---|---|
| validation observations read | NO |
| final-test observations read | NO |
| A6 validation objective used for candidates | NO |
| A5 GLOBAL/SOFT_AI recalculated | NO |
| A2/A3/A4/A5 historical objective used to warm-start new arms | NO |
| BIOS/driver/power-plan change | NO |
| completed evaluation rerun on resume | NO; formal ledger replay only |

Every successful new evaluation is persisted to the formal ledger with flush/fsync before atomic checkpoint and heartbeat updates. Checkpoints use temporary file, fsync, and atomic rename.

## Artifacts

- `results.csv`: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a5_5\results.csv`
- `A5_5_GATE.json`: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a5_5\A5_5_GATE.json`
- preregistration: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a5_5\A5_5_PREREG.json`
- local qsim/runtime: `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a5_5\qsim` / `D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal\artifacts\a5_5\runtime`
