#!/usr/bin/env python3
"""M18: bounded, physically constrained regional DTR x radiation HTEMP shape model.

Purpose
-------
Retain the M17 regional exposure signal while removing the unbounded exp(k*E)
coefficient that saturated at the numerical search ceiling in M17/M17b.

Regional coefficient
--------------------
K_RT is constrained to [0, 1]. K_RT=0 reproduces official HTEMP exactly on the
modified shoulder segments. For an active point:

    E = max(z_DTR-q, 0) * max(Kt0-Kt, 0) / 0.1
    G = E / (1 + E)
    S = K_RT * G
    q_target = q_temp ** P_MAX
    q_new = (1-S)*q_temp + S*q_target

P_MAX is a structural hyperparameter selected only by 2000-2016 leave-one-year-
out CV together with q and Kt0. Only K_RT is continuously fitted for the region.
The convex blend keeps q_new in [0,1], preserves Tmin/Tmax anchors, and preserves
monotonicity when the official branch is monotonic.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

HERE = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location(
    "m17base", HERE.with_name("m17_regional_radiative_monotonic_warp.py")
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

OUT = m.ROOT / "data" / "m18_bounded_regional_shape"
QGRID = [0.0, 0.5, 1.0]
KTGRID = [0.60, 0.70, 0.80, 0.90]
PMAXGRID = [2.0, 3.0, 5.0, 8.0, 12.0, 20.0]
KBOUND = (0.0, 1.0)


def write(name, rows):
    if not rows:
        return
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def bounded_gain(e):
    """Monotone bounded exposure activation in [0,1)."""
    return e / (1.0 + e) if e > 0 else 0.0


def pred(r, prof, q, kt0, pmax, krt):
    br, qt, lo, hi = m.segment(r)
    if br == "none":
        return r["p0"]
    e = m.exposure(r, prof, q, kt0)
    if e <= 0:
        return r["p0"]
    g = bounded_gain(e)
    s = min(max(krt * g, 0.0), 1.0)
    qtarget = qt ** pmax
    qnew = (1.0 - s) * qt + s * qtarget
    return lo + (hi - lo) * qnew


def fit_krt(rows, prof, q, kt0, pmax):
    active = [
        r for r in rows
        if m.segment(r)[0] != "none" and m.exposure(r, prof, q, kt0) > 0
    ]
    if not active:
        return 0.0

    def loss(krt):
        return m.mean([
            (pred(r, prof, q, kt0, pmax, krt) - r["obs"]) ** 2
            for r in active
        ])

    z = minimize_scalar(
        loss, bounds=KBOUND, method="bounded", options={"xatol": 1e-7}
    )
    return float(z.x)


def metrics(rows, pf):
    err = [pf(r) - r["obs"] for r in rows]
    return {
        "n": len(err),
        "rmse": math.sqrt(m.mean([x * x for x in err])),
        "mae": m.mean([abs(x) for x in err]),
        "bias": m.mean(err),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, daily = m.enrich()
    cal = [r for r in rows if r["year"] <= 2016]
    val = [r for r in rows if r["year"] >= 2017]
    years = sorted(set(r["year"] for r in cal))

    # Structural selection is calibration-only leave-one-year-out CV.
    cv = []
    for q in QGRID:
        for kt0 in KTGRID:
            for pmax in PMAXGRID:
                held = []
                fold_ks = []
                for y in years:
                    tr = [r for r in cal if r["year"] != y]
                    te = [r for r in cal if r["year"] == y]
                    pf = m.profile(daily, set(years) - {y})
                    krt = fit_krt(tr, pf, q, kt0, pmax)
                    fold_ks.append(krt)
                    for r in te:
                        held.append((r, pred(r, pf, q, kt0, pmax, krt)))
                ee = [p - r["obs"] for r, p in held]
                high = [(r, p) for r, p in held if r["formal_dtr"] >= 15]
                cv.append({
                    "q": q,
                    "kt0": kt0,
                    "pmax": pmax,
                    "cv_all_rmse": math.sqrt(m.mean([x * x for x in ee])),
                    "cv_high_rmse": math.sqrt(m.mean([
                        (p - r["obs"]) ** 2 for r, p in high
                    ])),
                    "mean_fold_krt": m.mean(fold_ks),
                    "max_fold_krt": max(fold_ks),
                    "boundary_fold_count": sum(k >= 0.995 for k in fold_ks),
                    "n": len(held),
                    "n_high": len(high),
                })

    official_cal_rmse = metrics(cal, lambda r: r["p0"])["rmse"]
    feasible = [x for x in cv if x["cv_all_rmse"] <= official_cal_rmse + 1e-12]
    pool = feasible if feasible else cv
    # Primary objective remains high-DTR error; then overall error, then simpler shape.
    best = min(
        pool,
        key=lambda x: (
            x["cv_high_rmse"], x["cv_all_rmse"],
            x["boundary_fold_count"], x["pmax"], x["q"], x["kt0"]
        ),
    )

    pf = m.profile(daily, set(years))
    krt = fit_krt(cal, pf, best["q"], best["kt0"], best["pmax"])

    official = lambda r: r["p0"]
    model = lambda r: pred(
        r, pf, best["q"], best["kt0"], best["pmax"], krt
    )

    res = []
    byyear = []
    for name, fn in {"OFFICIAL": official, "M18": model}.items():
        for group, rr in [
            ("MaySep", val),
            ("DTR_GE15", [r for r in val if r["formal_dtr"] >= 15]),
        ]:
            res.append({"model": name, "group": group, **metrics(rr, fn)})
        for y in sorted(set(r["year"] for r in val)):
            rr = [r for r in val if r["year"] == y and r["formal_dtr"] >= 15]
            if rr:
                byyear.append({"model": name, "year": y, **metrics(rr, fn)})

    # Full 24-h physical constraints on every high-DTR validation day.
    checks = []
    bydate = {r["solar_date"]: r for r in rows}
    for ds, r in bydate.items():
        if r["year"] < 2017 or r["formal_dtr"] < 15:
            continue
        mx = r["su"] + m.C + r["dl"] / 2 + m.A
        grid = np.arange(0, 24.0001, 0.05)
        vals = []
        for h in grid:
            fake = dict(r)
            fake["h"] = float(h)
            fake["p0"] = m.pl(
                h, r["tx"], r["tn"], r["dl"], r["su"], r["sd"]
            )
            vals.append((h, model(fake)))
        rise = [v for v in vals if r["su"] + m.C <= v[0] <= mx]
        fall = [v for v in vals if mx <= v[0] <= r["sd"]]
        rd = np.diff([v[1] for v in rise])
        fd = np.diff([v[1] for v in fall])
        checks.append({
            "date": ds,
            "below": max(0, r["tn"] - min(v[1] for v in vals)),
            "above": max(0, max(v[1] for v in vals) - r["tx"]),
            "rise_bad": int(np.min(rd) < -1e-7),
            "fall_bad": int(np.max(fd) > 1e-7),
        })

    # Calibration sensitivity curve of the single regional coefficient.
    sens = []
    for kg in [i / 20 for i in range(21)]:
        fn = lambda r, kk=kg: pred(
            r, pf, best["q"], best["kt0"], best["pmax"], kk
        )
        a = metrics(cal, fn)
        h = metrics([r for r in cal if r["formal_dtr"] >= 15], fn)
        sens.append({
            "krt": kg,
            "cal_all_rmse": a["rmse"],
            "cal_high_rmse": h["rmse"],
            "cal_all_bias": a["bias"],
            "cal_high_bias": h["bias"],
        })

    write("cv_grid.csv", cv)
    write("validation_metrics.csv", res)
    write("validation_by_year.csv", byyear)
    write("physical_checks.csv", checks)
    write("krt_sensitivity_calibration.csv", sens)

    pars = {
        "model": "M18_bounded_regional_shape",
        "formula": "q_new=(1-S)*q_temp+S*q_temp**P_MAX; S=K_RT*E/(1+E)",
        "q": best["q"],
        "kt0": best["kt0"],
        "pmax": best["pmax"],
        "K_RT": krt,
        "K_RT_bounds": [0.0, 1.0],
        "calibration_official_all_rmse": official_cal_rmse,
        "cv_selected": best,
    }
    (OUT / "parameters.json").write_text(json.dumps(pars, indent=2))

    mm = {(r["model"], r["group"]): r for r in res}
    oa = mm[("OFFICIAL", "MaySep")]
    oh = mm[("OFFICIAL", "DTR_GE15")]
    na = mm[("M18", "MaySep")]
    nh = mm[("M18", "DTR_GE15")]
    bad = sum(
        c["below"] > 1e-6 or c["above"] > 1e-6 or c["rise_bad"] or c["fall_bad"]
        for c in checks
    )
    # Idea-feasibility gate: beat locked physical M15 benchmark and preserve physics.
    gate = na["rmse"] < 2.7962 and nh["rmse"] < 4.6344 and bad == 0
    interior = krt < 0.995
    annual_pairs = {}
    for r in byyear:
        annual_pairs.setdefault(r["year"], {})[r["model"]] = r["rmse"]
    annual_wins = sum(
        1 for _, x in annual_pairs.items()
        if "OFFICIAL" in x and "M18" in x and x["M18"] < x["OFFICIAL"]
    )
    annual_total = sum(
        1 for x in annual_pairs.values() if "OFFICIAL" in x and "M18" in x
    )

    text = f"""# M18 bounded regional DTR-radiation HTEMP shape model

M18 keeps M17's region-relative DTR x radiative-deficit exposure, but replaces
unbounded `exp(k*E)` with a bounded convex shape blend. The continuously fitted
regional coefficient is `K_RT in [0,1]`; `K_RT=0` closes to official HTEMP.

Selected using **2000-2016 leave-one-year-out CV only**:
- q = {best['q']}
- Kt0 = {best['kt0']}
- structural P_MAX = {best['pmax']}
- final regional K_RT = {krt:.8f}
- CV all/high-DTR RMSE = {best['cv_all_rmse']:.4f} / {best['cv_high_rmse']:.4f} C
- CV folds at K_RT boundary >=0.995 = {best['boundary_fold_count']}

Independent legacy validation (2017+; kept only for continuity benchmarking):

|Metric|Official|M18|Improvement|
|---|---:|---:|---:|
|May-Sep RMSE|{oa['rmse']:.6f}|{na['rmse']:.6f}|{100*(oa['rmse']-na['rmse'])/oa['rmse']:.2f}%|
|DTR>=15 RMSE|{oh['rmse']:.6f}|{nh['rmse']:.6f}|{100*(oh['rmse']-nh['rmse'])/oh['rmse']:.2f}%|

- high-DTR full-curve physical violations = {bad}/{len(checks)}
- high-DTR annual RMSE wins vs official = {annual_wins}/{annual_total}
- idea-feasibility gate vs locked physical M15 = **{'PASS' if gate else 'FAIL'}**
- fitted K_RT interior (<0.995) = **{'PASS' if interior else 'BOUNDARY'}**

Interpretation boundary: 2017+ is a historical/legacy validation set already used
during model development and cannot serve as fresh final publication validation.
The purpose of M18 is to test a bounded transferable parameterization before
source-level DSSAT/CERES-Maize propagation and fresh Urumqi/Xinjiang validation.
"""
    (OUT / "README.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
