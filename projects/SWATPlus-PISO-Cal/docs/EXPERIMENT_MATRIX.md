# Frozen experiment matrix

## A. Published-method reproduction

| ID | Dataset | Model | Purpose |
|---|---|---|---|
| R0-A | Public DL4SWAT | Clean-room 1D CNN | Reproduce deterministic inverse calibration |
| R0-B | Public DL4SWAT | Published preprocessing variants | Sensitivity to scaling and train size |

## B. South Branch inverse encoder screen

All models receive identical simulation splits and loss definitions.

| ID | Encoder | Head | Seeds |
|---|---|---|---|
| R1-CNN | 1D CNN | bounded point estimate | 42, 2026, 3407 |
| R1-TCN | TCN | bounded point estimate | 42, 2026, 3407 |
| R1-BLSTM | BiLSTM | bounded point estimate | 42, 2026, 3407 |
| R1-PTR | patch Transformer | bounded point estimate | 42, 2026, 3407 |

Keep only the top two encoders. Encoder ranking is an engineering screen, not the claimed innovation.

## C. Posterior models

| ID | Encoder | Density head | Required diagnostics |
|---|---|---|---|
| R2-MAF | top encoder | MAF | SBC, coverage, TARP, PPC |
| R2-NSF | top encoder | NSF | same |
| R2-ALT | second encoder | best density | same |

Gaussian and MDN heads are optional diagnostic baselines. They are not required if MAF/NSF already reveal posterior failure.

## D. Misspecification experiments

Create controlled pseudo-observations with increasing mismatch:

1. in-distribution held-out SWAT+ simulation;
2. forcing perturbation;
3. additive and multiplicative observation noise;
4. structural proxy created by withholding a process/parameter block or using an alternate SWAT+ setup;
5. real USGS observation.

For each level, evaluate posterior calibration, posterior predictive skill, OOD score, and the safe posterior mixture weight. The trust schedule is chosen here and frozen before R4.

## E. Fresh Real-SWAT+ pilot

Common initial Sobol design: 42 evaluations per seed.
Total budget: 198 evaluations per method and seed.

| Method | Learned prior | Online optimizer | Role |
|---|---|---|---|
| DDS | no | DDS | mature baseline |
| TuRBO | no | local BO/TR | strongest surrogate baseline |
| Point-Warm-TuRBO | point inverse | TuRBO | simple learned warm-start ablation |
| Posterior-Only | NPE | posterior sampling | isolates inverse posterior value |
| PISO-Cal | OOD-weighted NPE | TuRBO + posterior candidate | proposed method |

The decisive primary comparison is TuRBO vs PISO-Cal. DDS establishes operational value. Point-Warm-TuRBO identifies whether the full posterior adds value beyond one learned initial point.

## F. Data provenance constraint

Primary South Branch inverse/posterior training uses only observation-independent broad samples. DeepCal/DDS/DE/BO trajectories are excluded because their parameter distribution was selected using Qobs. A separate asset-reuse analysis may include them with their full generation cost and explicit target-information label.
