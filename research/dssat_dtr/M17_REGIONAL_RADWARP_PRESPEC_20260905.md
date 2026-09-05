# M17 Regional Radiative Monotonic Warp — preregistered temperature screen

Date: 2026-09-05. This file is committed before M17 validation outputs.

## Goal
Recover the reproducible DTR × radiative-deficit signal identified by M10/M12 while preserving a physically valid complete diurnal curve and replacing a fixed absolute DTR trigger with a local seasonal anomaly. This is a temperature-only screen. Crop outcomes cannot select the temperature structure or parameters.

## Fixed comparators and hard gate
Legacy primary-station 2017–2024 May–Sep benchmark, with the frozen formal DTR classification, is retained as a historical benchmark rather than a fresh final test.

Reference values already obtained before this screen:
- M15-13.5: overall RMSE 2.796224 C; formal DTR>=15 RMSE 4.634433 C.
- M15-13.8: overall RMSE 2.801549 C; formal DTR>=15 RMSE 4.635762 C.
- M12 statistical prototype: overall RMSE 2.7639 C; high-DTR RMSE 4.4623 C, but complete-curve physical violations prohibit source promotion.

M17 advances only if all are satisfied on the legacy benchmark:
1. overall RMSE < 2.7639 C;
2. formal DTR>=15 RMSE < 4.4623 C;
3. zero Tmin/Tmax bound violations and zero pre/post monotonicity violations on the full 24-h diagnostic grid;
4. no validation year with high-DTR observations is materially worse than frozen M15-13.5 (>0.10 C RMSE increase).
This is an internal development gate, not evidence of independent final validation.

## Candidate formula family
Daily local thermal-structure anomaly:

z_DTR(d) = [DTR(d) - mu_DTR(DOY)] / sigma_DTR(DOY)

where mu and sigma are calculated only from the training years with a +/-15-day seasonal window. sigma has a 0.5 C lower bound for numerical stability.

Daily radiative deficit follows the previously audited M10 definition:

Kt = SRAD / Ra; Rdef = max(0, Kt0-Kt)/0.1.

The activation exposure is

E = max(z_DTR-q,0) * Rdef.

The original Parton–Logan temperature is converted to normalized progress qT between fixed segment endpoints. The corrected progress is

qT_new = qT ^ exp(k * E), k >= 0.

The exponent is constant within each daily segment, which preserves ordering and both segment endpoints. Separate k_pre and k_post are fitted for the robust calibration-derived H0→Tmax and Tmax→sunset segments. H0=10.455 solar hour is frozen from the prior calibration-only M14 diagnostic; no validation outcome can move H0.

Candidate discrete structures:
- regional anomaly q in {0.0, 0.5, 1.0};
- radiative taper Kt0 in {0.60, 0.70, 0.80, 0.90}.
For every leave-one-year-out calibration fold, the seasonal DTR profile is rebuilt from training years only, k_pre/k_post are refitted on training observations only, and the held-out year is predicted.

Selection rule: among candidates with pooled calibration LOYO overall RMSE no worse than official HTEMP, select minimum formal-high-DTR LOYO RMSE; ties are broken by lower overall RMSE, fewer/lower parameters, then lower q and Kt0. All candidate outcomes are preserved.

## Interpretation
The source-level innovation candidate is the combination of: region/season-relative DTR state, radiative modulation using weather already represented by DSSAT, constrained deformation of the HTEMP intraday curve, and explicit propagation into crop-model hourly temperature. Standardization, radiative deficit, and monotonic warping are individually established techniques; novelty claims require literature and patent claim comparison of the full combination and implementation position.
