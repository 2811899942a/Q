# Verified project state

## Verified in the build environment

- Package source imports under the base dependency set.
- Data-contract validation, hydrological metrics, proposal mixing, kNN OOD diagnostic, and all four encoder forward passes have unit tests.
- The patch-based Transformer avoids quadratic attention over the full 5,000-day sequence.
- The generic sequential loop and isolated Real-SWAT+ runner interfaces compile.
- Public DL4SWAT data metadata identify an 858.5 MB `Data.zip` with MD5 `d9547cebe2a6607dec5355a45296d5bd`.

## Still requires execution in the target environment

- Install and smoke-test `sbi==0.27.0` under the pinned Python environment.
- Download and unpack the complete DL4SWAT dataset.
- Reproduce the published deterministic CNN workflow.
- Connect the existing South Branch parameter writer and output parser to `RealSWATRunner`.
- Execute one real candidate end to end and verify exact equality with the established SWAT+ workflow.
- Implement and validate DDS and TuRBO wrappers under the shared budget accountant.
- Calibrate the posterior-trust schedule through synthetic misspecification tests.
- Run fresh paired-seed Real-SWAT+ experiments.

## Claims currently supported

The repository is an executable research scaffold and frozen protocol. It is not yet a completed reproduction or a validated calibration algorithm. No accuracy or efficiency gain is claimed before Gate R4.
