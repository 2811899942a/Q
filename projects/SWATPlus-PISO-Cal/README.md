# SWATPlus-PISO-Cal

**Posterior-Informed Sequential Optimization for fast and accurate SWAT+ calibration.**

This is a clean-room research implementation scaffold. It combines three validated ideas while keeping their roles separate:

1. deterministic inverse calibration inspired by DL4SWAT;
2. neural posterior estimation for multi-modal parameter proposals;
3. real-observation-driven sequential optimization for final calibration.

The core safety rule is that the neural posterior is a **proposal prior**, not the final judge. Every accepted parameter set must be rerun by Real-SWAT+ and scored against the observed multi-gauge objective.

## Current project status

- Research protocol: frozen for the first decisive experiment.
- Source code: runnable scaffold with tested data, metrics, encoders, proposal mixing, and sequential-loop interfaces.
- Real SWAT+ adapter: command-template implementation included; project-specific parameter writing and output parsing remain to be connected to the existing South Branch workflow.
- Published-code policy: no unlicensed DL4SWAT source code is copied. Public data are downloaded from the authors' CC BY 4.0 Zenodo record and the method is reimplemented from the paper.

## Scientific question

Can a simulation-trained, multi-gauge posterior reduce the number of fresh Real-SWAT+ evaluations needed to reach a target calibration skill, after an explicit misspecification check and observed-objective sequential correction?

## Mandatory baselines

- DDS
- TuRBO or equivalent local Bayesian optimization
- DL4SWAT-style deterministic CNN inverse model
- posterior-only candidate search
- PISO-Cal: posterior proposal + observed-objective sequential search

## Data contract

See `docs/DATA_CONTRACT.md`.

```text
theta.npy        [N, P]
qsim.npy         [N, G, T]
qobs.npy         [G, T]
parameter_bounds.csv
metadata.json
```

For the South Branch project, `P=14`, `G=3`, and the gauges are 01605500, 01606000, and 01606500.

## Environment

Python 3.11 is the reference environment.

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows
python -m pip install -U pip
python -m pip install -e ".[dev,sbi]"
pytest -q
```

The optional SBI dependency is pinned to `sbi==0.27.0` in the project metadata.

## Fast smoke test

```bash
python scripts/run_toy_smoke.py
```

## Execution order

1. Download and inspect the public DL4SWAT dataset.
2. Reproduce the deterministic CNN baseline with a clean-room implementation.
3. Convert South Branch simulations into the project data contract.
4. Compare CNN, TCN, BiLSTM, and a small Transformer under identical splits.
5. Train the top encoder with a neural posterior estimator.
6. Run posterior diagnostics on held-out synthetic targets.
7. Measure observation misspecification/OOD for the real USGS sequence.
8. Run the fresh Real-SWAT+ pilot: DDS vs TuRBO vs PISO-Cal.
9. Apply the decision gates before any expansion.

The detailed protocol and handoff instructions are in `docs/RESEARCH_FRAMEWORK_ZH.md` and `docs/HANDOFF_NEXT_CHAT_ZH.md`.
