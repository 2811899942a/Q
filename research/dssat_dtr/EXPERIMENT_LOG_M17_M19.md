# DSSAT regional-temperature experiment log: M17 -> M19

Purpose: preserve formulas, run IDs, failures, fixes, quantitative results and scientific decisions so the research chain can be reproduced without relying on chat history.

## E17 — regional DTR x radiation monotonic warp

Core exposure:

`E = max(z_DTR-q,0) * max(Kt0-Kt,0) / 0.1`

M17 used an unbounded shape exponent `exp(kE)` while constraining the generated temperature curve to physically valid Tmin/Tmax and monotonic shoulders.

Legacy validation result:
- overall RMSE: 2.6832 C
- DTR>=15 C RMSE: 4.3286 C
- improvement vs official HTEMP: 8.95% overall / 15.48% high-DTR
- full-curve high-DTR physical violations: 0/123
- issue: `k_pre=9.999994`, at search upper bound 10.

Decision: continue boundary audit; no parameter freeze.

## E17b — expanded boundary audit

Expanded `k_pre` and `k_post` upper bound to 40 while preserving the M17 exposure definition.

Result:
- `k_pre ~= 40`, `k_post ~= 40`: both at upper bound
- overall RMSE: 2.5832 C
- DTR>=15 C RMSE: 4.3768 C
- full-curve physical violations: 0/123
- 2020-2024 high-DTR annual RMSE: improved vs official in every year, approximately 12%-20%.

Decision: retain M17b as the strongest temperature-fit/performance candidate. The unbounded response coefficient is not sufficiently identifiable for the transferable regional parameter.

## E18 — bounded regional response-amplitude coefficient

Formula:

`G = E/(1+E)`

`S = K_RT * G`

`q_new = (1-S)*q_temp + S*q_temp^P_MAX`

`K_RT in [0,1]`; `K_RT=0` retains official HTEMP.

Implementation note: the first CI version was computationally inefficient because scalar optimization was repeated across folds. Since the prediction is affine in `K_RT`, the fit was replaced by exact bounded least squares:

`T_new = T_official + K_RT*delta`

Successful GitHub Actions run: `33949861407`.
Results commit: `ca7fa9f38702497eb25e02b01cc6fb55a9106c4a`.

Result:
- q = 0.0
- Kt0 = 0.7
- P_MAX = 20.0
- K_RT = 1.00000000, at boundary
- legacy overall RMSE: 2.789879 C, 5.33% improvement vs official
- legacy high-DTR RMSE: 4.776875 C, 6.73% improvement
- physical violations: 0/123
- annual high-DTR wins vs official: 5/5
- gate vs M15 high-DTR benchmark: FAIL

Decision: bounded physical response is feasible; regional response-amplitude coefficient remains poorly identifiable. Demote amplitude K_RT as the main transferable parameter.

## E19 — regional standardized DTR anomaly trigger

Regional parameter was redefined as a trigger threshold:

`K_RT = local seasonally standardized DTR anomaly threshold, in SD`

Formula:

`E = max(z_DTR-K_RT,0) * max(Kt0-Kt,0) / 0.1`

`S = 1-exp(-E/gain_scale)`

`q_new = (1-S)*q_temp + S*q_temp^P_TARGET`

Fixed structural values in the exploratory screen:
- Kt0 = 0.70
- P_TARGET = 20.0
- selected gain_scale = 0.25

Successful GitHub Actions run: `33949998528`.

Result:
- K_RT = **1.40 SD**, inside the -2 to +3 SD screen
- legacy overall RMSE: 2.833762 C, 3.84% improvement vs official
- legacy high-DTR RMSE: 4.742319 C, 7.40% improvement
- physical violations: 0/123
- annual high-DTR wins vs official: 5/5
- inactive trigger closure max absolute error: 0.000e+00 C
- temperature gate vs frozen M15: FAIL

Decision: promote M19 as the **transferable parameter architecture candidate**. Its value is the interpretable regional trigger parameter and exact neutral closure. M17b remains the **temperature-fit performance candidate**. These roles are intentionally separate.

## E19-SRC — source-level DSSAT propagation

Source lock:
- DSSAT source commit: `0b91373806786b600d89ccfcfff78fa2f82cb26b`
- DSSAT data commit: `79cb5db71bbca186add92a6a9695866a09c8b51d`

Source insertion:
1. `WEATHR` passes DOY into `HMET`.
2. `HMET` executes official `HTEMP` first.
3. `HTEMP_M19` conditionally modifies the physically constrained pre-peak and peak-to-sunset shoulders.
4. M19 uses tracked Urumqi 2000-2016 366-day DTR mean/SD profile plus daily SRAD/latitude to compute the trigger.
5. Result propagates through `TAIRHR/TGRO` into CERES-Maize.

First workflow `33950104916`: FAIL before compilation. Protection check assumed one `CALL HMET` in `Weather/weathr.for`; frozen v4.8.5 contains two legitimate call sites. M15 patch succeeded; M19 intentionally stopped with `expected exactly one ... found 2`.

Fix: `apply_m19_htemp_patch_2call.py` keeps all original patch logic but requires exactly two frozen WEATHR call sites and patches both. This is a source-version guard correction, not a model-formula change.

Corrected end-to-end workflow: `Anningqu M0 M15 M19 Crop Propagation V2`, run ID `33950231315` at log creation time. Final compile/run/output status must be appended only after the complete workflow finishes.

## Windows reproduction assets

Folder: `repro/windows_dssat_temperature_v1/`

Tracked files include:
- `environment_check.ps1`
- `requirements.txt`
- `run_temperature_only.ps1`
- `run_full_crop_ab.ps1`
- `parse_crop_ab.py`
- `README_WINDOWS.md`

Reproduction philosophy: exact Linux/Windows floating-point equality is secondary. Required invariants are the same formula/parameter definition, neutral closure, physical validity, successful DSSAT source compilation/execution, and reproducible propagation direction into crop outputs.
