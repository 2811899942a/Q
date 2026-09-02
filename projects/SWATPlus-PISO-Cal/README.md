# SWATPlus-PISO-Cal

**Posterior-Informed Sequential Optimization for fast and accurate SWAT+ calibration.**

## Study-area lock

The formal study area is **A basin = South Branch Potomac**, using the existing SWAT+ rev.62 project and the three long-used USGS gauges:

- 01605500 (ch12)
- 01606000 (ch17)
- 01606500 (ch18)

Time split remains fixed:

- 2000–2002: warm-up/context
- 2003–2016: development and method construction
- 2017–2020: locked validation
- 2021–2024: final test

The published DL4SWAT watershed is **not** the target study area and must not replace the South Branch project. DL4SWAT is used only as a methodological reproduction/reference framework for deep-learning-based inverse calibration.

## Methodological lineage

This clean-room research scaffold combines three validated ideas while keeping their roles separate:

1. deterministic inverse calibration inspired by DL4SWAT;
2. neural posterior estimation for multi-modal parameter proposals;
3. real-observation-driven sequential optimization for final A-basin calibration.

The core safety rule is that the neural posterior is a **proposal prior**, not the final judge. Every accepted parameter set must be rerun by the existing South Branch Real-SWAT+ workflow and scored against the frozen three-gauge observed objective.

## Current project status

- Research basin: locked to South Branch Potomac A basin.
- Parameter space: existing 14D A-basin calibration space; do not expand during the first decisive experiment.
- Research protocol: frozen for the first decisive experiment.
- Source code: runnable scaffold with tested data, metrics, encoders, proposal mixing, and sequential-loop interfaces.
- Real SWAT+ adapter: project-specific parameter writing and output parsing must be connected to the existing South Branch workflow rather than rebuilt from another basin.
- Published-code policy: no unlicensed DL4SWAT source code is copied. The paper/public dataset may be used only for clean-room implementation verification.

## Scientific question

Can a simulation-trained, multi-gauge deep-learning posterior reduce the number of fresh Real-SWAT+ evaluations needed to calibrate the existing South Branch Potomac SWAT+ model to the three USGS gauges, while reaching equal or higher accuracy than DDS/TuRBO?

## Mandatory baselines

- DDS
- TuRBO or equivalent local Bayesian optimization
- DL4SWAT-style deterministic inverse model transferred/reimplemented for the A-basin data contract
- posterior-only candidate search
- PISO-Cal: posterior proposal + observed-objective sequential search

## A-basin data contract

See `docs/DATA_CONTRACT.md`.

```text
theta.npy        [N, P]
qsim.npy         [N, G, T]
qobs.npy         [G, T]
parameter_bounds.csv
metadata.json
```

For the formal study, `P=14`, `G=3`, and the gauges are 01605500, 01606000, and 01606500.

## Public-paper reproduction role

The DL4SWAT public data can be used for one purpose only: verify that the clean-room inverse-calibration implementation behaves consistently with a published method. This is an implementation sanity check, not a substitute study area and not a source of training information for the South Branch formal experiment.

No published-paper watershed inputs are mixed into the A-basin training archive, posterior, calibration objective, validation, or final test.

## Environment

Python 3.11–3.12 is the reference range.

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

1. Audit and lock the existing South Branch A-basin SWAT+ project, 14D parameter definition, three-gauge objective, and existing Real-SWAT+ runner.
2. Optionally run the public DL4SWAT clean-room reproduction as an implementation verification; do not rebuild its watershed.
3. Convert the existing South Branch broad simulations into the project data contract and strictly separate observation-independent broad samples from observed-directed optimization traces.
4. Reproduce the DL4SWAT-style deterministic inverse-calibration idea directly on A-basin simulations and compare CNN, TCN, BiLSTM, and a small Transformer under identical splits.
5. Train the top encoder with a neural posterior estimator using only A-basin observation-independent simulations.
6. Run posterior diagnostics on held-out A-basin synthetic targets.
7. Measure simulation-to-real-observation misspecification/OOD for the three real USGS sequences.
8. Run the fresh A-basin Real-SWAT+ pilot: DDS vs TuRBO vs PISO-Cal.
9. Apply the decision gates before any expansion.

The detailed protocol and handoff instructions are in `docs/RESEARCH_FRAMEWORK_ZH.md` and `docs/HANDOFF_NEXT_CHAT_ZH.md`.
