#!/usr/bin/env python3
"""Focused result-first K_RT screen for M15 + stage-specific hourly heat dose.

Builds one patched CERES-Maize binary, then scans K_RT at runtime. This avoids
rebuilding already-demoted hourly-DTT arms. UFGA8201 is a mechanism benchmark;
K_RT values from this screen are not Urumqi calibration values.
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_dssat_m15_stage_heat_v2 as v2

KRT_GRID = [0.0, 0.005, 0.010, 0.020, 0.040, 0.080, 0.120, 0.160, 0.240, 0.320]
LOCKED_M15_HWAM = [2291.0, 2331.0, 8181.0, 11854.0, 7697.0, 10292.0]
LOCKED_M15_ADAT = [1982133] * 6
LOCKED_M15_MDAT = [1982185] * 6


def closes_to_locked_m15(summary: Path) -> bool:
    rows = v2.load_summary(summary)
    return (
        [r["HWAM"] for r in rows] == LOCKED_M15_HWAM
        and [r["ADAT"] for r in rows] == LOCKED_M15_ADAT
        and [r["MDAT"] for r in rows] == LOCKED_M15_MDAT
    )


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: run_dssat_m15_krt_focused.py <source> <data> <out>")
    base, data, out = [Path(x).resolve() for x in sys.argv[1:]]
    out.mkdir(parents=True, exist_ok=True)
    cases = out / "cases"
    cases.mkdir(exist_ok=True)

    src = out / "src_m15_hdh"
    v2.clone_tree(base, src)
    v2.patch(src, "apply_m15_frozen_patch.py", "--variant", "13p5")
    v2.patch(src, "apply_stage_hdh_krt_patch.py")
    exe = v2.build_dssat(src, out / "build")
    runtime = out / "runtime"
    v2.make_runtime(src, data, runtime)
    v2.install_exe(exe, runtime)

    summaries = {}
    rows = []
    for k in KRT_GRID:
        label = f"M15_HDH33_KRT={k:.3f}"
        s = v2.run_case(runtime, cases, label, k)
        summaries[k] = s
        rows.append(v2.metric_row(label, s))

    closure = closes_to_locked_m15(summaries[0.0])
    base_rmse = rows[0]["HWAM_RMSE"]
    for row, k in zip(rows, KRT_GRID):
        row["KRT"] = k
        row["delta_vs_M15_pct"] = 100.0 * (base_rmse - row["HWAM_RMSE"]) / base_rmse

    csv_path = out / "m15_krt_focused_screen.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    nonzero = rows[1:]
    best = min(nonzero, key=lambda r: r["HWAM_RMSE"])
    response = any(abs(r["HWAM_RMSE"] - base_rmse) > 1.0e-9 for r in nonzero)
    edge = math.isclose(best["KRT"], KRT_GRID[-1])

    print("\n=== FOCUSED M15 + HDH33 KRT SCREEN ===")
    print("LOCKED_M15_KRT0_CLOSURE=" + ("PASS" if closure else "FAIL"))
    print("NONZERO_KRT_RESPONSE=" + ("YES" if response else "NO"))
    for r in rows:
        print(
            f'{r["case"]}: RMSE={r["HWAM_RMSE"]:.3f}, MAE={r["HWAM_MAE"]:.3f}, '
            f'd={r["HWAM_d"]:.6f}, vs_M15={r["delta_vs_M15_pct"]:+.3f}%, '
            f'ADAT={r["ADAT_MAE_days"]:.2f}d, MDAT={r["MDAT_MAE_days"]:.2f}d'
        )
    print(f'BEST_KRT={best["KRT"]:.3f}')
    print(f'BEST_RMSE={best["HWAM_RMSE"]:.6f}')
    print(f'BEST_MAE={best["HWAM_MAE"]:.6f}')
    print(f'BEST_D={best["HWAM_d"]:.9f}')
    print(f'BEST_DELTA_VS_M15_PCT={best["delta_vs_M15_pct"]:+.6f}')
    print("BEST_AT_UPPER_EDGE=" + ("YES" if edge else "NO"))
    print("SUMMARY_CSV=" + str(csv_path))

    if not closure:
        raise SystemExit("KRT=0 did not reproduce locked M15 benchmark exactly")


if __name__ == "__main__":
    main()
