#!/usr/bin/env python3
"""Download and quality-summarize NOAA Global Hourly data for Urumqi station 51463099999.

Outputs are intentionally conservative: sparse SYNOP/METAR observations remain sparse.
No temporal interpolation is performed and no day is treated as a complete hourly curve
unless the source actually contains enough distinct local-hour observations.
"""

from __future__ import annotations

import csv
import io
import os
import statistics
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

STATION = "51463099999"
START_YEAR = int(os.environ.get("START_YEAR", "2000"))
END_YEAR = int(os.environ.get("END_YEAR", "2024"))
UTC_OFFSET_HOURS = 8  # China Standard Time used for project day grouping
BASE_URL = "https://www.ncei.noaa.gov/data/global-hourly/access/{year}/" + STATION + ".csv"

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed_51463"
OUT.mkdir(parents=True, exist_ok=True)

REPORT_PRIORITY = {
    "FM-15": 0,  # METAR
    "FM-16": 1,  # SPECI
    "FM-12": 2,  # SYNOP
    "FM-13": 3,
    "FM-14": 4,
    "SAO": 5,
}


def fetch(url: str, retries: int = 3) -> bytes:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DSSAT-DTR-research/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise last  # type: ignore[misc]


def parse_tmp(value: str):
    """Return (temperature_C, raw_quality_flag). NOAA TMP is signed tenths C + quality flag."""
    if not value:
        return None, ""
    parts = value.split(",")
    raw = parts[0].strip()
    q = parts[1].strip() if len(parts) > 1 else ""
    if raw in {"+9999", "9999", "-9999", ""}:
        return None, q
    try:
        return int(raw) / 10.0, q
    except ValueError:
        return None, q


def parse_dt(value: str):
    value = (value or "").strip()
    if not value:
        return None
    value = value.replace("Z", "")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                pass
    return None


def grade(n: int) -> str:
    if n >= 20:
        return "A"
    if n >= 8:
        return "B"
    if n >= 4:
        return "C"
    return "D"


def report_rank(report_type: str) -> int:
    return REPORT_PRIORITY.get((report_type or "").strip(), 50)


def select_one_per_local_hour(records):
    """Select one real report per local hour; do not create missing hours."""
    grouped = defaultdict(list)
    for r in records:
        dt = r["datetime_cst"]
        slot = dt.replace(minute=0, second=0, microsecond=0)
        r["hour_cst"] = slot
        r["minute_offset"] = abs(dt.minute + dt.second / 60.0)
        grouped[slot].append(r)

    selected = []
    for slot in sorted(grouped):
        candidates = grouped[slot]
        candidates.sort(key=lambda r: (r["minute_offset"], report_rank(r["report_type"]), r["datetime_cst"]))
        chosen = dict(candidates[0])
        chosen["reports_in_hour"] = len(candidates)
        selected.append(chosen)
    return selected


def write_csv(path: Path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            out = {}
            for k in fields:
                v = row.get(k, "")
                if isinstance(v, datetime):
                    v = v.strftime("%Y-%m-%d %H:%M:%S")
                out[k] = v
            w.writerow(out)


def main():
    manifest = []
    native_records = []

    for year in range(START_YEAR, END_YEAR + 1):
        url = BASE_URL.format(year=year)
        try:
            payload = fetch(url)
        except Exception as exc:
            manifest.append({"year": year, "status": "FAILED", "bytes": 0, "url": url, "error": str(exc)})
            print(f"[{year}] FAILED: {exc}")
            continue

        manifest.append({"year": year, "status": "OK", "bytes": len(payload), "url": url, "error": ""})
        text = payload.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        count = 0
        valid_temp = 0
        for row in reader:
            count += 1
            temp, temp_q = parse_tmp(row.get("TMP", ""))
            if temp is None:
                continue
            dt_utc = parse_dt(row.get("DATE", ""))
            if dt_utc is None:
                continue
            dt_cst = dt_utc + timedelta(hours=UTC_OFFSET_HOURS)
            valid_temp += 1
            native_records.append({
                "station": row.get("STATION", STATION),
                "name": row.get("NAME", ""),
                "latitude": row.get("LATITUDE", ""),
                "longitude": row.get("LONGITUDE", ""),
                "elevation_m": row.get("ELEVATION", ""),
                "datetime_utc": dt_utc,
                "datetime_cst": dt_cst,
                "temp_c": round(temp, 1),
                "temp_quality_flag": temp_q,
                "report_type": row.get("REPORT_TYPE", ""),
                "source": row.get("SOURCE", ""),
                "quality_control": row.get("QUALITY_CONTROL", ""),
                "year_source_file": year,
                "source_url": url,
            })
        print(f"[{year}] downloaded={len(payload):,} bytes rows={count:,} valid_temp={valid_temp:,}")

    selected = select_one_per_local_hour(native_records)

    # Daily summaries based only on genuinely observed local-hour slots.
    daily_groups = defaultdict(list)
    for r in selected:
        daily_groups[r["hour_cst"].date()].append(r)

    daily_rows = []
    for d in sorted(daily_groups):
        rs = daily_groups[d]
        temps = [r["temp_c"] for r in rs]
        hours = sorted({r["hour_cst"].hour for r in rs})
        n = len(hours)
        tmin = min(temps)
        tmax = max(temps)
        tmin_r = min(rs, key=lambda r: r["temp_c"])
        tmax_r = max(rs, key=lambda r: r["temp_c"])
        daily_rows.append({
            "date_cst": d.isoformat(),
            "year": d.year,
            "month": d.month,
            "day": d.day,
            "n_distinct_observed_hours": n,
            "coverage_grade": grade(n),
            "observed_hours_cst": " ".join(f"{h:02d}" for h in hours),
            "tmin_sample_c": round(tmin, 1),
            "tmin_sample_time_cst": tmin_r["datetime_cst"].strftime("%Y-%m-%d %H:%M:%S"),
            "tmax_sample_c": round(tmax, 1),
            "tmax_sample_time_cst": tmax_r["datetime_cst"].strftime("%Y-%m-%d %H:%M:%S"),
            "dtr_sample_c": round(tmax - tmin, 1),
            "suitable_for_curve_validation": "YES" if n >= 20 else "NO",
            "suitable_for_sparse_htemp_validation": "YES" if n >= 8 else "NO",
            "note": "Sample extrema from available reports; may differ from official daily extrema when coverage <20 h.",
        })

    by_year = defaultdict(list)
    for row in daily_rows:
        by_year[row["year"]].append(row)

    yearly_rows = []
    for year in range(START_YEAR, END_YEAR + 1):
        rows = by_year.get(year, [])
        counts = [r["n_distinct_observed_hours"] for r in rows]
        grades = {g: sum(1 for r in rows if r["coverage_grade"] == g) for g in "ABCD"}
        growing = [r for r in rows if 4 <= r["month"] <= 10]
        maize = [r for r in rows if 5 <= r["month"] <= 9]
        dtr_ab = [r["dtr_sample_c"] for r in rows if r["coverage_grade"] in {"A", "B"}]
        yearly_rows.append({
            "year": year,
            "days_with_any_temperature": len(rows),
            "median_observed_hours_per_day": round(statistics.median(counts), 1) if counts else "",
            "A_days_ge20h": grades["A"],
            "B_days_8_19h": grades["B"],
            "C_days_4_7h": grades["C"],
            "D_days_lt4h": grades["D"],
            "A_or_B_days": grades["A"] + grades["B"],
            "apr_oct_A_or_B_days": sum(1 for r in growing if r["coverage_grade"] in {"A", "B"}),
            "may_sep_A_or_B_days": sum(1 for r in maize if r["coverage_grade"] in {"A", "B"}),
            "mean_sample_dtr_A_or_B_c": round(statistics.mean(dtr_ab), 2) if dtr_ab else "",
            "max_sample_dtr_A_or_B_c": round(max(dtr_ab), 1) if dtr_ab else "",
            "decision": (
                "FULL_HOURLY_CANDIDATE" if grades["A"] >= 100 else
                "SPARSE_VALIDATION_CANDIDATE" if grades["A"] + grades["B"] >= 100 else
                "WEAK_COVERAGE"
            ),
        })

    hourly_fields = [
        "station", "name", "latitude", "longitude", "elevation_m",
        "datetime_utc", "datetime_cst", "hour_cst", "temp_c",
        "temp_quality_flag", "report_type", "source", "quality_control",
        "reports_in_hour", "minute_offset", "year_source_file", "source_url",
    ]
    write_csv(OUT / f"{STATION}_hourly_observed_2000_2024.csv", selected, hourly_fields)

    daily_fields = [
        "date_cst", "year", "month", "day", "n_distinct_observed_hours", "coverage_grade",
        "observed_hours_cst", "tmin_sample_c", "tmin_sample_time_cst", "tmax_sample_c",
        "tmax_sample_time_cst", "dtr_sample_c", "suitable_for_curve_validation",
        "suitable_for_sparse_htemp_validation", "note",
    ]
    write_csv(OUT / f"{STATION}_daily_dtr_qc_2000_2024.csv", daily_rows, daily_fields)

    yearly_fields = [
        "year", "days_with_any_temperature", "median_observed_hours_per_day", "A_days_ge20h",
        "B_days_8_19h", "C_days_4_7h", "D_days_lt4h", "A_or_B_days",
        "apr_oct_A_or_B_days", "may_sep_A_or_B_days", "mean_sample_dtr_A_or_B_c",
        "max_sample_dtr_A_or_B_c", "decision",
    ]
    write_csv(OUT / f"{STATION}_yearly_qc_2000_2024.csv", yearly_rows, yearly_fields)
    write_csv(OUT / f"{STATION}_source_manifest_2000_2024.csv", manifest,
              ["year", "status", "bytes", "url", "error"])

    # Compact machine-readable and human-readable verdict.
    total_ab = sum(r["A_or_B_days"] for r in yearly_rows)
    total_a = sum(r["A_days_ge20h"] for r in yearly_rows)
    maize_ab = sum(r["may_sep_A_or_B_days"] for r in yearly_rows)
    ok_years = sum(1 for m in manifest if m["status"] == "OK")
    verdict = "FULL_CURVE_FEASIBLE" if total_a >= 500 else ("SPARSE_HTEMP_FEASIBLE" if total_ab >= 1000 else "LIMITED")

    md = f"""# NOAA 51463099999 data QC result\n\n- Station: `{STATION}` (Urumqi)\n- Requested years: {START_YEAR}-{END_YEAR}\n- NOAA annual files downloaded successfully: **{ok_years}/{END_YEAR-START_YEAR+1}**\n- Selected real local-hour temperature observations: **{len(selected):,}**\n- Days with >=20 distinct observed hours (Grade A): **{total_a:,}**\n- Days with >=8 distinct observed hours (Grade A+B): **{total_ab:,}**\n- May-Sep Grade A+B days: **{maize_ab:,}**\n- Initial HTEMP data verdict: **{verdict}**\n\n## Interpretation\n\n`A` days can support direct daily-curve validation. `B` days support HTEMP comparison only at hours actually observed. `C/D` days are auxiliary. No interpolation has been applied. Daily Tmax/Tmin and DTR in the processed table are sample extrema from available reports and must not be called official daily extrema when coverage is incomplete.\n\n## Source\n\nNOAA NCEI Global Hourly / Integrated Surface Database:\nhttps://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database\n\nAnnual files:\nhttps://www.ncei.noaa.gov/data/global-hourly/access/YYYY/{STATION}.csv\n"""
    (OUT / "README_QC.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
