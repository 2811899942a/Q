# Core literature matrix

| Component | Primary source | What has already been demonstrated | Role in this project |
|---|---|---|---|
| Deterministic SWAT inverse calibration | Mudunuru et al. (2022), Frontiers in Earth Science, DOI 10.3389/feart.2022.1026479 | CNN maps streamflow to 20 SWAT parameters and was compared with DDS and GLUE | Public reproduction anchor and point-estimate baseline |
| Public reproduction data | Zenodo 10.5281/zenodo.7271945 | 1000 SWAT realizations, official 80/10/10 split, ARW observations WY2000–2016 | Clean-room R0 dataset |
| Hydrologic SBI and misspecification | Hull et al. (2024), HESS, DOI 10.5194/hess-28-4685-2024 | Neural density estimation of parameter posteriors; synthetic experiments expose unreliable inference under simulator mismatch | Posterior and misspecification rationale |
| SBI software | Boelts et al. (2025), JOSS, DOI 10.21105/joss.07754; sbi-dev/sbi | NPE and sequential SBI implementations plus SBC, TARP and coverage diagnostics | Production posterior implementation |
| Local Bayesian optimization | Eriksson et al. (2019), NeurIPS, TuRBO | Local probabilistic trust regions for sample-efficient expensive black-box optimization | Strong online optimization baseline and PISO backbone |

## Novelty boundary

The project does not claim novelty for CNN encoders, normalizing flows, NPE, TuRBO, or multi-gauge calibration individually.

The testable methodological contribution is the following complete bridge:

```text
multi-gauge SWAT+ simulation posterior
+ explicit simulator–observation support diagnostic
+ guarded posterior trust
+ fresh observed-objective Real-SWAT+ sequential optimization
+ complete offline/online/total cost accounting
```

A claim of innovation is allowed only after PISO-Cal beats the matched TuRBO baseline under the frozen fresh-evaluation protocol.
