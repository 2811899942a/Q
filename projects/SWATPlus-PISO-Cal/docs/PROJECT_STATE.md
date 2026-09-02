# Project state — 2026-09-02

## Formal research lock

- Only study area: South Branch Potomac A basin.
- Existing SWAT+ rev.62 project is retained; no watershed rebuild.
- Gauges: 01605500/ch12, 01606000/ch17, 01606500/ch18.
- Formal parameter dimension: existing 14D.
- Development: 2003–2016.
- Locked validation: 2017–2020.
- Final test: 2021–2024.
- DL4SWAT paper watershed is a method reference/optional implementation check only.

## Historical evidence that motivates the new route

Values below are project-history pointers and must be reverified from local artifacts in A0 before formal reporting:

- pseudo-target DeepCal previously reached about 0.92, but real-USGS DeepCal was about 0.506;
- DDS under the comparable 14D/200-evaluation setting reached about 0.557;
- dynamic-subspace/diagnosis steering did not add value in archive ablation;
- archive has about 7400 rows: about 5000 broad samples plus about 2400 observed-directed optimizer traces;
- broad pool maximum was only about 0.496, while optimizer traces contain target-enriched high-quality regions;
- therefore observed-directed rows cannot be mixed into the primary offline inverse/posterior training library.

## Repository code now present

- generic data contract and train-only scaler;
- hard A-basin study specification (`study_area.py`);
- strict formal A-basin loader (`load_south_branch_dataset`);
- CNN/TCN/BiLSTM/Patch Transformer encoders;
- point inverse head and NPE interface;
- OOD/proposal/sequential scaffolds;
- generic Real-SWAT+ isolated runner;
- SouthBranchLegacyAdapter to reuse the established A-basin writer/parser;
- tests for study-area lock and adapter shape/equivalence rules.

## Still requires target-machine execution

1. A0 scan of `D:/SWAT+_3V3/A_SouthBranchPotomac/`;
2. identify the current canonical project/runner rather than assuming an old subfolder;
3. freeze and hash the actual 14D parameter dictionary and objective implementation;
4. classify every archive row by provenance;
5. build the formal A-basin data contract;
6. connect the established writer/parser through SouthBranchLegacyAdapter;
7. run one-candidate old/new daily equivalence and objective-equivalence test;
8. only then run A1 deterministic inverse models;
9. A2/A3/A4 follow the decision gates.

## Claims currently supported

The repository is a research scaffold and execution protocol. No claim of improved calibration accuracy or efficiency is allowed before A4 fresh Real-SWAT+ PASS.
