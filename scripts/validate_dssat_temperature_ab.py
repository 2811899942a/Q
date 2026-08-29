#!/usr/bin/env python3
"""Compare baseline and modified DSSAT crop outputs against UFGA8201 observations.

Inputs may be DSSAT Summary.OUT files or CSV files containing treatment/TRNO,
HWAM, ADAT and MDAT columns. The script writes treatment-level and aggregate
comparison CSV files.

Example:
    python validate_dssat_temperature_ab.py \
        --baseline baseline/Summary.OUT \
        --modified modified/Summary.OUT \
        --observed results/DSSAT_UFGA8201_observed_targets.csv \
        --outdir results/ab_validation
"""

from __future__ import annotations

import argparse
import csv
import math
from datetime import datetime
from pathlib import Path
from statistics import mean


ALIASES = {
    "treatment": ["TRNO", "TRTNO", "TRT", "TREATMENT", "RUN"],
    "HWAM": ["HWAM"],
    "ADAT": ["ADAT"],
    "MDAT": ["MDAT"],
}


def norm(s: str) -> str:
    return s.strip().lstrip("@").upper()


def find_col(fieldnames, candidates):
    lookup = {norm(x): x for x in fieldnames}
    for c in candidates:
        if norm(c) in lookup:
            return lookup[norm(c)]
    return None


def to_float(value):
    if value is None:
        return math.nan
    text = str(value).strip()
    if not text or text in {"-99", "-99.0", "NA", "NAN"}:
        return math.nan
    try:
        return float(text)
    except ValueError:
        return math.nan


def to_int(value):
    x = to_float(value)
    if math.isnan(x):
        return None
    return int(round(x))


def parse_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"No rows in {path}")
    return normalize_rows(rows, list(rows[0].keys()), path)


def parse_summary_out(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    tables = []
    current_header = None
    current_rows = []

    def flush():
        nonlocal current_header, current_rows
        if current_header and current_rows:
            tables.append((current_header, current_rows))
        current_header = None
        current_rows = []

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("@"):
            flush()
            current_header = [norm(x) for x in line.split()]
            continue
        if line.startswith("*") or line.startswith("!"):
            continue
        if current_header is None:
            continue
        parts = line.split()
        if len(parts) == len(current_header):
            current_rows.append(dict(zip(current_header, parts)))
        elif len(parts) > len(current_header):
            # Some DSSAT tables can contain a free-text field. For Summary.OUT,
            # key numeric columns are normally aligned at the right. Keep the
            # rightmost header-length fields as a conservative fallback.
            current_rows.append(dict(zip(current_header, parts[-len(current_header):])))
    flush()

    candidates = []
    for header, rows in tables:
        if "HWAM" in header:
            candidates.append((header, rows))
    if not candidates:
        raise ValueError(f"Could not find a Summary.OUT table containing HWAM in {path}")

    # Prefer a table that also contains phenology columns and a treatment identifier.
    def score(item):
        header, rows = item
        s = 10 * len(rows)
        s += 5 if "ADAT" in header else 0
        s += 5 if "MDAT" in header else 0
        s += 5 if any(x in header for x in ["TRNO", "TRTNO", "TRT", "TREATMENT"]) else 0
        return s

    header, rows = max(candidates, key=score)
    return normalize_rows(rows, header, path)


def normalize_rows(rows, fieldnames, path):
    tr_col = find_col(fieldnames, ALIASES["treatment"])
    hwam_col = find_col(fieldnames, ALIASES["HWAM"])
    adat_col = find_col(fieldnames, ALIASES["ADAT"])
    mdat_col = find_col(fieldnames, ALIASES["MDAT"])

    if hwam_col is None:
        raise ValueError(f"HWAM column not found in {path}; fields={fieldnames}")
    if tr_col is None:
        # If exactly six rows are present, preserve DSSAT treatment order 1..6.
        if len(rows) != 6:
            raise ValueError(f"Treatment column not found in {path}; fields={fieldnames}")

    out = []
    for i, row in enumerate(rows, start=1):
        trt = to_int(row.get(tr_col)) if tr_col else i
        if trt is None:
            continue
        out.append(
            {
                "treatment": trt,
                "HWAM": to_float(row.get(hwam_col)),
                "ADAT": to_int(row.get(adat_col)) if adat_col else None,
                "MDAT": to_int(row.get(mdat_col)) if mdat_col else None,
            }
        )

    # Summary.OUT can contain multiple runs/sections. Keep the last record per treatment.
    dedup = {}
    for row in out:
        dedup[row["treatment"]] = row
    return [dedup[k] for k in sorted(dedup)]


def load_sim(path: Path):
    if path.suffix.lower() == ".csv":
        return parse_csv(path)
    return parse_summary_out(path)


def load_observed(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        trt = int(r["treatment"])
        out[trt] = {
            "name": r.get("treatment_name", ""),
            "HWAM": float(r["HWAM_obs_kg_ha"]),
            "ADAT": int(r["ADAT_obs_YYYYDDD"]),
            "MDAT": int(r["MDAT_obs_YYYYDDD"]),
        }
    return out


def date_error_days(sim_yyyyddd, obs_yyyyddd):
    if sim_yyyyddd is None or obs_yyyyddd is None:
        return math.nan
    try:
        sim = datetime.strptime(str(sim_yyyyddd), "%Y%j")
        obs = datetime.strptime(str(obs_yyyyddd), "%Y%j")
        return (sim - obs).days
    except ValueError:
        return math.nan


def willmott_d(obs, sim):
    pairs = [(o, s) for o, s in zip(obs, sim) if not (math.isnan(o) or math.isnan(s))]
    if not pairs:
        return math.nan
    o = [x[0] for x in pairs]
    s = [x[1] for x in pairs]
    om = mean(o)
    num = sum((si - oi) ** 2 for oi, si in pairs)
    den = sum((abs(si - om) + abs(oi - om)) ** 2 for oi, si in pairs)
    return math.nan if den == 0 else 1.0 - num / den


def metrics(obs, sim):
    pairs = [(o, s) for o, s in zip(obs, sim) if not (math.isnan(o) or math.isnan(s))]
    if not pairs:
        return {"n": 0, "bias": math.nan, "mae": math.nan, "rmse": math.nan, "d": math.nan}
    errors = [s - o for o, s in pairs]
    return {
        "n": len(pairs),
        "bias": mean(errors),
        "mae": mean(abs(e) for e in errors),
        "rmse": math.sqrt(mean(e * e for e in errors)),
        "d": willmott_d([x[0] for x in pairs], [x[1] for x in pairs]),
    }


def fmt(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--modified", required=True, type=Path)
    ap.add_argument("--observed", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    args = ap.parse_args()

    baseline = {r["treatment"]: r for r in load_sim(args.baseline)}
    modified = {r["treatment"]: r for r in load_sim(args.modified)}
    observed = load_observed(args.observed)

    treatments = sorted(observed)
    missing_b = [t for t in treatments if t not in baseline]
    missing_m = [t for t in treatments if t not in modified]
    if missing_b or missing_m:
        raise ValueError(f"Missing treatments: baseline={missing_b}, modified={missing_m}")

    args.outdir.mkdir(parents=True, exist_ok=True)
    detail_path = args.outdir / "DSSAT_temperature_AB_treatment_comparison.csv"
    metric_path = args.outdir / "DSSAT_temperature_AB_metrics.csv"

    detail = []
    for t in treatments:
        o, b, m = observed[t], baseline[t], modified[t]
        b_err = b["HWAM"] - o["HWAM"]
        m_err = m["HWAM"] - o["HWAM"]
        detail.append(
            {
                "treatment": t,
                "treatment_name": o["name"],
                "HWAM_obs": o["HWAM"],
                "HWAM_baseline": b["HWAM"],
                "HWAM_modified": m["HWAM"],
                "baseline_error": b_err,
                "modified_error": m_err,
                "baseline_abs_error": abs(b_err),
                "modified_abs_error": abs(m_err),
                "abs_error_change_modified_minus_baseline": abs(m_err) - abs(b_err),
                "ADAT_obs": o["ADAT"],
                "ADAT_baseline": b["ADAT"],
                "ADAT_modified": m["ADAT"],
                "ADAT_baseline_error_days": date_error_days(b["ADAT"], o["ADAT"]),
                "ADAT_modified_error_days": date_error_days(m["ADAT"], o["ADAT"]),
                "MDAT_obs": o["MDAT"],
                "MDAT_baseline": b["MDAT"],
                "MDAT_modified": m["MDAT"],
                "MDAT_baseline_error_days": date_error_days(b["MDAT"], o["MDAT"]),
                "MDAT_modified_error_days": date_error_days(m["MDAT"], o["MDAT"]),
            }
        )

    with detail_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(detail[0].keys()))
        w.writeheader()
        w.writerows(detail)

    obs_y = [observed[t]["HWAM"] for t in treatments]
    b_y = [baseline[t]["HWAM"] for t in treatments]
    m_y = [modified[t]["HWAM"] for t in treatments]
    bm = metrics(obs_y, b_y)
    mm = metrics(obs_y, m_y)
    rmse_reduction_pct = math.nan
    if bm["rmse"] and not math.isnan(bm["rmse"]):
        rmse_reduction_pct = (bm["rmse"] - mm["rmse"]) / bm["rmse"] * 100.0

    metric_rows = []
    for label, vals in [("baseline", bm), ("modified", mm)]:
        metric_rows.append({"model": label, **vals, "rmse_reduction_vs_baseline_pct": 0.0 if label == "baseline" else rmse_reduction_pct})

    with metric_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(metric_rows[0].keys()))
        w.writeheader()
        w.writerows(metric_rows)

    print(f"Wrote: {detail_path}")
    print(f"Wrote: {metric_path}")
    print(f"Baseline RMSE: {bm['rmse']:.3f} kg/ha")
    print(f"Modified RMSE: {mm['rmse']:.3f} kg/ha")
    print(f"RMSE reduction: {rmse_reduction_pct:.2f}%")


if __name__ == "__main__":
    main()
