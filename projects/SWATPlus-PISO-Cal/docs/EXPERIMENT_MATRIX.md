# Frozen experiment matrix — South Branch Potomac A basin

## A0. Takeover audit

No new large batch. Audit existing model, 14D parameter semantics, observations, objective, archives, and old/new runner equivalence.

## Optional P0. Published-method sanity check

| ID | Dataset | Model | Role |
|---|---|---|---|
| P0-CNN | Public DL4SWAT | clean-room 1D CNN | implementation sanity check only |

P0 is not the formal study and does not gate A0/A1.

## A1. A-basin deterministic inverse encoder screen

All models use the same observation-independent A-basin broad simulations, realization split, scaler rules, parameter bounds, and seeds.

| ID | Encoder | Head | Seeds |
|---|---|---|---|
| A1-CNN | 1D CNN | bounded point estimate | 42, 2026, 3407 |
| A1-TCN | TCN | bounded point estimate | 42, 2026, 3407 |
| A1-BLSTM | BiLSTM | bounded point estimate | 42, 2026, 3407 |
| A1-PTR | patch Transformer | bounded point estimate | 42, 2026, 3407 |

Keep top two. Encoder ranking is an engineering screen, not the claimed methodological innovation.

Training-size analysis uses nested observation-independent subsets where provenance permits: 250/500/1000/2500/5000.

## A2. Posterior models

| ID | Encoder | Density | Diagnostics |
|---|---|---|---|
| A2-MAF | top encoder | MAF | SBC, coverage, TARP, PPC |
| A2-NSF | top encoder | NSF | same |
| A2-ALT | second encoder | best density | same |

## A3. Misspecification experiments

Increasing mismatch:

1. held-out in-distribution A-basin SWAT+ simulation;
2. additive/multiplicative observation noise;
3. forcing perturbation;
4. predeclared structural proxy mismatch if reproducible without touching locked periods;
5. real 2003–2016 USGS observation.

Freeze posterior trust rule before A4.

## A4. Fresh Real-SWAT+ pilot

Common initial Sobol design: 42 evaluations/seed. Total budget: 198 evaluations/method/seed. Three paired seeds.

| Method | Learned information | Online mechanism | Scientific role |
|---|---|---|---|
| DDS | none | DDS | mature operational baseline |
| TuRBO | none | local BO/TR | strongest matched surrogate baseline |
| Point-Warm-TuRBO | A1 point inverse | TuRBO | tests whether one learned start is enough |
| Posterior-Only | A2 NPE | posterior sampling | isolates posterior quality |
| PISO-Cal | A2 NPE + A3 trust | TuRBO + guarded posterior proposal | proposed method |

Primary causal comparison: PISO-Cal vs TuRBO. Secondary: Point-Warm-TuRBO vs PISO-Cal.

## Provenance constraint

Formal A1/A2 training excludes every parameter vector selected using the real USGS objective. Historical DeepCal/DDS/DE/BO/TuRBO traces remain diagnostic-only unless a separate asset-reuse experiment explicitly counts their generation cost and target-information advantage.
