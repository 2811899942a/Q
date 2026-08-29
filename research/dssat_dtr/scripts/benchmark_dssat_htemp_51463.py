#!/usr/bin/env python3
"""Benchmark the original DSSAT HTEMP (Parton-Logan) temperature reconstruction
against real sub-daily observations at Urumqi station 51463099999.

Design:
- Daily forcing: NOAA GHCN-Daily CHM00051463 TMAX/TMIN (QC-clean pairs).
- Sub-daily observations: NOAA ISD / Global Hourly 51463099999.
- Time axis: observations are converted from China Standard Time (UTC+8)
  to local apparent solar time before comparison because DSSAT DAYLEN/HTEMP
  defines solar noon at 12:00 and does not use the civil time-zone longitude.
- DSSAT equations are transcribed directly from Weather/SOLAR.for::DAYLEN and
  Weather/HMET.for::HTEMP with the same constants (PI=3.14159;
  A=2.0, B=2.2, C=1.0).
- No interpolation is applied to observations.
- ISD temperature quality codes marked suspect/erroneous (2,3,6,7) are excluded.

Outputs:
  htemp_pointwise_2000_2024.csv
  htemp_metrics_summary.csv
  htemp_metrics_by_dtr.csv
  htemp_metrics_by_solar_hour.csv
  htemp_daily_rmse_vs_dtr.csv
  README_HTEMP_BASELINE.md
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ISD_ID = "51463099999"
LAT = 43.7833
LON = 87.6167
TZ_HOURS = 8.0
STANDARD_MERIDIAN = 15.0 * TZ_HOURS  # 120 E for China Standard Time

PI = 3.14159
RAD = PI / 180.0
A = 2.0
B = 2.2
C = 1.0

BAD_ISD_QC = {"2", "3", "6", "7"}

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed_51463"
HOURLY = DATA / f"{ISD_ID}_hourly_observed_2000_2024.csv"
DAILY = DATA / f"{ISD_ID}_htemp_validation_daily_2000_2024.csv"

PRED_OUT = DATA / "htemp_pointwise_2000_2024.csv"
SUMMARY_OUT = DATA / "htemp_metrics_summary.csv"
DTR_OUT = DATA / "htemp_metrics_by_dtr.csv"
HOUR_OUT = DATA / "htemp_metrics_by_solar_hour.csv"
DAILY_RMSE_OUT = DATA / "htemp_daily_rmse_vs_dtr.csv"
README_OUT = DATA / "README_HTEMP_BASELINE.md"


def parse_dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def equation_of_time_minutes(doy: int) -> float:
    """Common equation-of-time approximation in minutes.

    This is only used to map civil timestamps onto local apparent solar time.
    It is not inserted into the DSSAT DAYLEN or HTEMP equations themselves.
    """
    b = math.radians((360.0 / 365.0) * (doy - 81))
    return 9.87 * math.sin(2.0 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def cst_to_apparent_solar(dt_cst: datetime) -> datetime:
    doy = dt_cst.timetuple().tm_yday
    eot = equation_of_time_minutes(doy)
    correction_min = 4.0 * (LON - STANDARD_MERIDIAN) + eot
    return dt_cst + timedelta(minutes=correction_min)


def dssat_daylen(doy: int, lat: float = LAT):
    dec = -23.45 * math.cos(2.0 * PI * (doy + 10.0) / 365.0)
    soc = math.tan(RAD * dec) * math.tan(RAD * lat)
    soc = min(max(soc, -1.0), 1.0)
    dayl = 12.0 + 24.0 * math.asin(soc) / PI
    dayl = min(max(dayl, 0.0), 24.0)
    snup = 12.0 - dayl / 2.0
    sndn = 12.0 + dayl / 2.0
    return dayl, dec, snup, sndn


def dssat_htemp(hs: float, tmax: float, tmin: float, dayl: float, snup: float, sndn: float) -> float:
    """Continuous evaluation of the exact DSSAT HTEMP equation at solar hour hs."""
    hs = hs % 24.0
    tmin_time = snup + C
    tmax_time = tmin_time + dayl / 2.0 + A
    t = 0.5 * PI * (sndn - tmin_time) / (tmax_time - tmin_time)
    tsndn = tmin + (tmax - tmin) * math.sin(t)
    tmini = (tmin - tsndn * math.exp(-B)) / (1.0 - math.exp(-B))
    hdecay = 24.0 + C - dayl

    if hs >= snup + C and hs <= sndn:
        t = 0.5 * PI * (hs - tmin_time) / (tmax_time - tmin_time)
        return tmin + (tmax - tmin) * math.sin(t)

    if hs < snup + C:
        t = 24.0 + hs - sndn
    else:
        t = hs - sndn
    arg = -B * t / hdecay
    return tmini + (tsndn - tmini) * math.exp(arg)


def dtr_bin(dtr: float) -> str:
    if dtr < 10.0:
        return "<10"
    if dtr < 15.0:
        return "10-<15"
    if dtr < 20.0:
        return "15-<20"
    return ">=20"


def season_label(month: int) -> str:
    return "May-Sep" if 5 <= month <= 9 else "Other"


def mean(xs):
    return statistics.mean(xs) if xs else float("nan")


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
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def spearman(x, y):
    if len(x) < 3:
        return float("nan")
    return pearson(rankdata(x), rankdata(y))


def metric_row(label, rows):
    obs = [r["obs_c"] for r in rows]
    pred = [r["pred_c"] for r in rows]
    err = [p - o for p, o in zip(pred, obs)]
    if not rows:
        return {
            "group": label, "n_points": 0, "n_days": 0,
            "rmse_c": "", "mae_c": "", "mbe_c": "", "r2": "", "pearson_r": "",
        }
    rmse = math.sqrt(mean([e * e for e in err]))
    mae = mean([abs(e) for e in err])
    mbe = mean(err)
    r = pearson(obs, pred)
    return {
        "group": label,
        "n_points": len(rows),
        "n_days": len({r["solar_date"] for r in rows}),
        "rmse_c": round(rmse, 4),
        "mae_c": round(mae, 4),
        "mbe_c": round(mbe, 4),
        "r2": round(r * r, 4) if not math.isnan(r) else "",
        "pearson_r": round(r, 4) if not math.isnan(r) else "",
    }


def write_csv(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    if not HOURLY.exists() or not DAILY.exists():
        raise FileNotFoundError("Required processed NOAA files are missing; run NOAA/GHCN processing first.")

    daily_map = {}
    with DAILY.open("r", newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r.get("formal_dtr_c", "") == "":
                continue
            if r.get("ghcn_pair_qc_clean") != "YES":
                continue
            daily_map[r["date_cst"]] = {
                "tmax": float(r["ghcn_tmax_c"]),
                "tmin": float(r["ghcn_tmin_c"]),
                "dtr": float(r["formal_dtr_c"]),
            }

    predictions = []
    qc_counts = defaultdict(int)
    unmatched_solar_date = 0

    with HOURLY.open("r", newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            q = (r.get("temp_quality_flag") or "").strip()
            qc_counts[q or "BLANK"] += 1
            if q in BAD_ISD_QC:
                continue

            dt_cst = parse_dt(r["datetime_cst"])
            dt_solar = cst_to_apparent_solar(dt_cst)
            solar_date = dt_solar.date().isoformat()
            daily = daily_map.get(solar_date)
            if daily is None:
                unmatched_solar_date += 1
                continue

            doy = dt_solar.timetuple().tm_yday
            dayl, dec, snup, sndn = dssat_daylen(doy)
            hs = dt_solar.hour + dt_solar.minute / 60.0 + dt_solar.second / 3600.0
            pred = dssat_htemp(hs, daily["tmax"], daily["tmin"], dayl, snup, sndn)
            obs = float(r["temp_c"])
            err = pred - obs
            predictions.append({
                "datetime_cst": r["datetime_cst"],
                "datetime_solar": dt_solar.strftime("%Y-%m-%d %H:%M:%S"),
                "solar_date": solar_date,
                "solar_hour": round(hs, 4),
                "solar_hour_bin": int(math.floor(hs)) % 24,
                "month": dt_solar.month,
                "season": season_label(dt_solar.month),
                "obs_c": obs,
                "pred_c": round(pred, 4),
                "error_c": round(err, 4),
                "abs_error_c": round(abs(err), 4),
                "tmax_ghcn_c": daily["tmax"],
                "tmin_ghcn_c": daily["tmin"],
                "formal_dtr_c": daily["dtr"],
                "dtr_bin": dtr_bin(daily["dtr"]),
                "dayl_h": round(dayl, 4),
                "snup_solar_h": round(snup, 4),
                "sndn_solar_h": round(sndn, 4),
                "dssat_A": A,
                "dssat_B": B,
                "dssat_C": C,
                "isd_temp_qc": q,
            })

    # Internal numeric representation for metrics.
    num_rows = []
    for r in predictions:
        nr = dict(r)
        for k in ["obs_c", "pred_c", "formal_dtr_c"]:
            nr[k] = float(nr[k])
        num_rows.append(nr)

    # Summary groups.
    summary_groups = [
        ("All matched", num_rows),
        ("May-Sep", [r for r in num_rows if r["season"] == "May-Sep"]),
        ("All DTR>=15", [r for r in num_rows if r["formal_dtr_c"] >= 15.0]),
        ("May-Sep DTR>=15", [r for r in num_rows if r["season"] == "May-Sep" and r["formal_dtr_c"] >= 15.0]),
        ("All DTR>=20", [r for r in num_rows if r["formal_dtr_c"] >= 20.0]),
        ("May-Sep DTR>=20", [r for r in num_rows if r["season"] == "May-Sep" and r["formal_dtr_c"] >= 20.0]),
    ]
    summary_rows = [metric_row(label, rows) for label, rows in summary_groups]

    # DTR bins, all and May-Sep.
    dtr_rows = []
    for season in ["All", "May-Sep"]:
        base = num_rows if season == "All" else [r for r in num_rows if r["season"] == "May-Sep"]
        for b in ["<10", "10-<15", "15-<20", ">=20"]:
            dtr_rows.append(metric_row(f"{season}|DTR {b}", [r for r in base if r["dtr_bin"] == b]))

    # Solar-hour bins.
    hour_rows = []
    for h in range(24):
        rows = [r for r in num_rows if int(r["solar_hour_bin"]) == h]
        hour_rows.append(metric_row(f"solar_hour_{h:02d}", rows))

    # Per-day RMSE and relationship to DTR.
    by_day = defaultdict(list)
    for r in num_rows:
        by_day[r["solar_date"]].append(r)
    daily_rmse = []
    for date in sorted(by_day):
        rs = by_day[date]
        errs = [float(r["pred_c"]) - float(r["obs_c"]) for r in rs]
        dtr = float(rs[0]["formal_dtr_c"])
        month = int(rs[0]["month"])
        daily_rmse.append({
            "solar_date": date,
            "month": month,
            "season": season_label(month),
            "n_points": len(rs),
            "formal_dtr_c": round(dtr, 1),
            "daily_rmse_c": round(math.sqrt(mean([e * e for e in errs])), 4),
            "daily_mae_c": round(mean([abs(e) for e in errs]), 4),
            "daily_mbe_c": round(mean(errs), 4),
        })

    def corr_block(rows):
        xs = [float(r["formal_dtr_c"]) for r in rows]
        ys = [float(r["daily_rmse_c"]) for r in rows]
        return pearson(xs, ys), spearman(xs, ys)

    r_all, rho_all = corr_block(daily_rmse)
    daily_maize = [r for r in daily_rmse if r["season"] == "May-Sep"]
    r_maize, rho_maize = corr_block(daily_maize)

    # Trend slope: OLS daily RMSE ~ intercept + slope*DTR.
    def ols_slope(rows):
        xs = [float(r["formal_dtr_c"]) for r in rows]
        ys = [float(r["daily_rmse_c"]) for r in rows]
        if len(xs) < 2:
            return float("nan")
        mx, my = mean(xs), mean(ys)
        den = sum((x - mx) ** 2 for x in xs)
        if den <= 0:
            return float("nan")
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den

    slope_all = ols_slope(daily_rmse)
    slope_maize = ols_slope(daily_maize)

    # Count usable QC values and excluded values.
    valid_qc_points = len(predictions)
    bad_qc_total = sum(v for k, v in qc_counts.items() if k in BAD_ISD_QC)

    write_csv(PRED_OUT, predictions)
    write_csv(SUMMARY_OUT, summary_rows)
    write_csv(DTR_OUT, dtr_rows)
    write_csv(HOUR_OUT, hour_rows)
    write_csv(DAILY_RMSE_OUT, daily_rmse)

    overall = summary_rows[0]
    maize_metric = summary_rows[1]
    high = summary_rows[2]
    high_maize = summary_rows[3]

    # Scientific gate: require both a positive daily trend and visibly higher RMSE at high DTR.
    rmse_all = float(overall["rmse_c"])
    rmse_high = float(high["rmse_c"]) if high["rmse_c"] != "" else float("nan")
    rmse_maize = float(maize_metric["rmse_c"])
    rmse_high_maize = float(high_maize["rmse_c"]) if high_maize["rmse_c"] != "" else float("nan")

    signal_all = (not math.isnan(rmse_high) and rmse_high > rmse_all and slope_all > 0 and r_all > 0)
    signal_maize = (not math.isnan(rmse_high_maize) and rmse_high_maize > rmse_maize and slope_maize > 0 and r_maize > 0)

    verdict = (
        "DTR_ERROR_SIGNAL_SUPPORTED" if signal_all and signal_maize else
        "PARTIAL_DTR_ERROR_SIGNAL" if signal_all or signal_maize else
        "NO_MONOTONIC_DTR_ERROR_SIGNAL"
    )

    qc_text = ", ".join(f"{k}:{v}" for k, v in sorted(qc_counts.items()))
    readme = f"""# Original DSSAT HTEMP baseline — Urumqi 51463

## Data and alignment

- Daily Tmax/Tmin: NOAA GHCN-Daily `CHM00051463`.
- Sub-daily observations: NOAA ISD `51463099999`.
- Observation timestamps converted from CST (UTC+8) to **local apparent solar time** using longitude {LON} E before comparison.
- DSSAT `DAYLEN` and `HTEMP` equations are reproduced from the official open-source code.
- Parton-Logan parameters kept at official DSSAT defaults: **A={A}, B={B}, C={C}**.
- ISD suspect/erroneous temperature QC codes excluded: {sorted(BAD_ISD_QC)}.
- Matched prediction-observation points: **{valid_qc_points:,}**.
- ISD records excluded by suspect/erroneous QC: **{bad_qc_total:,}**.
- Source QC flag counts before filtering: `{qc_text}`.

## Core metrics

| Scope | N points | N days | RMSE C | MAE C | MBE C | R2 |
|---|---:|---:|---:|---:|---:|---:|
| All | {overall['n_points']} | {overall['n_days']} | {overall['rmse_c']} | {overall['mae_c']} | {overall['mbe_c']} | {overall['r2']} |
| May-Sep | {maize_metric['n_points']} | {maize_metric['n_days']} | {maize_metric['rmse_c']} | {maize_metric['mae_c']} | {maize_metric['mbe_c']} | {maize_metric['r2']} |
| DTR >=15 C | {high['n_points']} | {high['n_days']} | {high['rmse_c']} | {high['mae_c']} | {high['mbe_c']} | {high['r2']} |
| May-Sep DTR >=15 C | {high_maize['n_points']} | {high_maize['n_days']} | {high_maize['rmse_c']} | {high_maize['mae_c']} | {high_maize['mbe_c']} | {high_maize['r2']} |

## Does HTEMP error increase with DTR?

Daily RMSE versus formal GHCN DTR:

- All seasons Pearson r = **{r_all:.4f}**; Spearman rho = **{rho_all:.4f}**; OLS slope = **{slope_all:.4f} C RMSE per 1 C DTR**.
- May-Sep Pearson r = **{r_maize:.4f}**; Spearman rho = **{rho_maize:.4f}**; OLS slope = **{slope_maize:.4f} C RMSE per 1 C DTR**.
- Automated first-pass verdict: **{verdict}**.

The verdict is only a diagnostic gate. A source-code modification should be pursued after inspecting DTR-bin errors, time-of-day errors, and independent-year calibration/validation, rather than from the correlation alone.

## DSSAT source reproduction

`Weather/SOLAR.for::DAYLEN`

- `DEC = -23.45*COS(2*PI*(DOY+10)/365)`
- `DAYL = 12 + 24*ASIN(TAN(DEC)*TAN(XLAT))/PI`
- `SNUP = 12 - DAYL/2`
- `SNDN = 12 + DAYL/2`

`Weather/HMET.for::HTEMP`

- Parton & Logan (1981)
- fixed `A=2.0, B=2.2, C=1.0`
- daytime sine curve + nighttime exponential decay

## Interpretation rule

The strongest support for the proposed DSSAT-DTR study would be a reproducible rise in RMSE/MAE with formal DTR, concentrated in identifiable solar-time periods (for example afternoon peak timing or nighttime cooling), and repeated within May-Sep. If that pattern is absent, the source-code innovation hypothesis must be narrowed before modifying DSSAT.
"""
    README_OUT.write_text(readme, encoding="utf-8")
    print(readme)


if __name__ == "__main__":
    main()
