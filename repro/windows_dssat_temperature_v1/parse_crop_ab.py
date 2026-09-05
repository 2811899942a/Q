#!/usr/bin/env python3
"""Parse Windows M0/M15/M19 DSSAT Summary.OUT copies into compact A/B evidence.

This parser mirrors the GitHub CI parser and explicitly handles DSSAT multiword
TNAM fields so the Windows reproduction route uses the same evidence logic.
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path

MODELS = ("M0", "M15", "M19")
SCENARIOS = tuple(f"ANQH{yy}{i:02d}" for yy in ("21", "22") for i in range(1, 6))
DATES = {1: "Apr21", 2: "Apr26", 3: "May06", 4: "May16", 5: "May26"}
TARGETS = (
    "PDAT", "EDAT", "ADAT", "MDAT", "HDAT", "CWAM", "HWAM", "HIAM", "LAIX",
    "NDCH", "TMAXA", "TMINA", "SRADA", "DAYLA", "CRST",
)
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
            tnam_idx = next((i for i, name in enumerate(header) if name.startswith("TNAM")), None)
            if tnam_idx is None:
                continue
            parts = (
                parts[:tnam_idx]
                + [" ".join(parts[tnam_idx : tnam_idx + extra + 1])]
                + parts[tnam_idx + extra + 1 :]
            )
        if len(parts) != len(header):
            continue
        row = dict(zip(header, parts))
        if row.get("HWAM") not in (None, ""):
            return row
    preview = "\n".join(lines[:80])
    raise ValueError(f"Could not parse a valid HWAM row from {path}. Preview:\n{preview}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    rows = []
    for scenario in SCENARIOS:
        got = {
            model: parse_summary(args.results_root / model / f"{scenario}_Summary.OUT")
            for model in MODELS
        }
        row = {
            "scenario": scenario,
            "year": 2000 + int(scenario[4:6]),
            "sowing": DATES[int(scenario[6:8])],
        }
        for model in MODELS:
            for key in TARGETS:
                row[f"{model}_{key}"] = got[model].get(key, "")
        for model in ("M15", "M19"):
            for key in COMPARE:
                a = fnum(got[model].get(key))
                b = fnum(got["M0"].get(key))
                row[f"{model}_minus_M0_{key}"] = "" if a is None or b is None else a - b
        rows.append(row)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "m0_m15_m19_crop_outputs.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summaries = []
    for model in ("M15", "M19"):
        dy = [fnum(row[f"{model}_minus_M0_HWAM"]) for row in rows]
        da = [fnum(row[f"{model}_minus_M0_ADAT"]) for row in rows]
        dm = [fnum(row[f"{model}_minus_M0_MDAT"]) for row in rows]
        dy = [x for x in dy if x is not None]
        da = [x for x in da if x is not None]
        dm = [x for x in dm if x is not None]
        if not dy or not da or not dm:
            raise ValueError(f"{model}: required propagation delta vector is empty")
        changed = sum(
            1
            for row in rows
            if any(
                abs(fnum(row.get(f"{model}_minus_M0_{key}")) or 0.0) > 1e-9
                for key in COMPARE
            )
        )
        summaries.append(
            {
                "model": model,
                "scenarios": len(rows),
                "changed_scenarios": changed,
                "mean_delta_yield_kg_ha": statistics.mean(dy),
                "max_abs_delta_yield_kg_ha": max(abs(x) for x in dy),
                "min_delta_yield_kg_ha": min(dy),
                "max_delta_yield_kg_ha": max(dy),
                "mean_delta_anthesis_day": statistics.mean(da),
                "mean_delta_maturity_day": statistics.mean(dm),
            }
        )

    with (args.output_dir / "propagation_summary.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)

    lines = [
        "# Windows source-level DSSAT M0/M15/M19 propagation",
        "",
        "All arms share identical weather, soil, crop, sowing-date, water and nitrogen settings. Only HTEMP source differs.",
        "",
        "| Model | Changed scenarios | Mean delta yield vs M0 (kg/ha) | Max abs delta yield (kg/ha) | Mean delta anthesis (d) | Mean delta maturity (d) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in summaries:
        lines.append(
            f"| {item['model']} | {item['changed_scenarios']}/{item['scenarios']} | "
            f"{item['mean_delta_yield_kg_ha']:.2f} | {item['max_abs_delta_yield_kg_ha']:.2f} | "
            f"{item['mean_delta_anthesis_day']:.2f} | {item['mean_delta_maturity_day']:.2f} |"
        )
    lines += [
        "",
        "PASS criterion for mechanism reproduction: M19 must compile/run cleanly and produce at least one reproducible crop-output difference from M0 under identical inputs. Exact Linux/Windows floating-point equality is not required.",
    ]
    (args.output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
