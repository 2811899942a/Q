#!/usr/bin/env python3
"""Diagnose whether Urumqi DSSAT HTEMP residuals exhibit DTR-driven diurnal asymmetry.

This script does not modify DSSAT and does not fit a new temperature model.
It tests the local mechanism hypothesis from the already-generated original-DSSAT
pointwise benchmark:

  higher DTR -> stronger morning underestimation and stronger afternoon overestimation.

It also checks whether errors concentrate on locally extreme hot/cold days using
May-Sep empirical quantiles, without yet imposing crop-specific physiological thresholds.

Input:
  data/processed_51463/htemp_pointwise_2000_2024.csv

Outputs:
  dtr_asymmetry_daily.csv
  dtr_asymmetry_by_bin.csv
  dtr_asymmetry_relationships.csv
  peak_checkpoint_timing_by_dtr.csv
  extreme_temperature_diagnostics.csv
  README_DTR_ASYMMETRY.md
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed_51463"
INFILE = DATA / "htemp_pointwise_2000_2024.csv"

DAILY_OUT = DATA / "dtr_asymmetry_daily.csv"
BIN_OUT = DATA / "dtr_asymmetry_by_bin.csv"
REL_OUT = DATA / "dtr_asymmetry_relationships.csv"
PEAK_OUT = DATA / "peak_checkpoint_timing_by_dtr.csv"
EXTREME_OUT = DATA / "extreme_temperature_diagnostics.csv"
README_OUT = DATA / "README_DTR_ASYMMETRY.md"

# Local apparent solar-time windows selected to match the actual ISD checkpoint pattern.
MORNING_START, MORNING_END = 5.0, 10.0    # [05,10)
AFTERNOON_START, AFTERNOON_END = 14.0, 19.0  # [14,19)
NIGHT1_START, NIGHT1_END = 20.0, 24.0
NIGHT2_START, NIGHT2_END = 0.0, 5.0


def f(x):
    return float(x)


def mean(xs):
    return statistics.mean(xs) if xs else float("nan")


def median(xs):
    return statistics.median(xs) if xs else float("nan")


def percentile(xs, p):
    vals = sorted(xs)
    if not vals:
        return float("nan")
    if len(vals) == 1:
        return vals[0]
    k = (len(vals) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return vals[lo]
    return vals[lo] * (hi - k) + vals[hi] * (k - lo)


def pearson(x, y):
    if len(x) < 3 or len(x) != len(y):
        return float("nan")
    mx, my = mean(x), mean(y)
    sx = sum((v - mx) ** 2 for v in x)
    sy = sum((v - my) ** 2 for v in y)
    if sx <= 0 or sy <= 0:
        return float("nan")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sx * sy)


def rankdata(values):
    indexed = sorted(enumerate(values), key=lambda z: z[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg
        i = j
    return ranks


def spearman(x, y):
    if len(x) < 3:
        return float("nan")
    return pearson(rankdata(x), rankdata(y))


def slope(x, y):
    if len(x) < 2:
        return float("nan")
    mx, my = mean(x), mean(y)
    den = sum((a - mx) ** 2 for a in x)
    if den <= 0:
        return float("nan")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / den


def rmse(errors):
    return math.sqrt(mean([e * e for e in errors])) if errors else float("nan")


def dtr_bin(dtr):
    if dtr < 8:
        return "<8"
    if dtr < 10:
        return "8-<10"
    if dtr < 12:
        return "10-<12"
    if dtr < 15:
        return "12-<15"
    if dtr < 18:
        return "15-<18"
    if dtr < 20:
        return "18-<20"
    return ">=20"


def signed_circular_hour_diff(pred_h, obs_h):
    """Signed pred-observed hour difference folded to [-12, 12)."""
    return ((pred_h - obs_h + 12.0) % 24.0) - 12.0


def write_csv(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    if not INFILE.exists():
        raise FileNotFoundError(INFILE)

    points = []
    with INFILE.open("r", newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            r2 = dict(r)
            for key in ["solar_hour", "obs_c", "pred_c", "error_c", "formal_dtr_c", "tmax_ghcn_c", "tmin_ghcn_c"]:
                r2[key] = f(r2[key])
            r2["month"] = int(r2["month"])
            points.append(r2)

    by_day = defaultdict(list)
    for r in points:
        by_day[r["solar_date"]].append(r)

    daily = []
    for date in sorted(by_day):
        rs = sorted(by_day[date], key=lambda r: r["solar_hour"])
        month = int(rs[0]["month"])
        dtr = f(rs[0]["formal_dtr_c"])
        tmax = f(rs[0]["tmax_ghcn_c"])
        tmin = f(rs[0]["tmin_ghcn_c"])

        morning = [r for r in rs if MORNING_START <= r["solar_hour"] < MORNING_END]
        afternoon = [r for r in rs if AFTERNOON_START <= r["solar_hour"] < AFTERNOON_END]
        night = [r for r in rs if (NIGHT1_START <= r["solar_hour"] < NIGHT1_END) or (NIGHT2_START <= r["solar_hour"] < NIGHT2_END)]

        obs_peak = max(rs, key=lambda r: r["obs_c"])
        pred_peak = max(rs, key=lambda r: r["pred_c"])
        peak_err = signed_circular_hour_diff(pred_peak["solar_hour"], obs_peak["solar_hour"])

        errs = [r["error_c"] for r in rs]
        row = {
            "solar_date": date,
            "month": month,
            "season": "May-Sep" if 5 <= month <= 9 else "Other",
            "n_points": len(rs),
            "dtr_c": round(dtr, 1),
            "dtr_bin": dtr_bin(dtr),
            "tmax_c": round(tmax, 1),
            "tmin_c": round(tmin, 1),
            "daily_bias_c": round(mean(errs), 4),
            "daily_rmse_c": round(rmse(errs), 4),
            "morning_n": len(morning),
            "morning_bias_c": "" if not morning else round(mean([r["error_c"] for r in morning]), 4),
            "morning_rmse_c": "" if not morning else round(rmse([r["error_c"] for r in morning]), 4),
            "afternoon_n": len(afternoon),
            "afternoon_bias_c": "" if not afternoon else round(mean([r["error_c"] for r in afternoon]), 4),
            "afternoon_rmse_c": "" if not afternoon else round(rmse([r["error_c"] for r in afternoon]), 4),
            "night_n": len(night),
            "night_bias_c": "" if not night else round(mean([r["error_c"] for r in night]), 4),
            "obs_peak_checkpoint_solar_h": round(obs_peak["solar_hour"], 4),
            "pred_peak_checkpoint_solar_h": round(pred_peak["solar_hour"], 4),
            "peak_checkpoint_error_h": round(peak_err, 4),
        }
        daily.append(row)

    write_csv(DAILY_OUT, daily)

    # Primary mechanism test uses May-Sep because it is the DSSAT maize-relevant window.
    maize = [r for r in daily if r["season"] == "May-Sep"]

    def valid(rows, key):
        return [r for r in rows if r.get(key, "") != ""]

    relationships = []
    for scope_name, rows in [("All", daily), ("May-Sep", maize)]:
        for key, label in [
            ("morning_bias_c", "morning_bias"),
            ("afternoon_bias_c", "afternoon_bias"),
            ("night_bias_c", "night_bias"),
            ("daily_rmse_c", "daily_rmse"),
            ("peak_checkpoint_error_h", "sample_peak_timing_error"),
        ]:
            vr = valid(rows, key)
            x = [f(r["dtr_c"]) for r in vr]
            y = [f(r[key]) for r in vr]
            relationships.append({
                "scope": scope_name,
                "response": label,
                "n_days": len(vr),
                "pearson_r": round(pearson(x, y), 4),
                "spearman_rho": round(spearman(x, y), 4),
                "ols_slope_per_1c_dtr": round(slope(x, y), 4),
                "mean_response": round(mean(y), 4),
            })
    write_csv(REL_OUT, relationships)

    # DTR-bin diagnostics.
    bins = ["<8", "8-<10", "10-<12", "12-<15", "15-<18", "18-<20", ">=20"]
    bin_rows = []
    for scope_name, rows in [("All", daily), ("May-Sep", maize)]:
        for b in bins:
            br = [r for r in rows if r["dtr_bin"] == b]
            mb = [f(r["morning_bias_c"]) for r in br if r["morning_bias_c"] != ""]
            ab = [f(r["afternoon_bias_c"]) for r in br if r["afternoon_bias_c"] != ""]
            nb = [f(r["night_bias_c"]) for r in br if r["night_bias_c"] != ""]
            pk = [f(r["peak_checkpoint_error_h"]) for r in br]
            dr = [f(r["daily_rmse_c"]) for r in br]
            bin_rows.append({
                "scope": scope_name,
                "dtr_bin": b,
                "n_days": len(br),
                "mean_dtr_c": "" if not br else round(mean([f(r["dtr_c"]) for r in br]), 3),
                "morning_bias_c": "" if not mb else round(mean(mb), 4),
                "afternoon_bias_c": "" if not ab else round(mean(ab), 4),
                "afternoon_minus_morning_bias_c": "" if not mb or not ab else round(mean(ab) - mean(mb), 4),
                "night_bias_c": "" if not nb else round(mean(nb), 4),
                "daily_rmse_c": "" if not dr else round(mean(dr), 4),
                "median_peak_checkpoint_error_h": "" if not pk else round(median(pk), 4),
                "mean_abs_peak_checkpoint_error_h": "" if not pk else round(mean([abs(v) for v in pk]), 4),
            })
    write_csv(BIN_OUT, bin_rows)

    # Peak checkpoint timing by DTR on days with a reasonably complete sparse pattern.
    peak_rows = []
    for b in bins:
        br = [r for r in maize if r["dtr_bin"] == b and int(r["n_points"]) >= 6]
        vals = [f(r["peak_checkpoint_error_h"]) for r in br]
        peak_rows.append({
            "scope": "May-Sep_n>=6_checkpoints",
            "dtr_bin": b,
            "n_days": len(br),
            "median_signed_peak_error_h": "" if not vals else round(median(vals), 4),
            "mean_signed_peak_error_h": "" if not vals else round(mean(vals), 4),
            "mean_abs_peak_error_h": "" if not vals else round(mean([abs(v) for v in vals]), 4),
            "pct_model_peak_later": "" if not vals else round(100.0 * sum(v > 0 for v in vals) / len(vals), 2),
            "pct_model_peak_earlier": "" if not vals else round(100.0 * sum(v < 0 for v in vals) / len(vals), 2),
        })
    write_csv(PEAK_OUT, peak_rows)

    # Empirical extreme-temperature diagnostics in May-Sep.
    tmax90 = percentile([f(r["tmax_c"]) for r in maize], 0.90)
    tmax95 = percentile([f(r["tmax_c"]) for r in maize], 0.95)
    tmin10 = percentile([f(r["tmin_c"]) for r in maize], 0.10)
    tmin05 = percentile([f(r["tmin_c"]) for r in maize], 0.05)

    classes = [
        ("non_extreme_10_90", lambda r: f(r["tmax_c"]) < tmax90 and f(r["tmin_c"]) > tmin10),
        ("hot_top10_tmax", lambda r: f(r["tmax_c"]) >= tmax90),
        ("hot_top5_tmax", lambda r: f(r["tmax_c"]) >= tmax95),
        ("cold_bottom10_tmin", lambda r: f(r["tmin_c"]) <= tmin10),
        ("cold_bottom5_tmin", lambda r: f(r["tmin_c"]) <= tmin05),
        ("high_dtr_ge15", lambda r: f(r["dtr_c"]) >= 15.0),
    ]
    ext_rows = []
    for label, cond in classes:
        rs = [r for r in maize if cond(r)]
        mb = [f(r["morning_bias_c"]) for r in rs if r["morning_bias_c"] != ""]
        ab = [f(r["afternoon_bias_c"]) for r in rs if r["afternoon_bias_c"] != ""]
        ext_rows.append({
            "class": label,
            "n_days": len(rs),
            "mean_tmax_c": "" if not rs else round(mean([f(r["tmax_c"]) for r in rs]), 3),
            "mean_tmin_c": "" if not rs else round(mean([f(r["tmin_c"]) for r in rs]), 3),
            "mean_dtr_c": "" if not rs else round(mean([f(r["dtr_c"]) for r in rs]), 3),
            "mean_daily_rmse_c": "" if not rs else round(mean([f(r["daily_rmse_c"]) for r in rs]), 4),
            "morning_bias_c": "" if not mb else round(mean(mb), 4),
            "afternoon_bias_c": "" if not ab else round(mean(ab), 4),
            "afternoon_minus_morning_bias_c": "" if not mb or not ab else round(mean(ab) - mean(mb), 4),
            "mean_abs_peak_checkpoint_error_h": "" if not rs else round(mean([abs(f(r["peak_checkpoint_error_h"])) for r in rs]), 4),
        })
    write_csv(EXTREME_OUT, ext_rows)

    # Extract headline May-Sep relationships.
    relmap = {(r["scope"], r["response"]): r for r in relationships}
    mr = relmap[("May-Sep", "morning_bias")]
    ar = relmap[("May-Sep", "afternoon_bias")]
    pr = relmap[("May-Sep", "sample_peak_timing_error")]

    maize_bins = [r for r in bin_rows if r["scope"] == "May-Sep"]
    low_bin = next((r for r in maize_bins if r["dtr_bin"] == "<8"), None)
    high_bin = next((r for r in maize_bins if r["dtr_bin"] == "15-<18"), None)
    very_high = next((r for r in maize_bins if r["dtr_bin"] == ">=20"), None)

    # Mechanism gate: morning becomes more negative with DTR and afternoon more positive.
    mechanism_supported = f(mr["ols_slope_per_1c_dtr"]) < 0 and f(ar["ols_slope_per_1c_dtr"]) > 0
    verdict = "ASYMMETRIC_DTR_SIGNAL_SUPPORTED" if mechanism_supported else "ASYMMETRIC_DTR_SIGNAL_NOT_CLEANLY_SUPPORTED"

    def btxt(r):
        if not r:
            return "NA"
        return f"morning={r['morning_bias_c']} C; afternoon={r['afternoon_bias_c']} C; gap={r['afternoon_minus_morning_bias_c']} C; daily_RMSE={r['daily_rmse_c']} C; n={r['n_days']}"

    readme = f"""# Urumqi 51463 — DTR-driven asymmetric HTEMP residual diagnosis

## Purpose

This is a **mechanism-discovery** analysis. No new DSSAT formula has been fitted. The test asks whether Urumqi observations support the local hypothesis that increasing DTR changes the *temporal allocation* of temperature error: stronger morning underestimation together with stronger afternoon overestimation.

## Analysis windows

- Morning: local apparent solar time **05:00-09:59**.
- Afternoon: **14:00-18:59**.
- Night: **20:00-04:59**.
- Main crop-relevant window: **May-Sep**.

## Key DTR relationships in May-Sep

### Morning bias vs DTR
- n days = **{mr['n_days']}**
- Pearson r = **{mr['pearson_r']}**
- Spearman rho = **{mr['spearman_rho']}**
- OLS slope = **{mr['ols_slope_per_1c_dtr']} C bias per 1 C DTR**

A negative slope means the model becomes increasingly cold-biased in the morning as DTR increases.

### Afternoon bias vs DTR
- n days = **{ar['n_days']}**
- Pearson r = **{ar['pearson_r']}**
- Spearman rho = **{ar['spearman_rho']}**
- OLS slope = **{ar['ols_slope_per_1c_dtr']} C bias per 1 C DTR**

A positive slope means the model becomes increasingly warm-biased in the afternoon as DTR increases.

### Sampled peak-checkpoint timing error vs DTR
- Pearson r = **{pr['pearson_r']}**
- Spearman rho = **{pr['spearman_rho']}**
- OLS slope = **{pr['ols_slope_per_1c_dtr']} h per 1 C DTR**

This timing diagnostic is deliberately called a **sampled peak-checkpoint error**, because ISD provides about eight real observations per day rather than a continuous observed Tmax timestamp.

## DTR-bin contrast in May-Sep

- DTR <8 C: {btxt(low_bin)}
- DTR 15-<18 C: {btxt(high_bin)}
- DTR >=20 C: {btxt(very_high)}

Automated mechanism verdict: **{verdict}**.

## Extreme-temperature diagnostic thresholds (May-Sep empirical distribution)

These are diagnostic quantiles, not yet maize physiological thresholds:

- TMAX P90 = **{tmax90:.2f} C**
- TMAX P95 = **{tmax95:.2f} C**
- TMIN P10 = **{tmin10:.2f} C**
- TMIN P05 = **{tmin05:.2f} C**

The file `extreme_temperature_diagnostics.csv` compares hot-tail, cold-tail, non-extreme, and high-DTR days using the same morning/afternoon residual metrics. This tells us whether a future source-level correction should be activated broadly by DTR or only under extreme high/low temperature regimes.

## Scientific use rule

Do not yet claim a new mechanism from the automated verdict alone. A locally defensible DSSAT modification requires that the residual asymmetry is (1) monotonic or at least threshold-like across DTR bins, (2) present in the maize season, (3) not explained solely by a handful of >=20 C DTR days, and (4) stronger than or complementary to the hot/cold extreme-temperature signal.
"""
    README_OUT.write_text(readme, encoding="utf-8")
    print(readme)


if __name__ == "__main__":
    main()
