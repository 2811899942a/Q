#!/usr/bin/env python3
"""Download NOAA GHCN-Daily for Urumqi CHM00051463 and merge official TMAX/TMIN
with the already processed ISD sparse sub-daily observations.

Scientific intent:
- GHCN-Daily provides official daily TMAX/TMIN -> DTR.
- ISD/Global Hourly provides real sub-daily observations (~8 times/day).
- DTR is therefore not estimated from sparse ISD sample extrema when GHCN data exist.
"""

from __future__ import annotations

import csv
import gzip
import io
import os
import statistics
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

GHCN_ID = "CHM00051463"
ISD_ID = "51463099999"
START_YEAR = int(os.environ.get("START_YEAR", "2000"))
END_YEAR = int(os.environ.get("END_YEAR", "2024"))
URL = f"https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/{GHCN_ID}.csv.gz"

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed_51463"
ISD_DAILY = OUT / f"{ISD_ID}_daily_dtr_qc_2000_2024.csv"
GHCN_OUT = OUT / f"{GHCN_ID}_daily_tmax_tmin_2000_2024.csv"
MERGED_OUT = OUT / f"{ISD_ID}_htemp_validation_daily_2000_2024.csv"
SUMMARY_OUT = OUT / "README_DTR_MERGED.md"


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "DSSAT-DTR-research/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def main():
    payload = download(URL)
    raw = gzip.decompress(payload).decode("utf-8", errors="replace")

    # by_station schema: ID, YYYYMMDD, ELEMENT, VALUE, MFLAG, QFLAG, SFLAG, OBS_TIME
    by_date = defaultdict(dict)
    for row in csv.reader(io.StringIO(raw)):
        if len(row) < 4:
            continue
        sid, datestr, element, value = row[:4]
        mflag = row[4] if len(row) > 4 else ""
        qflag = row[5] if len(row) > 5 else ""
        sflag = row[6] if len(row) > 6 else ""
        obs_time = row[7] if len(row) > 7 else ""
        if sid != GHCN_ID or element not in {"TMAX", "TMIN"}:
            continue
        dt = datetime.strptime(datestr, "%Y%m%d").date()
        if not (START_YEAR <= dt.year <= END_YEAR):
            continue
        try:
            val_c = int(value) / 10.0  # GHCN TMAX/TMIN are tenths deg C
        except ValueError:
            continue
        # Keep record even if qflag populated, but expose flag so downstream can exclude it.
        by_date[dt][element] = val_c
        by_date[dt][f"{element}_mflag"] = mflag
        by_date[dt][f"{element}_qflag"] = qflag
        by_date[dt][f"{element}_sflag"] = sflag
        by_date[dt][f"{element}_obs_time"] = obs_time

    ghcn_rows = []
    for dt in sorted(by_date):
        d = by_date[dt]
        tmax = d.get("TMAX")
        tmin = d.get("TMIN")
        valid_pair = tmax is not None and tmin is not None
        qgood = not d.get("TMAX_qflag", "") and not d.get("TMIN_qflag", "")
        ghcn_rows.append({
            "date_cst": dt.isoformat(),
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "ghcn_tmax_c": "" if tmax is None else round(tmax, 1),
            "ghcn_tmin_c": "" if tmin is None else round(tmin, 1),
            "ghcn_dtr_c": "" if not valid_pair else round(tmax - tmin, 1),
            "ghcn_tmax_qflag": d.get("TMAX_qflag", ""),
            "ghcn_tmin_qflag": d.get("TMIN_qflag", ""),
            "ghcn_pair_complete": "YES" if valid_pair else "NO",
            "ghcn_pair_qc_clean": "YES" if valid_pair and qgood else "NO",
            "source": URL,
        })

    fields = list(ghcn_rows[0].keys()) if ghcn_rows else []
    with GHCN_OUT.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(ghcn_rows)

    if not ISD_DAILY.exists():
        raise FileNotFoundError(f"Missing prerequisite: {ISD_DAILY}")

    ghcn_map = {r["date_cst"]: r for r in ghcn_rows}
    merged = []
    with ISD_DAILY.open("r", newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            g = ghcn_map.get(r["date_cst"], {})
            row = dict(r)
            for k in [
                "ghcn_tmax_c", "ghcn_tmin_c", "ghcn_dtr_c",
                "ghcn_tmax_qflag", "ghcn_tmin_qflag",
                "ghcn_pair_complete", "ghcn_pair_qc_clean",
            ]:
                row[k] = g.get(k, "")
            # Formal DTR for downstream model validation.
            row["formal_dtr_c"] = g.get("ghcn_dtr_c", "") if g.get("ghcn_pair_qc_clean") == "YES" else ""
            row["formal_dtr_source"] = "GHCN-Daily CHM00051463" if row["formal_dtr_c"] != "" else "MISSING"
            merged.append(row)

    merged_fields = list(merged[0].keys()) if merged else []
    with MERGED_OUT.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=merged_fields)
        w.writeheader()
        w.writerows(merged)

    valid_ghcn = [r for r in merged if r.get("formal_dtr_c") != ""]
    bplus = [r for r in valid_ghcn if r.get("coverage_grade") in {"A", "B"}]
    maize = [r for r in bplus if 5 <= int(r["month"]) <= 9]

    def asfloat(r):
        return float(r["formal_dtr_c"])

    dtr15 = [r for r in bplus if asfloat(r) >= 15.0]
    dtr20 = [r for r in bplus if asfloat(r) >= 20.0]
    maize15 = [r for r in maize if asfloat(r) >= 15.0]
    maize20 = [r for r in maize if asfloat(r) >= 20.0]

    yearly = defaultdict(lambda: {"all": 0, "bplus": 0, "dtr15": 0, "dtr20": 0, "maize": 0, "maize15": 0, "maize20": 0})
    for r in valid_ghcn:
        y = int(r["year"])
        yearly[y]["all"] += 1
        if r.get("coverage_grade") in {"A", "B"}:
            yearly[y]["bplus"] += 1
            d = asfloat(r)
            if d >= 15: yearly[y]["dtr15"] += 1
            if d >= 20: yearly[y]["dtr20"] += 1
            if 5 <= int(r["month"]) <= 9:
                yearly[y]["maize"] += 1
                if d >= 15: yearly[y]["maize15"] += 1
                if d >= 20: yearly[y]["maize20"] += 1

    yearly_path = OUT / f"{ISD_ID}_formal_dtr_yearly_summary_2000_2024.csv"
    with yearly_path.open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["year", "ghcn_pair_days", "isd_grade_A_or_B_days", "dtr_ge15_days", "dtr_ge20_days", "may_sep_days", "may_sep_dtr_ge15_days", "may_sep_dtr_ge20_days"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for y in range(START_YEAR, END_YEAR + 1):
            d = yearly[y]
            w.writerow({
                "year": y,
                "ghcn_pair_days": d["all"],
                "isd_grade_A_or_B_days": d["bplus"],
                "dtr_ge15_days": d["dtr15"],
                "dtr_ge20_days": d["dtr20"],
                "may_sep_days": d["maize"],
                "may_sep_dtr_ge15_days": d["maize15"],
                "may_sep_dtr_ge20_days": d["maize20"],
            })

    dtr_vals = [asfloat(r) for r in bplus]
    maize_vals = [asfloat(r) for r in maize]
    summary = f"""# Urumqi 51463 formal DTR merge result

- GHCN station: `{GHCN_ID}`
- ISD station: `{ISD_ID}`
- Period: {START_YEAR}-{END_YEAR}
- GHCN daily TMAX/TMIN pairs merged: **{len(valid_ghcn):,}** days
- Days with both clean GHCN DTR and ISD Grade A/B sub-daily observations: **{len(bplus):,}**
- May-Sep matched days: **{len(maize):,}**
- Formal DTR >=15 C days (matched A/B): **{len(dtr15):,}**
- Formal DTR >=20 C days (matched A/B): **{len(dtr20):,}**
- May-Sep DTR >=15 C days: **{len(maize15):,}**
- May-Sep DTR >=20 C days: **{len(maize20):,}**
- Mean formal DTR on matched A/B days: **{statistics.mean(dtr_vals):.2f} C**
- Mean formal DTR in May-Sep matched days: **{statistics.mean(maize_vals):.2f} C**

## Formal use rule

For DSSAT-DTR experiments, define daily DTR from GHCN-Daily (`TMAX-TMIN`) and use the ISD observations only as real sub-daily checkpoints for the reconstructed temperature curve. Do not derive the formal daily DTR from the sparse ISD sample extrema.

## Sources

- GHCN-Daily station file: {URL}
- NOAA GHCN-Daily documentation: https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt
- NOAA Global Hourly / ISD: https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database
"""
    SUMMARY_OUT.write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
