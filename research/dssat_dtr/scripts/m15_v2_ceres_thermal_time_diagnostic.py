#!/usr/bin/env python3
"""Diagnose how frozen hourly-temperature variants propagate into CERES-Maize DTT.

This script does not read yield/crop-observation data and does not fit parameters.
It reproduces the exact MZ_PHENOL temperature branch and HMET H=1..24 timing.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import csv
import json
import math
import sys

import shihezi_dtrc_fourlevel_ablation as base

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'm15_temp_v2' / 'ceres_thermal_time_diagnostic'
RESULT_CP = ROOT / 'CHECKPOINT_20260830_M15_V2_CERES_THERMAL_TIME_DIAGNOSTIC_RESULT.md'
WEATHER = ROOT / 'data' / 'shihezi_real_case' / 'power_daily' / 'shihezi_power_2019_2020_wth_inputs.csv'

DSSAT_OS_COMMIT = '0b91373806786b600d89ccfcfff78fa2f82cb26b'
DTRC_13P5 = 13.5
DTRC_13P8 = 13.8
ALPHA_13P5 = 6.407985379809223
ALPHA_13P8 = 6.749813473189908
B_OFFICIAL = 2.2
B_ROUND3 = 1.05
P_ROUND1 = 0.5

ARMS = ['H0TT', 'M15_13P5', 'M15_13P8', 'R1_P05', 'R3_P05_B105']
PAIRS = [
    ('R1_P05', 'M15_13P5', 'R1_minus_M15_13P5'),
    ('R3_P05_B105', 'R1_P05', 'R3_minus_R1'),
    ('M15_13P8', 'M15_13P5', 'M15_13P8_minus_13P5'),
]
FULL_WINDOWS = {
    2019: (date(2019, 5, 3), date(2019, 10, 25)),
    2020: (date(2020, 5, 5), date(2020, 10, 25)),
}


def mean(xs):
    return sum(xs) / len(xs) if xs else float('nan')


def write_csv(path: Path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def parse_ib0001_ecotype(os_root: Path):
    eco = os_root / 'Data' / 'Genotype' / 'MZCER048.ECO'
    if not eco.exists():
        raise FileNotFoundError(f'Missing locked ecotype file: {eco}')
    row = None
    for raw in eco.read_text(encoding='latin-1').splitlines():
        if raw.startswith('IB0001 '):
            row = raw
            break
    if row is None:
        raise RuntimeError('IB0001 not found in MZCER048.ECO')
    toks = row.split()
    nums = [float(x) for x in toks[-11:]]
    tbase, topt, ropt = nums[:3]
    if (tbase, topt, ropt) != (8.0, 34.0, 34.0):
        raise RuntimeError(f'Unexpected IB0001 thermal parameters: {(tbase,topt,ropt)}')
    return {
        'source_commit': DSSAT_OS_COMMIT,
        'ecotype_file': 'Data/Genotype/MZCER048.ECO',
        'ecotype': 'IB0001',
        'raw_row': row,
        'TBASE_C': tbase,
        'TOPT_C': topt,
        'ROPT_C': ropt,
    }


def parts_b(tx, tn, dl, su, sd, b):
    mn = su + base.C
    mx = mn + dl / 2.0 + base.A
    theta = 0.5 * base.PI * (sd - mn) / (mx - mn)
    ts = tn + (tx - tn) * math.sin(theta)
    eb = math.exp(-b)
    ti = (tn - ts * eb) / (1.0 - eb)
    hd = 24.0 + base.C - dl
    return mn, mx, ts, ti, hd


def official_pl(h, tx, tn, dl, su, sd):
    return base.pl(h, tx, tn, dl, su, sd)


def m15_general(h, tx, tn, dl, su, sd, cl, dtrc, alpha, p=1.0, bnight=2.2):
    """M15 with explicit p and active-regime Bnight; pre-peak stays official."""
    p0 = official_pl(h, tx, tn, dl, su, sd)
    dtr = tx - tn
    if dtr <= dtrc or cl <= 0:
        return p0, False, False

    # Sunset anchor must use official Parton-Logan B=2.2 through base.parts.
    mn, mx, ts0, _ti0, hd = base.parts(tx, tn, dl, su, sd)
    delta = alpha * (dtr - dtrc) * cl
    ts1 = max(tn, ts0 - delta)
    capped = (ts0 - delta) < tn

    if mx < h <= sd:
        den = tx - ts0
        if den <= 1e-12:
            return p0, True, capped
        r = min(max((tx - p0) / den, 0.0), 1.0)
        rp = r ** p
        return tx - (tx - ts1) * rp, True, capped

    if h > sd or h < mn:
        eb = math.exp(-bnight)
        ti1 = (tn - ts1 * eb) / (1.0 - eb)
        tt = 24.0 + h - sd if h < mn else h - sd
        return ti1 + (ts1 - ti1) * math.exp(-bnight * tt / hd), True, capped

    return p0, True, capped


def hourly_arm(arm, tx, tn, dl, su, sd, cl):
    vals = []
    active = False
    capped = False
    for h in range(1, 25):  # HMET: TS=24, HS=REAL(H)*24/TS => 1,...,24
        if arm == 'H0TT':
            v = official_pl(float(h), tx, tn, dl, su, sd)
            a = c = False
        elif arm == 'M15_13P5':
            v, a, c = m15_general(float(h), tx, tn, dl, su, sd, cl, DTRC_13P5, ALPHA_13P5, 1.0, B_OFFICIAL)
        elif arm == 'M15_13P8':
            v, a, c = m15_general(float(h), tx, tn, dl, su, sd, cl, DTRC_13P8, ALPHA_13P8, 1.0, B_OFFICIAL)
        elif arm == 'R1_P05':
            v, a, c = m15_general(float(h), tx, tn, dl, su, sd, cl, DTRC_13P5, ALPHA_13P5, P_ROUND1, B_OFFICIAL)
        elif arm == 'R3_P05_B105':
            v, a, c = m15_general(float(h), tx, tn, dl, su, sd, cl, DTRC_13P5, ALPHA_13P5, P_ROUND1, B_ROUND3)
        else:
            raise KeyError(arm)
        vals.append(v)
        active = active or a
        capped = capped or c
    return vals, active, capped


def ceres_dtt(tx, tn, hourly, tbase, dopt):
    """Exact MZ_PHENOL thermal branch after TH=TGRO(I) patch."""
    if tx < tbase:
        branch = 'TMAX_LT_TBASE'
        dtt = 0.0
    elif tn > dopt:
        branch = 'TMIN_GT_DOPT'
        dtt = dopt - tbase
    elif tn < tbase or tx > dopt:
        branch = 'TGRO_CLIPPED_24H'
        clipped = [min(max(t, tbase), dopt) for t in hourly]
        dtt = sum(t - tbase for t in clipped) / 24.0
    else:
        branch = 'DAILY_MEAN_NORMAL'
        dtt = (tx + tn) / 2.0 - tbase
    return max(dtt, 0.0), branch


def load_weather():
    rows = []
    with WEATHER.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            d = datetime.strptime(r['DATE'], '%Y-%m-%d').date()
            if d.year not in FULL_WINDOWS:
                continue
            lo, hi = FULL_WINDOWS[d.year]
            if not (lo <= d <= hi):
                continue
            factor = base.SRAD_FACTOR[d.year]
            srad_raw = float(r['SRAD_MJ_m2'])
            srad_scaled = srad_raw * factor
            dl, su, sd, cl = base.solar(d, srad_scaled)
            rows.append({
                'date': d,
                'year': d.year,
                'srad_raw': srad_raw,
                'srad_scaled': srad_scaled,
                'srad_factor': factor,
                'tmax': float(r['TMAX_C']),
                'tmin': float(r['TMIN_C']),
                'dayl': dl,
                'snup': su,
                'sndn': sd,
                'clouds': cl,
            })
    expected_min = {2019: date(2019,5,3), 2020: date(2020,5,5)}
    expected_max = {2019: date(2019,10,25), 2020: date(2020,10,25)}
    for yr in (2019, 2020):
        q = [r['date'] for r in rows if r['year'] == yr]
        if not q or min(q) != expected_min[yr] or max(q) != expected_max[yr]:
            raise RuntimeError(f'Weather window incomplete for {yr}: {min(q) if q else None} .. {max(q) if q else None}')
    return rows


def daily_table(weather, tbase, dopt):
    out = []
    for w in weather:
        tx, tn = w['tmax'], w['tmin']
        for arm in ARMS:
            hourly, active, capped = hourly_arm(arm, tx, tn, w['dayl'], w['snup'], w['sndn'], w['clouds'])
            dtt, branch = ceres_dtt(tx, tn, hourly, tbase, dopt)
            clipped = [min(max(t, tbase), dopt) for t in hourly]
            row = {
                'date': w['date'].isoformat(), 'year': w['year'], 'arm': arm,
                'TMAX_C': tx, 'TMIN_C': tn, 'DTR_C': tx-tn,
                'SRAD_raw_MJ_m2': w['srad_raw'], 'SRAD_scaled_MJ_m2': w['srad_scaled'],
                'SRAD_factor': w['srad_factor'], 'CLOUDS': w['clouds'],
                'M15_active': active, 'sunset_anchor_capped': capped,
                'CERES_branch': branch, 'CERES_DTT_Cd': dtt,
                'raw_hourly_mean_C': mean(hourly), 'clipped_hourly_mean_C': mean(clipped),
                'hours_below_TBASE': sum(t < tbase for t in hourly),
                'hours_above_DOPT': sum(t > dopt for t in hourly),
                'degree_hours_below_TBASE': sum(max(0.0, tbase-t) for t in hourly),
                'degree_hours_above_DOPT': sum(max(0.0, t-dopt) for t in hourly),
            }
            for h, t in enumerate(hourly, 1):
                row[f'TGRO_{h:02d}_C'] = t
            out.append(row)
    return out


def in_window(iso, year, window):
    d = datetime.strptime(iso, '%Y-%m-%d').date()
    if d.year != year:
        return False
    if window == 'PLANT_TO_HORIZON':
        lo, hi = FULL_WINDOWS[year]
    elif window == 'MAY_SEP':
        lo = FULL_WINDOWS[year][0]
        hi = date(year, 9, 30)
    else:
        raise KeyError(window)
    return lo <= d <= hi


def summarize_arm(daily):
    out = []
    for year in (2019, 2020):
        for window in ('PLANT_TO_HORIZON', 'MAY_SEP'):
            for arm in ARMS:
                q = [r for r in daily if r['arm']==arm and in_window(r['date'],year,window)]
                out.append({
                    'year': year, 'window': window, 'arm': arm, 'n_days': len(q),
                    'active_days': sum(bool(r['M15_active']) for r in q),
                    'extreme_DTT_days': sum(r['CERES_branch']=='TGRO_CLIPPED_24H' for r in q),
                    'normal_DTT_days': sum(r['CERES_branch']=='DAILY_MEAN_NORMAL' for r in q),
                    'cum_DTT_Cd': sum(r['CERES_DTT_Cd'] for r in q),
                    'sum_hours_below_TBASE': sum(r['hours_below_TBASE'] for r in q),
                    'sum_hours_above_DOPT': sum(r['hours_above_DOPT'] for r in q),
                    'sum_degree_hours_below_TBASE': sum(r['degree_hours_below_TBASE'] for r in q),
                    'sum_degree_hours_above_DOPT': sum(r['degree_hours_above_DOPT'] for r in q),
                })
    return out


def summarize_pairs(daily):
    idx = {(r['date'], r['arm']): r for r in daily}
    out = []
    for year in (2019, 2020):
        for window in ('PLANT_TO_HORIZON', 'MAY_SEP'):
            dates = sorted({r['date'] for r in daily if in_window(r['date'], year, window)})
            for cand, ref, label in PAIRS:
                diffs=[]; rawmean=[]; clipmean=[]; hb=[]; ha=[]; db=[]; da=[]; hourly_l1=[]
                for d in dates:
                    a=idx[(d,cand)]; b=idx[(d,ref)]
                    diffs.append(a['CERES_DTT_Cd']-b['CERES_DTT_Cd'])
                    rawmean.append(a['raw_hourly_mean_C']-b['raw_hourly_mean_C'])
                    clipmean.append(a['clipped_hourly_mean_C']-b['clipped_hourly_mean_C'])
                    hb.append(a['hours_below_TBASE']-b['hours_below_TBASE'])
                    ha.append(a['hours_above_DOPT']-b['hours_above_DOPT'])
                    db.append(a['degree_hours_below_TBASE']-b['degree_hours_below_TBASE'])
                    da.append(a['degree_hours_above_DOPT']-b['degree_hours_above_DOPT'])
                    hourly_l1.append(mean([abs(a[f'TGRO_{h:02d}_C']-b[f'TGRO_{h:02d}_C']) for h in range(1,25)]))
                out.append({
                    'year':year,'window':window,'contrast':label,'candidate':cand,'reference':ref,'n_days':len(dates),
                    'days_nonzero_DTT_delta':sum(abs(x)>1e-12 for x in diffs),
                    'cum_DTT_delta_Cd':sum(diffs),
                    'mean_daily_DTT_delta_Cd':mean(diffs),
                    'mean_abs_daily_DTT_delta_Cd':mean([abs(x) for x in diffs]),
                    'max_abs_daily_DTT_delta_Cd':max([abs(x) for x in diffs]) if diffs else 0.0,
                    'mean_abs_hourly_temperature_delta_C':mean(hourly_l1),
                    'mean_raw_hourly_mean_delta_C':mean(rawmean),
                    'mean_clipped_hourly_mean_delta_C':mean(clipmean),
                    'delta_total_hours_below_TBASE':sum(hb),
                    'delta_total_hours_above_DOPT':sum(ha),
                    'delta_degree_hours_below_TBASE':sum(db),
                    'delta_degree_hours_above_DOPT':sum(da),
                })
    return out


def source_rounding_sensitivity(weather, tbase, dopt):
    """Quantify exact scientific alpha vs 4-decimal Fortran literal used in crop builds."""
    rec=[]
    for alpha_exact, alpha_src, label, dtrc, p, bn in [
        (ALPHA_13P5, 6.4080, '13P5', 13.5, .5, 1.05),
        (ALPHA_13P8, 6.7498, '13P8', 13.8, 1.0, 2.2),
    ]:
        max_t=0.0; max_dtt=0.0
        for w in weather:
            hv1=[];hv2=[]
            for h in range(1,25):
                hv1.append(m15_general(float(h),w['tmax'],w['tmin'],w['dayl'],w['snup'],w['sndn'],w['clouds'],dtrc,alpha_exact,p,bn)[0])
                hv2.append(m15_general(float(h),w['tmax'],w['tmin'],w['dayl'],w['snup'],w['sndn'],w['clouds'],dtrc,alpha_src,p,bn)[0])
            max_t=max(max_t,max(abs(a-b) for a,b in zip(hv1,hv2)))
            d1,_=ceres_dtt(w['tmax'],w['tmin'],hv1,tbase,dopt);d2,_=ceres_dtt(w['tmax'],w['tmin'],hv2,tbase,dopt)
            max_dtt=max(max_dtt,abs(d1-d2))
        rec.append({'arm_family':label,'alpha_exact':alpha_exact,'alpha_fortran_literal':alpha_src,
                    'max_hourly_temperature_difference_C':max_t,'max_daily_DTT_difference_Cd':max_dtt})
    return rec


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: m15_v2_ceres_thermal_time_diagnostic.py /path/to/locked/dssat-csm-os')
    os_root = Path(sys.argv[1]).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    eco = parse_ib0001_ecotype(os_root)
    tbase = eco['TBASE_C']
    # TOPT==ROPT is a hard lock for IB0001; one DOPT therefore applies to both phenological phases.
    dopt = eco['TOPT_C']

    weather = load_weather()
    daily = daily_table(weather, tbase, dopt)
    arms = summarize_arm(daily)
    pairs = summarize_pairs(daily)
    rounding = source_rounding_sensitivity(weather,tbase,dopt)

    write_csv(OUT/'daily_hourly_thermal_time.csv', daily)
    write_csv(OUT/'arm_summary.csv', arms)
    write_csv(OUT/'contrast_summary.csv', pairs)
    write_csv(OUT/'alpha_rounding_sensitivity.csv', rounding)
    (OUT/'ecotype_lock.json').write_text(json.dumps(eco,indent=2),encoding='utf-8')

    def pair(year,window,label):
        return next(r for r in pairs if r['year']==year and r['window']==window and r['contrast']==label)

    # Aggregate the two crop years for mechanism-scale comparison.
    agg=[]
    for window in ('PLANT_TO_HORIZON','MAY_SEP'):
        for _cand,_ref,label in PAIRS:
            q=[r for r in pairs if r['window']==window and r['contrast']==label]
            agg.append({
                'window':window,'contrast':label,'n_days':sum(r['n_days'] for r in q),
                'days_nonzero_DTT_delta':sum(r['days_nonzero_DTT_delta'] for r in q),
                'cum_DTT_delta_Cd':sum(r['cum_DTT_delta_Cd'] for r in q),
                'mean_abs_daily_DTT_delta_Cd':sum(r['mean_abs_daily_DTT_delta_Cd']*r['n_days'] for r in q)/sum(r['n_days'] for r in q),
                'max_abs_daily_DTT_delta_Cd':max(r['max_abs_daily_DTT_delta_Cd'] for r in q),
                'mean_abs_hourly_temperature_delta_C':sum(r['mean_abs_hourly_temperature_delta_C']*r['n_days'] for r in q)/sum(r['n_days'] for r in q),
                'delta_degree_hours_below_TBASE':sum(r['delta_degree_hours_below_TBASE'] for r in q),
                'delta_degree_hours_above_DOPT':sum(r['delta_degree_hours_above_DOPT'] for r in q),
            })
    write_csv(OUT/'two_year_contrast_summary.csv',agg)

    a_r1=next(r for r in agg if r['window']=='PLANT_TO_HORIZON' and r['contrast']=='R1_minus_M15_13P5')
    a_r3=next(r for r in agg if r['window']=='PLANT_TO_HORIZON' and r['contrast']=='R3_minus_R1')
    # Diagnostic classification is descriptive, not a model-selection gate.
    if a_r3['mean_abs_daily_DTT_delta_Cd'] > a_r1['mean_abs_daily_DTT_delta_Cd'] * 2.0 and a_r3['days_nonzero_DTT_delta'] > a_r1['days_nonzero_DTT_delta']:
        mechanism = 'ROUND3_HAS_STRONGER_DIRECT_DTT_PROPAGATION'
    elif a_r3['mean_abs_daily_DTT_delta_Cd'] <= 1e-6:
        mechanism = 'DTT_PATHWAY_NEGLIGIBLE_INSPECT_OTHER_HMET_PATHS'
    else:
        mechanism = 'DTT_PATHWAY_PRESENT_BUT_NOT_SUFFICIENT_ALONE'

    manifest={
        'dssat_source_commit':DSSAT_OS_COMMIT,'ecotype':eco,
        'hours_reproduced':[1,24],'srad_scenario':'SRAD19P8_N_OFF',
        'round1_two_year_plant_horizon':a_r1,'round3_two_year_plant_horizon':a_r3,
        'alpha_rounding_sensitivity':rounding,'diagnostic_classification':mechanism,
    }
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

    text=f'''# M15-V2 CERES thermal-time sensitivity diagnostic result

## Locked CERES thermal parameters

- DSSAT source: `{DSSAT_OS_COMMIT}`.
- Ecotype: **IB0001**.
- TBASE: **{tbase:.1f} C**; TOPT: **{eco['TOPT_C']:.1f} C**; ROPT: **{eco['ROPT_C']:.1f} C**.
- TOPT=ROPT, so the Shihezi case uses one development upper clipping temperature (**34 C**) before and after anthesis.
- HMET hourly sampling is reproduced at H=1,...,24 exactly.
- Scenario: **SRAD19P8_N_OFF**.

## Two-year planting-to-horizon propagation

|Contrast|Days|Days with nonzero DTT delta|Cumulative DTT delta (C d)|Mean abs daily DTT delta|Max abs daily DTT delta|Mean abs hourly temp delta|
|---|---:|---:|---:|---:|---:|---:|
'''
    for x in [r for r in agg if r['window']=='PLANT_TO_HORIZON']:
        text+=f"|{x['contrast']}|{x['n_days']}|{x['days_nonzero_DTT_delta']}|{x['cum_DTT_delta_Cd']:+.6f}|{x['mean_abs_daily_DTT_delta_Cd']:.6f}|{x['max_abs_daily_DTT_delta_Cd']:.6f}|{x['mean_abs_hourly_temperature_delta_C']:.6f}|\n"
    text+='''
## Year-specific direct thermal-time contrasts

|Year|Contrast|nonzero DTT days|cum DTT delta|mean abs daily delta|max abs daily delta|delta degree-hours <8C|delta degree-hours >34C|
|---:|---|---:|---:|---:|---:|---:|---:|
'''
    for y in (2019,2020):
        for label in ('R1_minus_M15_13P5','R3_minus_R1','M15_13P8_minus_13P5'):
            x=pair(y,'PLANT_TO_HORIZON',label)
            text+=f"|{y}|{label}|{x['days_nonzero_DTT_delta']}|{x['cum_DTT_delta_Cd']:+.6f}|{x['mean_abs_daily_DTT_delta_Cd']:.6f}|{x['max_abs_daily_DTT_delta_Cd']:.6f}|{x['delta_degree_hours_below_TBASE']:+.3f}|{x['delta_degree_hours_above_DOPT']:+.3f}|\n"
    text+=f'''
## Mechanism classification

**{mechanism}**

- Round-1 post-peak shape: mean absolute daily DTT change **{a_r1['mean_abs_daily_DTT_delta_Cd']:.6f} C d**, cumulative two-year change **{a_r1['cum_DTT_delta_Cd']:+.6f} C d**, nonzero on **{a_r1['days_nonzero_DTT_delta']}/{a_r1['n_days']}** days.
- Round-3 nighttime-B increment: mean absolute daily DTT change **{a_r3['mean_abs_daily_DTT_delta_Cd']:.6f} C d**, cumulative two-year change **{a_r3['cum_DTT_delta_Cd']:+.6f} C d**, nonzero on **{a_r3['days_nonzero_DTT_delta']}/{a_r3['n_days']}** days.

This diagnostic does not fit parameters and does not alter the current temperature winner. Full daily 24-hour TGRO and CERES DTT values are committed in `daily_hourly_thermal_time.csv`.
'''
    (OUT/'README_CERES_THERMAL_TIME_DIAGNOSTIC.md').write_text(text,encoding='utf-8')
    RESULT_CP.write_text(text,encoding='utf-8')
    print(text)


if __name__=='__main__':
    main()
