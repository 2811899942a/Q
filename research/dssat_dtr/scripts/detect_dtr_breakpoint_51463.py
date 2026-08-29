#!/usr/bin/env python3
"""Detect a local DTR breakpoint in Urumqi DSSAT HTEMP residual diagnostics.

The model is a continuous segmented regression:

  y = b0 + b1*DTR + b2*max(0, DTR-c)

where c is searched from 10.0 to 18.0 C in 0.1 C increments.
The script is mechanism-oriented: it estimates whether morning bias, afternoon bias,
AM-PM asymmetry, and daily RMSE share a stable breakpoint, and checks stability
between 2000-2016 and 2017-2024 May-Sep periods.

The standalone workflow intentionally reuses the committed daily residual table so
breakpoint estimation can be rerun without redownloading NOAA data or recalibrating PL-XJ.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed_51463"
INFILE = DATA / "dtr_asymmetry_daily.csv"
OUT = DATA / "dtr_breakpoint_results.csv"
STAB = DATA / "dtr_breakpoint_stability.csv"
README = DATA / "README_DTR_BREAKPOINT.md"

TARGETS = [
    ("morning_bias_c", "Morning bias"),
    ("afternoon_bias_c", "Afternoon bias"),
    ("asymmetry_gap_c", "Afternoon-minus-morning bias"),
    ("daily_rmse_c", "Daily RMSE"),
]


def solve3(a, b):
    m = [list(a[i]) + [b[i]] for i in range(3)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            return None
        m[col], m[pivot] = m[pivot], m[col]
        p = m[col][col]
        for j in range(col, 4):
            m[col][j] /= p
        for r in range(3):
            if r == col:
                continue
            fac = m[r][col]
            for j in range(col, 4):
                m[r][j] -= fac * m[col][j]
    return [m[i][3] for i in range(3)]


def fit_hinge(rows, target, c):
    vals = [(float(r["dtr_c"]), float(r[target])) for r in rows if r.get(target, "") != ""]
    if len(vals) < 20:
        return None
    n_lo = sum(x <= c for x, _ in vals)
    n_hi = sum(x > c for x, _ in vals)
    if min(n_lo, n_hi) < 50:
        return None
    s00 = len(vals)
    s01 = sum(x for x, _ in vals)
    s02 = sum(max(0.0, x-c) for x, _ in vals)
    s11 = sum(x*x for x, _ in vals)
    s12 = sum(x*max(0.0, x-c) for x, _ in vals)
    s22 = sum(max(0.0, x-c)**2 for x, _ in vals)
    ty0 = sum(y for _, y in vals)
    ty1 = sum(x*y for x, y in vals)
    ty2 = sum(max(0.0, x-c)*y for x, y in vals)
    beta = solve3([[s00,s01,s02],[s01,s11,s12],[s02,s12,s22]], [ty0,ty1,ty2])
    if beta is None:
        return None
    b0,b1,b2 = beta
    sse = sum((y-(b0+b1*x+b2*max(0.0,x-c)))**2 for x,y in vals)
    return {
        "n": len(vals), "n_below": n_lo, "n_above": n_hi,
        "breakpoint_c": c, "b0": b0, "slope_below": b1,
        "slope_change": b2, "slope_above": b1+b2, "sse": sse,
    }


def fit_linear(rows, target):
    vals = [(float(r["dtr_c"]), float(r[target])) for r in rows if r.get(target, "") != ""]
    n = len(vals)
    mx = sum(x for x,_ in vals)/n
    my = sum(y for _,y in vals)/n
    den = sum((x-mx)**2 for x,_ in vals)
    b1 = sum((x-mx)*(y-my) for x,y in vals)/den
    b0 = my-b1*mx
    sse = sum((y-(b0+b1*x))**2 for x,y in vals)
    return n,b0,b1,sse


def search(rows, target):
    best = None
    for i in range(81):
        c = 10.0 + i*0.1
        res = fit_hinge(rows, target, c)
        if res is None:
            continue
        if best is None or res["sse"] < best["sse"]:
            best = res
    if best is None:
        return None
    n,b0,b1,sse_lin = fit_linear(rows,target)
    best["linear_sse"] = sse_lin
    best["sse_reduction_pct"] = 100.0*(sse_lin-best["sse"])/sse_lin
    best["aic_linear"] = n*math.log(sse_lin/n)+2*2
    best["aic_segmented"] = n*math.log(best["sse"]/n)+2*4
    best["delta_aic_segmented_minus_linear"] = best["aic_segmented"]-best["aic_linear"]
    return best


def main():
    rows=[]
    with INFILE.open("r",newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["season"]!="May-Sep":
                continue
            year=int(r["solar_date"][:4])
            r["year"]=year
            if r.get("morning_bias_c","")!="" and r.get("afternoon_bias_c","")!="":
                r["asymmetry_gap_c"]=float(r["afternoon_bias_c"])-float(r["morning_bias_c"])
            else:
                r["asymmetry_gap_c"]=""
            rows.append(r)

    out=[]
    stability=[]
    subsets=[
        ("All_2000_2024", rows),
        ("Calibration_2000_2016", [r for r in rows if r["year"]<=2016]),
        ("Validation_2017_2024", [r for r in rows if r["year"]>=2017]),
    ]
    for target,label in TARGETS:
        for subset_name,subset in subsets:
            res=search(subset,target)
            if res is None:
                continue
            rec={"target":target,"label":label,"subset":subset_name}
            rec.update({k:round(v,4) if isinstance(v,float) else v for k,v in res.items()})
            out.append(rec)
        ss=[r for r in out if r["target"]==target]
        mp={r["subset"]:r for r in ss}
        if all(k in mp for k in ["All_2000_2024","Calibration_2000_2016","Validation_2017_2024"]):
            c_all=float(mp["All_2000_2024"]["breakpoint_c"])
            c_cal=float(mp["Calibration_2000_2016"]["breakpoint_c"])
            c_val=float(mp["Validation_2017_2024"]["breakpoint_c"])
            stability.append({
                "target":target,"label":label,
                "breakpoint_all_c":c_all,
                "breakpoint_cal_c":c_cal,
                "breakpoint_val_c":c_val,
                "cal_val_abs_diff_c":round(abs(c_cal-c_val),3),
                "stable_within_2c":"YES" if abs(c_cal-c_val)<=2.0 else "NO",
                "slope_below_all":mp["All_2000_2024"]["slope_below"],
                "slope_above_all":mp["All_2000_2024"]["slope_above"],
                "sse_reduction_all_pct":mp["All_2000_2024"]["sse_reduction_pct"],
                "delta_aic_all":mp["All_2000_2024"]["delta_aic_segmented_minus_linear"],
            })

    fields=list(out[0].keys())
    with OUT.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out)
    with STAB.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(stability[0].keys())); w.writeheader(); w.writerows(stability)

    allmap={(r["target"],r["subset"]):r for r in out}
    c_gap=float(allmap[("asymmetry_gap_c","All_2000_2024")]["breakpoint_c"])
    c_rmse=float(allmap[("daily_rmse_c","All_2000_2024")]["breakpoint_c"])
    c_am=float(allmap[("morning_bias_c","All_2000_2024")]["breakpoint_c"])
    c_pm=float(allmap[("afternoon_bias_c","All_2000_2024")]["breakpoint_c"])
    consensus=(c_gap+c_rmse+c_am+c_pm)/4.0
    spread=max(c_gap,c_rmse,c_am,c_pm)-min(c_gap,c_rmse,c_am,c_pm)

    lines=["# Urumqi local DTR breakpoint diagnosis","",
           "Continuous segmented regression was fitted as `y = b0 + b1*DTR + b2*max(0,DTR-c)` over May-Sep days.","",
           f"- Morning-bias best breakpoint: **{c_am:.1f} C**",
           f"- Afternoon-bias best breakpoint: **{c_pm:.1f} C**",
           f"- AM-PM asymmetry-gap best breakpoint: **{c_gap:.1f} C**",
           f"- Daily-RMSE best breakpoint: **{c_rmse:.1f} C**",
           f"- Four-diagnostic mean breakpoint: **{consensus:.2f} C**",
           f"- Cross-diagnostic breakpoint spread: **{spread:.2f} C**","",
           "## Detailed all-period fits","",
           "| Diagnostic | Breakpoint | Slope below | Slope above | SSE reduction vs linear | Delta AIC (seg-linear) |","|---|---:|---:|---:|---:|---:|"]
    for target,label in TARGETS:
        r=allmap[(target,"All_2000_2024")]
        lines.append(f"| {label} | {float(r['breakpoint_c']):.1f} | {float(r['slope_below']):.4f} | {float(r['slope_above']):.4f} | {float(r['sse_reduction_pct']):.2f}% | {float(r['delta_aic_segmented_minus_linear']):.2f} |")
    lines += ["","## Stability rule","","A local threshold is considered promising if the calibration- and validation-period breakpoints remain within 2 C and the segmented model materially improves SSE/AIC over a single linear relation.","","This output is a diagnostic threshold estimate, not yet a physiological crop threshold and not yet a source-code switch value."]
    README.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))


if __name__=="__main__":
    main()
