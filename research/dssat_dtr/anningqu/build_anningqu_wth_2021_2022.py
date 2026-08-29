#!/usr/bin/env python3
"""Build publication-auditable DSSAT v4.8.5 weather files for Anningqu 2021-2022.

Temperature hierarchy
---------------------
1. NOAA Global Hourly station 51463599999 (Diwopu), grouped by local apparent
   solar date; accept a daily Tmax/Tmin only when >=20 distinct observed solar
   hours are present after source QC.
2. NOAA GHCN-Daily CHM00051463 TMAX/TMIN, used only for dense-station gaps.
3. NASA POWER daily T2M_MAX/T2M_MIN at the Anningqu coordinate, last-resort gap
   fill only.

Radiation and precipitation
---------------------------
- NASA POWER daily LST at 87.49 E, 43.95 N:
  ALLSKY_SFC_SW_DWN (MJ m-2 d-1) and PRECTOTCORR (mm d-1).
- M0 and M15 use the exact same generated WTH files.

Daily date convention
---------------------
NOAA subdaily reports are converted UTC -> China Standard Time -> local apparent
solar time with station longitude and equation of time, then grouped by solar
calendar date. NASA POWER is requested in LST. This keeps daily extrema and
radiation on the same solar-day convention as the HTEMP validation.

TAV/AMP
-------
Calculated from dense 51463599999 observations over 2000-2024 using only days
with >=20 distinct solar hours:
- TAV = mean of the 12 climatological monthly mean temperatures.
- AMP = max(monthly climatological Tmean) - min(monthly climatological Tmean).

Outputs
-------
- data/anningqu/ANQH2101.WTH
- data/anningqu/ANQH2201.WTH
- data/anningqu/anningqu_wth_daily_2021_2022.csv
- data/anningqu/anningqu_wth_qc_by_year.csv
- data/anningqu/README_ANINGQU_WTH.md
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import math
import statistics
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "anningqu"
OUT.mkdir(parents=True, exist_ok=True)

DENSE_ST = "51463599999"
DENSE_LON = 87.474244
STD_MERIDIAN = 120.0
GHCN_ST = "CHM00051463"
LAT = 43.95
LON = 87.49
ELEV = 590
INSI = "ANQH"
YEARS = (2021, 2022)
BAD_TMP_QC = {"2", "3", "6", "7"}


def get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "DSSAT-Urumqi-public-reconstruction/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_tmp(field: str):
    if not field or field.strip() == "":
        return None, ""
    parts = field.split(",")
    try:
        raw = int(parts[0])
    except Exception:
        return None, ""
    if raw in (9999, 99999, -9999):
        return None, parts[1].strip() if len(parts) > 1 else ""
    qc = parts[1].strip() if len(parts) > 1 else ""
    return raw / 10.0, qc


def eot_minutes(doy: int) -> float:
    b = math.radians((360.0 / 365.0) * (doy - 81.0))
    return 9.87 * math.sin(2.0 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def utc_to_solar(dt_utc: datetime) -> datetime:
    cst = dt_utc + timedelta(hours=8)
    correction = 4.0 * (DENSE_LON - STD_MERIDIAN) + eot_minutes(cst.timetuple().tm_yday)
    return cst + timedelta(minutes=correction)


def load_dense_all_years():
    """Return accepted daily extrema and monthly mean temperatures for 2000-2024."""
    by_day = defaultdict(list)
    for y in range(2000, 2025):
        url = f"https://www.ncei.noaa.gov/data/global-hourly/access/{y}/{DENSE_ST}.csv"
        text = get(url, 90).decode("utf-8-sig", errors="replace")
        for r in csv.DictReader(io.StringIO(text)):
            t, qc = parse_tmp(r.get("TMP", ""))
            if t is None or qc in BAD_TMP_QC:
                continue
            try:
                dt = datetime.fromisoformat(r["DATE"].replace("Z", ""))
            except Exception:
                continue
            sol = utc_to_solar(dt)
            by_day[sol.date()].append((sol, t))

    daily = {}
    monthly_tmean = defaultdict(list)
    for d, vals in sorted(by_day.items()):
        # One representative report per solar hour, nearest to the integer hour.
        hour_groups = defaultdict(list)
        for sol, t in vals:
            hour_groups[sol.hour].append((sol, t))
        reps = []
        for h, hv in hour_groups.items():
            target = datetime.combine(d, datetime.min.time()) + timedelta(hours=h)
            reps.append(min(hv, key=lambda z: abs((z[0] - target).total_seconds())))
        if len(reps) < 20:
            continue
        temps = [t for _, t in reps]
        tx, tn = max(temps), min(temps)
        daily[d] = {"tmax": tx, "tmin": tn, "n_hours": len(reps)}
        monthly_tmean[(d.year, d.month)].append((tx + tn) / 2.0)
    return daily, monthly_tmean


def climate_tav_amp(monthly_tmean):
    month_clim = {}
    for m in range(1, 13):
        vals = []
        for (y, mm), xs in monthly_tmean.items():
            if mm == m and xs:
                vals.append(statistics.mean(xs))
        if not vals:
            raise RuntimeError(f"No dense-station climatology for month {m}")
        month_clim[m] = statistics.mean(vals)
    tav = statistics.mean(month_clim.values())
    amp = max(month_clim.values()) - min(month_clim.values())
    return tav, amp, month_clim


def load_ghcn():
    url = f"https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/{GHCN_ST}.csv.gz"
    raw = gzip.decompress(get(url, 120)).decode("utf-8", errors="replace")
    out = defaultdict(dict)
    # GHCN by_station format: ID,DATE,ELEMENT,DATA_VALUE,MFLAG,QFLAG,SFLAG,OBS_TIME
    for row in csv.reader(io.StringIO(raw)):
        if len(row) < 4 or row[2] not in {"TMAX", "TMIN"}:
            continue
        qflag = row[5].strip() if len(row) > 5 else ""
        if qflag:
            continue
        try:
            d = datetime.strptime(row[1], "%Y%m%d").date()
            v = float(row[3]) / 10.0
        except Exception:
            continue
        out[d][row[2]] = v
    return {d: {"tmax": x["TMAX"], "tmin": x["TMIN"]} for d, x in out.items() if "TMAX" in x and "TMIN" in x}


def load_power(start="20210101", end="20221231"):
    params = "ALLSKY_SFC_SW_DWN,PRECTOTCORR,T2M_MAX,T2M_MIN"
    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters={params}&community=AG&longitude={LON}&latitude={LAT}"
        f"&start={start}&end={end}&format=JSON&time-standard=LST"
    )
    j = json.loads(get(url, 180).decode("utf-8"))
    p = j["properties"]["parameter"]
    out = {}
    for k in p["ALLSKY_SFC_SW_DWN"]:
        try:
            d = datetime.strptime(k, "%Y%m%d").date()
            vals = {
                "srad": float(p["ALLSKY_SFC_SW_DWN"][k]),
                "rain": float(p["PRECTOTCORR"][k]),
                "tmax": float(p["T2M_MAX"][k]),
                "tmin": float(p["T2M_MIN"][k]),
            }
        except Exception:
            continue
        if any(v < -900 for v in vals.values()):
            continue
        out[d] = vals
    return out, url


def daterange(y):
    d = date(y, 1, 1)
    end = date(y + 1, 1, 1)
    while d < end:
        yield d
        d += timedelta(days=1)


def build_daily(dense, ghcn, power):
    rows = []
    for y in YEARS:
        for d in daterange(y):
            if d not in power:
                raise RuntimeError(f"Missing POWER day {d}")
            if d in dense:
                tx, tn = dense[d]["tmax"], dense[d]["tmin"]
                t_source = "NOAA_ISD_514635_DENSE"
                n_hours = dense[d]["n_hours"]
            elif d in ghcn:
                tx, tn = ghcn[d]["tmax"], ghcn[d]["tmin"]
                t_source = "NOAA_GHCN_CHM00051463_FALLBACK"
                n_hours = 0
            else:
                tx, tn = power[d]["tmax"], power[d]["tmin"]
                t_source = "NASA_POWER_T2M_FALLBACK"
                n_hours = 0
            if tx < tn:
                raise RuntimeError(f"TMAX<TMIN on {d}: {tx} < {tn}")
            rows.append({
                "date": d.isoformat(), "year": y, "doy": d.timetuple().tm_yday,
                "srad_mj_m2_d": power[d]["srad"], "tmax_c": tx, "tmin_c": tn,
                "rain_mm": max(0.0, power[d]["rain"]), "temperature_source": t_source,
                "dense_observed_hours": n_hours,
            })
    return rows


def write_wth(year, rows, tav, amp):
    path = OUT / f"{INSI}{str(year)[-2:]}01.WTH"
    with path.open("w", encoding="ascii", newline="\n") as f:
        f.write("*WEATHER DATA : Anningqu,Urumqi,Xinjiang,China - public reconstruction\n\n")
        f.write("@ INSI      LAT     LONG  ELEV   TAV   AMP REFHT WNDHT\n")
        f.write(f"  {INSI:<4s}  {LAT:7.3f}  {LON:8.3f} {ELEV:5d} {tav:5.1f} {amp:5.1f}  2.00  3.00\n")
        f.write("@DATE  SRAD  TMAX  TMIN  RAIN\n")
        yy = str(year)[-2:]
        for r in rows:
            f.write(
                f"{yy}{int(r['doy']):03d} {float(r['srad_mj_m2_d']):5.1f}"
                f" {float(r['tmax_c']):5.1f} {float(r['tmin_c']):5.1f} {float(r['rain_mm']):5.1f}\n"
            )
    return path


def main():
    dense, monthly = load_dense_all_years()
    tav, amp, month_clim = climate_tav_amp(monthly)
    ghcn = load_ghcn()
    power, power_url = load_power()
    rows = build_daily(dense, ghcn, power)

    daily_path = OUT / "anningqu_wth_daily_2021_2022.csv"
    with daily_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    wth_paths = []
    qc_rows = []
    for y in YEARS:
        yr = [r for r in rows if r["year"] == y]
        wth_paths.append(write_wth(y, yr, tav, amp))
        c = Counter(r["temperature_source"] for r in yr)
        may_oct = [r for r in yr if 5 <= datetime.strptime(r["date"], "%Y-%m-%d").month <= 10]
        qc_rows.append({
            "year": y, "n_days": len(yr), "dense_temp_days": c["NOAA_ISD_514635_DENSE"],
            "ghcn_fallback_days": c["NOAA_GHCN_CHM00051463_FALLBACK"],
            "power_temp_fallback_days": c["NASA_POWER_T2M_FALLBACK"],
            "annual_rain_mm": round(sum(r["rain_mm"] for r in yr), 2),
            "may_oct_rain_mm": round(sum(r["rain_mm"] for r in may_oct), 2),
            "annual_mean_tmax_c": round(statistics.mean(r["tmax_c"] for r in yr), 3),
            "annual_mean_tmin_c": round(statistics.mean(r["tmin_c"] for r in yr), 3),
            "max_tmax_c": round(max(r["tmax_c"] for r in yr), 2),
            "min_tmin_c": round(min(r["tmin_c"] for r in yr), 2),
            "mean_srad_mj_m2_d": round(statistics.mean(r["srad_mj_m2_d"] for r in yr), 3),
        })

    qc_path = OUT / "anningqu_wth_qc_by_year.csv"
    with qc_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(qc_rows[0].keys())); w.writeheader(); w.writerows(qc_rows)

    clim_txt = ", ".join(f"{m}:{month_clim[m]:.2f}" for m in range(1,13))
    q2022 = next(r for r in qc_rows if r["year"] == 2022)
    temp_counts = Counter(r["temperature_source"] for r in rows)
    readme = f"""# Anningqu DSSAT weather reconstruction, 2021-2022

## Status

Two standard DSSAT v4.8.5 weather files were generated:
- `{wth_paths[0].name}`
- `{wth_paths[1].name}`

Station metadata used for the Anningqu experiment: `{INSI}`, {LAT:.3f} N, {LON:.3f} E, {ELEV} m.

## Temperature hierarchy

Across 2021-2022 ({len(rows)} calendar days):
- dense NOAA ISD 51463599999 days (>=20 distinct solar hours): **{temp_counts['NOAA_ISD_514635_DENSE']}**
- GHCN CHM00051463 fallback days: **{temp_counts['NOAA_GHCN_CHM00051463_FALLBACK']}**
- NASA POWER T2M fallback days: **{temp_counts['NASA_POWER_T2M_FALLBACK']}**

No interpolation was used to create a daily station Tmax/Tmin. Each day is either based on dense real reports or explicitly flagged as a fallback source.

## Radiation and precipitation

Daily SRAD and RAIN come from NASA POWER at the Anningqu coordinate in **LST**:
`ALLSKY_SFC_SW_DWN` and `PRECTOTCORR`.

POWER request used by the workflow:
`{power_url}`

This rainfall is a gridded/reanalysis-derived public estimate, not a local rain-gauge measurement. It must therefore remain a disclosed uncertainty/sensitivity dimension. For the first crop propagation experiment, the fully irrigated treatment is preferred because temperature-pathway attribution is cleaner.

## DSSAT climate constants

Using dense NOAA 51463599999 daily extrema from 2000-2024 on days with >=20 observed solar hours:
- `TAV = {tav:.2f} C`
- `AMP = {amp:.2f} C`
- monthly climatological Tmean (Jan-Dec C): {clim_txt}

These values are used identically in M0 and M15.

## 2022 same-site external consistency check

The public 2022-2023 DSSAT peanut study at the Anningqu Comprehensive Experimental Station reports 2022 growing-season rainfall of about **63.1 mm** and a temperature envelope of approximately **Tmax 3.7-38.5 C / Tmin -1.4-26.6 C** during its stated season.

Current public WTH reconstruction gives for 2022:
- May-Oct POWER rainfall: **{q2022['may_oct_rain_mm']:.2f} mm**
- full-year maximum Tmax: **{q2022['max_tmax_c']:.2f} C**
- full-year minimum Tmin: **{q2022['min_tmin_c']:.2f} C**

The rainfall values are not expected to match exactly because the paper reports local station/experimental-season precipitation whereas POWER is a gridded estimate and May-Oct is a fixed comparison window. Any material discrepancy is retained as uncertainty rather than scaled away.

## Comparison rule

M0 official DSSAT v4.8.5 and M15 must use these exact same WTH files. No weather variable is recalibrated separately for either source version. The M15 `CLOUDS` driver is calculated internally by DSSAT from the WTH SRAD using its existing `SOLAR.for` pathway.
"""
    (OUT / "README_ANINGQU_WTH.md").write_text(readme, encoding="utf-8")
    print(readme)

if __name__ == "__main__":
    main()
