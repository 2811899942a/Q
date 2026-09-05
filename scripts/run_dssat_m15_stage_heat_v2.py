#!/usr/bin/env python3
"""Run the DSSAT M15 + hourly-DTT + reproductive HDH/KRT V2 mechanism screen.

UFGA8201 is used only as a reproducible source-level mechanism benchmark.
It is not Xinjiang regional validation.
"""
from __future__ import annotations

import csv
import math
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PATCH = REPO / "research" / "dssat_dtr" / "dssat485"
KRT_GRID = [0.0, 0.003, 0.006, 0.009, 0.012]
OBS = {
    1: {"HWAM": 2929.0, "ADAT": 1982132, "MDAT": 1982185},
    2: {"HWAM": 3130.0, "ADAT": 1982132, "MDAT": 1982185},
    3: {"HWAM": 6850.0, "ADAT": 1982132, "MDAT": 1982185},
    4: {"HWAM": 11881.0, "ADAT": 1982132, "MDAT": 1982185},
    5: {"HWAM": 6375.0, "ADAT": 1982132, "MDAT": 1982185},
    6: {"HWAM": 9344.0, "ADAT": 1982132, "MDAT": 1982185},
}


def run(cmd, cwd=None, env=None):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def clone_tree(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=True)


def find_exe(build: Path) -> Path:
    candidates = [p for p in build.rglob("dscsm048") if p.is_file()]
    if not candidates:
        raise FileNotFoundError(f"dscsm048 not found in {build}")
    candidates.sort(key=lambda p: (0 if "bin" in p.parts else 1, len(p.parts)))
    return candidates[0]


def build_dssat(src: Path, build: Path) -> Path:
    if build.exists():
        shutil.rmtree(build)
    run([
        "cmake", "-S", str(src), "-B", str(build),
        "-DCMAKE_BUILD_TYPE=RELEASE",
        "-DCMAKE_Fortran_COMPILER=gfortran",
        "-DCMAKE_INSTALL_PREFIX=/DSSAT48",
    ])
    run(["cmake", "--build", str(build), "-j", "2"])
    return find_exe(build)


def patch(src: Path, script: str, *args: str):
    run([sys.executable, str(PATCH / script), str(src), *args])


def make_runtime(src: Path, data: Path, runtime: Path):
    if runtime.exists():
        shutil.rmtree(runtime)
    shutil.copytree(data, runtime)
    shutil.copytree(src / "Data", runtime, dirs_exist_ok=True)
    if not (runtime / "DSSATPRO.L48").exists():
        raise FileNotFoundError(
            "DSSATPRO.L48 missing after CMake configure; build official source before runtime copy"
        )
    if not (runtime / "Maize" / "UFGA8201.MZX").exists():
        raise FileNotFoundError("UFGA8201.MZX missing")


def install_exe(exe: Path, runtime: Path):
    target = runtime / "dscsm048"
    shutil.copy2(exe, target)
    os.chmod(target, 0o755)


def clean_outputs(maize: Path):
    for name in ["Summary.OUT", "PlantGro.OUT", "Overview.OUT", "Evaluate.OUT", "WARNING.OUT"]:
        p = maize / name
        if p.exists():
            p.unlink()


def case_slug(label: str) -> str:
    return label.replace("+", "p").replace("-", "m").replace("=", "_").replace(".", "p").replace("/", "_")


def run_case(runtime: Path, cases: Path, label: str, krt: float | None = None) -> Path:
    maize = runtime / "Maize"
    clean_outputs(maize)
    env = os.environ.copy()
    if krt is None:
        env.pop("DSSAT_KRT", None)
    else:
        env["DSSAT_KRT"] = f"{krt:.6f}"
    run(["../dscsm048", "A", "UFGA8201.MZX"], cwd=maize, env=env)
    summary = maize / "Summary.OUT"
    if not summary.exists():
        raise RuntimeError(f"{label}: Summary.OUT missing")
    target = cases / case_slug(label)
    target.mkdir(parents=True, exist_ok=True)
    for name in ["Summary.OUT", "PlantGro.OUT", "Overview.OUT", "Evaluate.OUT", "WARNING.OUT"]:
        p = maize / name
        if p.exists():
            shutil.copy2(p, target / name)
    return target / "Summary.OUT"


def load_summary(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    header = None
    rows = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("@"):
            h = line.split()
            if h and h[0] == "@":
                h = h[1:]
            header = [x.lstrip("@").upper() for x in h]
            continue
        if line.startswith("*") or line.startswith("!") or header is None or "HWAM" not in header:
            continue
        parts = line.split()
        if len(parts) < len(header):
            continue
        extra = len(parts) - len(header)
        if extra:
            idx = next((i for i, x in enumerate(header) if x.startswith("TNAM")), None)
            if idx is None:
                continue
            parts = parts[:idx] + [" ".join(parts[idx:idx + extra + 1])] + parts[idx + extra + 1:]
        if len(parts) != len(header):
            continue
        row = dict(zip(header, parts))
        try:
            rows.append({
                "treatment": int(float(row["TRNO"])),
                "HWAM": float(row["HWAM"]),
                "ADAT": int(float(row["ADAT"])),
                "MDAT": int(float(row["MDAT"])),
            })
        except (KeyError, ValueError):
            pass
    dedup = {r["treatment"]: r for r in rows}
    parsed = [dedup[k] for k in sorted(dedup)]
    if len(parsed) != 6:
        raise ValueError(f"Expected 6 UFGA treatments in {path}; got {sorted(dedup)}")
    return parsed


def dssat_date(n: int) -> date:
    y, doy = divmod(int(n), 1000)
    return date(y, 1, 1) + timedelta(days=doy - 1)


def date_err(a: int, b: int) -> float:
    if a < 0 or b < 0:
        return math.nan
    return float((dssat_date(a) - dssat_date(b)).days)


def willmott(obs, sim):
    mean_o = sum(obs) / len(obs)
    num = sum((s - o) ** 2 for o, s in zip(obs, sim))
    den = sum((abs(s - mean_o) + abs(o - mean_o)) ** 2 for o, s in zip(obs, sim))
    return 1.0 - num / den if den else math.nan


def metric_row(label: str, summary: Path):
    sim = {r["treatment"]: r for r in load_summary(summary)}
    trts = sorted(OBS)
    o = [OBS[t]["HWAM"] for t in trts]
    s = [sim[t]["HWAM"] for t in trts]
    errors = [ss - oo for oo, ss in zip(o, s)]
    bias = sum(errors) / len(errors)
    mae = sum(abs(x) for x in errors) / len(errors)
    rmse = math.sqrt(sum(x * x for x in errors) / len(errors))
    adat = [abs(date_err(sim[t]["ADAT"], OBS[t]["ADAT"])) for t in trts]
    mdat = [abs(date_err(sim[t]["MDAT"], OBS[t]["MDAT"])) for t in trts]
    row = {
        "case": label,
        "HWAM_bias": bias,
        "HWAM_MAE": mae,
        "HWAM_RMSE": rmse,
        "HWAM_d": willmott(o, s),
        "ADAT_MAE_days": sum(adat) / len(adat),
        "MDAT_MAE_days": sum(mdat) / len(mdat),
        "HWAM_mean": sum(s) / len(s),
    }
    row.update({f"HWAM_T{t}": sim[t]["HWAM"] for t in trts})
    row.update({f"ADAT_T{t}": sim[t]["ADAT"] for t in trts})
    row.update({f"MDAT_T{t}": sim[t]["MDAT"] for t in trts})
    return row


def exact_equal(a: Path, b: Path) -> bool:
    aa = {r["treatment"]: r for r in load_summary(a)}
    bb = {r["treatment"]: r for r in load_summary(b)}
    return all(aa[t][f] == bb[t][f] for t in aa for f in ("HWAM", "ADAT", "MDAT"))


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: run_dssat_m15_stage_heat_v2.py <source> <data> <out>")
    base, data, out = [Path(x).resolve() for x in sys.argv[1:]]
    out.mkdir(parents=True, exist_ok=True)
    cases = out / "cases"
    cases.mkdir(exist_ok=True)

    # M0 official baseline. CMake configure generates Data/DSSATPRO.L48,
    # therefore the official source must be built before copying runtime Data.
    exe0 = build_dssat(base, out / "build_m0")
    runtime = out / "runtime"
    make_runtime(base, data, runtime)
    install_exe(exe0, runtime)
    m0 = run_case(runtime, cases, "M0_official")

    # Frozen M15-13.5 baseline.
    src_m15 = out / "src_m15"
    clone_tree(base, src_m15)
    patch(src_m15, "apply_m15_frozen_patch.py", "--variant", "13p5")
    exem15 = build_dssat(src_m15, out / "build_m15")
    install_exe(exem15, runtime)
    m15 = run_case(runtime, cases, "M15_13p5")

    # M15 + reproductive HDH/KRT, one binary and runtime coefficient grid.
    src_hdh = out / "src_hdh"
    clone_tree(src_m15, src_hdh)
    patch(src_hdh, "apply_stage_hdh_krt_patch.py")
    exehdh = build_dssat(src_hdh, out / "build_hdh")
    install_exe(exehdh, runtime)
    hdh = {}
    for k in KRT_GRID:
        label = f"M15_HDH_KRT={k:.3f}"
        hdh[k] = run_case(runtime, cases, label, k)

    # M15 + existing extreme-hourly-DTT path.
    src_dtt = out / "src_dtt"
    clone_tree(src_m15, src_dtt)
    patch(src_dtt, "apply_extreme_dtt_tgro_patch.py")
    exedtt = build_dssat(src_dtt, out / "build_dtt")
    install_exe(exedtt, runtime)
    dtt = run_case(runtime, cases, "M15_hourlyDTT")

    # Combined: hourly-DTT + reproductive HDH/KRT.
    src_combo = out / "src_combo"
    clone_tree(src_m15, src_combo)
    patch(src_combo, "apply_extreme_dtt_tgro_patch.py")
    patch(src_combo, "apply_stage_hdh_krt_patch.py")
    execombo = build_dssat(src_combo, out / "build_combo")
    install_exe(execombo, runtime)
    combo = {}
    for k in KRT_GRID:
        label = f"M15_hourlyDTT_HDH_KRT={k:.3f}"
        combo[k] = run_case(runtime, cases, label, k)

    closure_hdh = exact_equal(m15, hdh[0.0])
    closure_combo = exact_equal(dtt, combo[0.0])

    ordered = [("M0_official", m0), ("M15_13p5", m15)]
    ordered += [(f"M15_HDH_KRT={k:.3f}", hdh[k]) for k in KRT_GRID]
    ordered += [("M15_hourlyDTT", dtt)]
    ordered += [(f"M15_hourlyDTT_HDH_KRT={k:.3f}", combo[k]) for k in KRT_GRID]
    rows = [metric_row(label, path) for label, path in ordered]

    base_rmse = next(r["HWAM_RMSE"] for r in rows if r["case"] == "M15_13p5")
    dtt_rmse = next(r["HWAM_RMSE"] for r in rows if r["case"] == "M15_hourlyDTT")
    for r in rows:
        r["delta_vs_M15_pct"] = 100.0 * (base_rmse - r["HWAM_RMSE"]) / base_rmse

    csv_path = out / "m15_stage_heat_v2_screen.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    best_hdh = min((r for r in rows if r["case"].startswith("M15_HDH_KRT=") and not r["case"].endswith("0.000")), key=lambda x: x["HWAM_RMSE"])
    best_combo = min((r for r in rows if r["case"].startswith("M15_hourlyDTT_HDH_KRT=") and not r["case"].endswith("0.000")), key=lambda x: x["HWAM_RMSE"])

    print("\n=== DSSAT M15 STAGE HEAT V2 ===")
    print("M15_TO_HDH_KRT0_CLOSURE=" + ("PASS" if closure_hdh else "FAIL"))
    print("DTT_TO_COMBINED_KRT0_CLOSURE=" + ("PASS" if closure_combo else "FAIL"))
    for r in rows:
        imp = 100.0 * (base_rmse - r["HWAM_RMSE"]) / base_rmse
        print(f'{r["case"]}: RMSE={r["HWAM_RMSE"]:.3f}, d={r["HWAM_d"]:.5f}, vs_M15={imp:+.3f}%, ADAT={r["ADAT_MAE_days"]:.2f}d, MDAT={r["MDAT_MAE_days"]:.2f}d')
    print(f'BEST_HDH={best_hdh["case"]}, RMSE={best_hdh["HWAM_RMSE"]:.3f}')
    print(f'BEST_COMBINED={best_combo["case"]}, RMSE={best_combo["HWAM_RMSE"]:.3f}')
    print(f'M15_RMSE={base_rmse:.3f}; DTT_RMSE={dtt_rmse:.3f}')
    print("SUMMARY_CSV=" + str(csv_path))

    if not closure_hdh:
        raise SystemExit("KRT=0 failed exact closure to M15")
    if not closure_combo:
        raise SystemExit("Combined KRT=0 failed exact closure to M15+hourlyDTT")


if __name__ == "__main__":
    main()
