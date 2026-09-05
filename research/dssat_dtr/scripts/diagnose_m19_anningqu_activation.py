#!/usr/bin/env python3
"""Diagnose whether tracked Anningqu weather activates the M19 regional trigger.

This isolates the weather-side trigger from crop-model propagation. It uses the
same K_RT, Kt0 and 366-day Urumqi DTR climatology as the frozen M19 source patch.
"""
from __future__ import annotations

import csv
import json
import math
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PROFILE = REPO / "research/dssat_dtr/data/m19_regional_anomaly_threshold/regional_dtr_profile_2000_2016.csv"
PARAMS = REPO / "research/dssat_dtr/data/m19_regional_anomaly_threshold/parameters.json"
WTH_DIR = REPO / "research/dssat_dtr/data/anningqu/formal_ghcn_rain"
OUT = REPO / "research/dssat_dtr/data/anningqu/m19_activation_diagnostic"
LAT = 43.95


def load_profile():
    with PROFILE.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 366:
        raise ValueError(f"expected 366 profile rows, got {len(rows)}")
    return {
        i + 1: (float(row["dtr_mean_c"]), float(row["dtr_sd_c"]))
        for i, row in enumerate(rows)
    }


def extraterrestrial_radiation(doy: int, lat_deg: float) -> float:
    pi = math.pi
    lat = math.radians(lat_deg)
    dr = 1.0 + 0.033 * math.cos(2.0 * pi * doy / 365.0)
    dec = 0.409 * math.sin(2.0 * pi * doy / 365.0 - 1.39)
    x = max(-1.0, min(1.0, -math.tan(lat) * math.tan(dec)))
    ws = math.acos(x)
    return (24.0 * 60.0 / pi) * 0.0820 * dr * (
        ws * math.sin(lat) * math.sin(dec)
        + math.cos(lat) * math.cos(dec) * math.sin(ws)
    )


def parse_wth(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith(("*", "@")):
            continue
        parts = s.split()
        if len(parts) < 5 or not parts[0].isdigit():
            continue
        yyddd = parts[0]
        yy = int(yyddd[:2])
        year = 2000 + yy if yy < 70 else 1900 + yy
        doy = int(yyddd[2:])
        rows.append(
            {
                "year": year,
                "doy": doy,
                "date": date(year, 1, 1) + timedelta(days=doy - 1),
                "srad": float(parts[1]),
                "tmax": float(parts[2]),
                "tmin": float(parts[3]),
            }
        )
    return rows


def main():
    profile = load_profile()
    params = json.loads(PARAMS.read_text(encoding="utf-8"))
    krt = float(params["K_RT"])
    kt0 = float(params["Kt0"])
    gain_scale = float(params["gain_scale"])

    daily = []
    for weather_name in ("ANQH2101.WTH", "ANQH2201.WTH"):
        for row in parse_wth(WTH_DIR / weather_name):
            mu, sd = profile[row["doy"]]
            dtr = row["tmax"] - row["tmin"]
            z = (dtr - mu) / sd if sd > 1e-12 else float("nan")
            ra = extraterrestrial_radiation(row["doy"], LAT)
            kt = row["srad"] / ra if ra > 1e-12 else float("nan")
            e = max(z - krt, 0.0) * max(kt0 - kt, 0.0) / 0.1
            strength = 1.0 - math.exp(-e / gain_scale) if e > 0 else 0.0
            daily.append(
                {
                    **row,
                    "dtr": dtr,
                    "z_dtr": z,
                    "ra": ra,
                    "kt": kt,
                    "exposure": e,
                    "strength": strength,
                    "trigger": int(e > 0),
                }
            )

    windows = []
    for year in (2021, 2022):
        windows.append((year, "FULL_YEAR", date(year, 1, 1), date(year, 12, 31)))
        windows.append((year, "MAY_SEP", date(year, 5, 1), date(year, 9, 30)))
        for month, day, label in [
            (4, 21, "SOW_APR21_TO_OCT31"),
            (4, 26, "SOW_APR26_TO_OCT31"),
            (5, 6, "SOW_MAY06_TO_OCT31"),
            (5, 16, "SOW_MAY16_TO_OCT31"),
            (5, 26, "SOW_MAY26_TO_OCT31"),
        ]:
            windows.append((year, label, date(year, month, day), date(year, 10, 31)))

    summary = []
    for year, label, start, end in windows:
        subset = [r for r in daily if r["year"] == year and start <= r["date"] <= end]
        active = [r for r in subset if r["trigger"]]
        summary.append(
            {
                "year": year,
                "window": label,
                "n_days": len(subset),
                "active_days": len(active),
                "active_fraction": len(active) / len(subset) if subset else 0.0,
                "max_z_dtr": max((r["z_dtr"] for r in subset), default=float("nan")),
                "max_exposure": max((r["exposure"] for r in subset), default=0.0),
                "mean_active_strength": sum(r["strength"] for r in active) / len(active) if active else 0.0,
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "activation_summary.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    top = sorted(daily, key=lambda r: r["exposure"], reverse=True)[:40]
    with (OUT / "top_activation_days.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        fields = ["date", "year", "doy", "srad", "tmax", "tmin", "dtr", "z_dtr", "ra", "kt", "exposure", "strength", "trigger"]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in top:
            writer.writerow({key: row[key] for key in fields})

    full_active = sum(r["trigger"] for r in daily)
    growing_active = sum(r["trigger"] for r in daily if 5 <= r["date"].month <= 9)
    lines = [
        "# M19 Anningqu activation diagnostic",
        "",
        f"K_RT = {krt:.2f} SD; Kt0 = {kt0:.2f}; gain_scale = {gain_scale:.2f}.",
        f"Across 2021-2022 full weather records: {full_active} active days.",
        f"Across May-September 2021-2022: {growing_active} active days.",
        "",
        "This diagnostic separates weather-trigger activation from downstream CERES-Maize use. A nonzero active-day count together with zero crop-output change demonstrates an interface/propagation gap rather than a dormant M19 trigger.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
