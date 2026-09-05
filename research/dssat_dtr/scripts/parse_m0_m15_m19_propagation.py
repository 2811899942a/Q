#!/usr/bin/env python3
"""Parse M0/M15/M19 DSSAT Summary.OUT files from the Anningqu propagation audit.

The parser follows the DSSAT whitespace-table format and explicitly collapses
multiword TNAM values, which is required for cases such as "RAINFED LOW NITROGEN".
It is intentionally standalone so the same parser can be reused on Windows.
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path

MODELS = ("M0", "M15", "M19")
SCENARIOS = tuple(f"ANQH{yy}{i:02d}" for yy in ("21", "22") for i in range(1, 6))
SOWING_LABEL = {1: "Apr21", 2: "Apr26", 3: "May06", 4: "May16", 5: "May26"}
TARGETS = (
    "PDAT", "EDAT", "ADAT", "MDAT", "HDAT", "CWAM", "HWAM", "HIAM", "LAIX",
    "NDCH", "TMAXA", "TMINA", "SRADA", "DAYLA", "CRST",
)
DELTA_TARGETS = ("ADAT", "MDAT", "CWAM", "HWAM", "HIAM", "LAIX")


def _to_float(value: str | float | int | None) -> float | None:
    try:
        x = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def parse_summary(path: Path) -> dict[str, str]:
    """Return the first valid Summary.OUT crop row after the HWAM header.

    DSSAT Summary.OUT contains a whitespace-delimited header beginning with '@'.
    TNAM may contain spaces, so a naive split produces more data tokens than header
    tokens. We collapse all excess tokens into TNAM, matching the validated parser
    used in the earlier DSSAT v4.8.5 KT sensitivity screen.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    header: list[str] | None = None

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if line.startswith("@"):
            tokens = line.split()
            if tokens and tokens[0] == "@":
                tokens = tokens[1:]
            header = [tok.lstrip("@").upper() for tok in tokens]
            continue

        if line.startswith(("*", "!")) or header is None or "HWAM" not in header:
            continue

        parts = line.split()
        if len(parts) < len(header):
            continue

        extra = len(parts) - len(header)
        if extra:
            try:
                tnam_idx = next(i for i, name in enumerate(header) if name.startswith("TNAM"))
            except StopIteration as exc:
                raise ValueError(
                    f"{path}: data row has {extra} extra tokens but TNAM column is absent"
                ) from exc
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


def build_rows(results_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        parsed = {
            model: parse_summary(results_root / model / f"{scenario}_Summary.OUT")
            for model in MODELS
        }
        year = 2000 + int(scenario[4:6])
        sow_index = int(scenario[6:8])
        row: dict[str, object] = {
            "scenario": scenario,
            "year": year,
            "sowing": SOWING_LABEL[sow_index],
        }
        for model in MODELS:
            for target in TARGETS:
                row[f"{model}_{target}"] = parsed[model].get(target, "")

        for model in ("M15", "M19"):
            for target in DELTA_TARGETS:
                a = _to_float(parsed[model].get(target))
                b = _to_float(parsed["M0"].get(target))
                row[f"{model}_minus_M0_{target}"] = "" if a is None or b is None else a - b
        rows.append(row)
    return rows


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for model in ("M15", "M19"):
        dy = [_to_float(row.get(f"{model}_minus_M0_HWAM")) for row in rows]
        da = [_to_float(row.get(f"{model}_minus_M0_ADAT")) for row in rows]
        dm = [_to_float(row.get(f"{model}_minus_M0_MDAT")) for row in rows]
        dy = [x for x in dy if x is not None]
        da = [x for x in da if x is not None]
        dm = [x for x in dm if x is not None]
        if not dy or not da or not dm:
            raise ValueError(f"{model}: one or more required delta vectors are empty")

        changed = 0
        for row in rows:
            if any(
                abs(_to_float(row.get(f"{model}_minus_M0_{target}")) or 0.0) > 1e-9
                for target in DELTA_TARGETS
            ):
                changed += 1

        output.append(
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
    return output


def write_outputs(rows: list[dict[str, object]], summary: list[dict[str, object]], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)

    with (out / "m0_m15_m19_crop_outputs.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with (out / "propagation_summary.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    lines = [
        "# Source-level DSSAT 4.8.5 M19 crop propagation",
        "",
        "All three arms use identical DSSAT data, Anningqu weather/soil, fixed proxy cultivar IB0035, sowing dates, WATER=N and NITRO=N. Only the HTEMP source differs.",
        "",
        "| Model | Changed scenarios | Mean delta yield vs M0 (kg/ha) | Max abs delta yield (kg/ha) | Mean delta anthesis (d) | Mean delta maturity (d) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in summary:
        lines.append(
            f"| {item['model']} | {item['changed_scenarios']}/{item['scenarios']} | "
            f"{float(item['mean_delta_yield_kg_ha']):.2f} | "
            f"{float(item['max_abs_delta_yield_kg_ha']):.2f} | "
            f"{float(item['mean_delta_anthesis_day']):.2f} | "
            f"{float(item['mean_delta_maturity_day']):.2f} |"
        )
    lines += [
        "",
        "Interpretation: reproducible M19-M0 crop-output differences establish source-level propagation from the regional HTEMP correction into CERES-Maize. These proxy-cultivar runs are a mechanism test and are not observed-yield validation.",
    ]
    (out / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=Path("/tmp/results"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("research/dssat_dtr/data/anningqu/m19_source_propagation"),
    )
    args = parser.parse_args()
    rows = build_rows(args.results_root)
    summary = summarize(rows)
    write_outputs(rows, summary, args.output_dir)


if __name__ == "__main__":
    main()
