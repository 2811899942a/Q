#!/usr/bin/env python3
"""Parse M0/M19/M20 CERES-Maize bridge experiments for natural/stress weather."""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path

MODELS = ("M0", "M19", "M20")
MODES = ("NATURAL", "STRESS_DTR4")
SCENARIOS = tuple(f"ANQH{yy}{i:02d}" for yy in ("21", "22") for i in range(1, 6))
DATES = {1: "Apr21", 2: "Apr26", 3: "May06", 4: "May16", 5: "May26"}
TARGETS = ("ADAT", "MDAT", "CWAM", "HWAM", "HIAM", "LAIX", "TMAXA", "TMINA", "SRADA")
COMPARE = ("ADAT", "MDAT", "CWAM", "HWAM", "HIAM", "LAIX")


def fnum(value):
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def parse_summary(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    header = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("@"):
            tokens = line.split()
            if tokens and tokens[0] == "@":
                tokens = tokens[1:]
            header = [token.lstrip("@").upper() for token in tokens]
            continue
        if line.startswith(("*", "!")) or header is None or "HWAM" not in header:
            continue
        parts = line.split()
        if len(parts) < len(header):
            continue
        extra = len(parts) - len(header)
        if extra:
            idx = next((i for i, name in enumerate(header) if name.startswith("TNAM")), None)
            if idx is None:
                continue
            parts = parts[:idx] + [" ".join(parts[idx:idx + extra + 1])] + parts[idx + extra + 1:]
        if len(parts) == len(header):
            row = dict(zip(header, parts))
            if row.get("HWAM") not in (None, ""):
                return row
    raise ValueError(f"Could not parse HWAM row from {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-root", type=Path, default=Path("/tmp/results"))
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    detail = []
    summary = []
    for mode in MODES:
        mode_rows = []
        for scenario in SCENARIOS:
            got = {
                model: parse_summary(args.results_root / mode / model / f"{scenario}_Summary.OUT")
                for model in MODELS
            }
            row = {
                "mode": mode,
                "scenario": scenario,
                "year": 2000 + int(scenario[4:6]),
                "sowing": DATES[int(scenario[6:8])],
            }
            for model in MODELS:
                for key in TARGETS:
                    row[f"{model}_{key}"] = got[model].get(key, "")
            for model in ("M19", "M20"):
                for key in COMPARE:
                    a = fnum(got[model].get(key))
                    b = fnum(got["M0"].get(key))
                    row[f"{model}_minus_M0_{key}"] = "" if a is None or b is None else a - b
            for key in COMPARE:
                a = fnum(got["M20"].get(key))
                b = fnum(got["M19"].get(key))
                row[f"M20_minus_M19_{key}"] = "" if a is None or b is None else a - b
            detail.append(row)
            mode_rows.append(row)

        for model in ("M19", "M20"):
            dy = [fnum(r[f"{model}_minus_M0_HWAM"]) for r in mode_rows]
            da = [fnum(r[f"{model}_minus_M0_ADAT"]) for r in mode_rows]
            dm = [fnum(r[f"{model}_minus_M0_MDAT"]) for r in mode_rows]
            dy = [x for x in dy if x is not None]
            da = [x for x in da if x is not None]
            dm = [x for x in dm if x is not None]
            changed = sum(
                any(abs(fnum(r.get(f"{model}_minus_M0_{key}")) or 0.0) > 1e-9 for key in COMPARE)
                for r in mode_rows
            )
            summary.append(
                {
                    "mode": mode,
                    "model": model,
                    "scenarios": len(mode_rows),
                    "changed_scenarios": changed,
                    "mean_delta_yield_kg_ha": statistics.mean(dy),
                    "max_abs_delta_yield_kg_ha": max(abs(x) for x in dy),
                    "min_delta_yield_kg_ha": min(dy),
                    "max_delta_yield_kg_ha": max(dy),
                    "mean_delta_anthesis_day": statistics.mean(da),
                    "mean_delta_maturity_day": statistics.mean(dm),
                }
            )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "bridge_detail.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(detail[0].keys()))
        w.writeheader(); w.writerows(detail)
    with (args.output_dir / "bridge_summary.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        w.writeheader(); w.writerows(summary)

    lines = [
        "# M20 source bridge: M19 hourly correction -> CERES-Maize DTT",
        "",
        "M0 = official DSSAT 4.8.5; M19 = weather-side hourly correction only; M20 = M19 plus neutral-delta DTT bridge.",
        "",
        "| Weather | Model | Changed scenarios | Mean yield delta vs M0 (kg/ha) | Max abs yield delta | Mean anthesis delta (d) | Mean maturity delta (d) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for s in summary:
        lines.append(
            f"| {s['mode']} | {s['model']} | {s['changed_scenarios']}/{s['scenarios']} | "
            f"{s['mean_delta_yield_kg_ha']:.2f} | {s['max_abs_delta_yield_kg_ha']:.2f} | "
            f"{s['mean_delta_anthesis_day']:.2f} | {s['mean_delta_maturity_day']:.2f} |"
        )
    lines += [
        "",
        "Interpretation gate: M19=0 change confirms the original interface gap. M20>0 changed scenarios establishes source-level propagation through DTT. STRESS_DTR4 is a controlled causal stress test and is not an observed-climate validation.",
    ]
    (args.output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
