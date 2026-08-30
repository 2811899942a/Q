#!/usr/bin/env python3
"""M15-V2 round 1: one-parameter post-peak power warp.

Scientific contract
-------------------
- Frozen M15-13.5 controls DTRc and sunset coefficient.
- Only modeled-Tmax -> sunset cooling progress changes: R_p = R**p.
- p=1 is exactly the frozen M15 implementation.
- p is selected using dense Diwopu 2000-2016 temperature data only.
- Validation 2017-2024 and target station 514630 are evaluated only after p freezes.
- Crop observations/results are not read by this script.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
import csv
import json
import math
import statistics

import analyze_dense_514635_shape as ds
import diagnose_dense_sunset_anchor_514635 as dense
import shihezi_dtrc_fourlevel_ablation as base

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'm15_temp_v2' / 'postpeak_power_round1'
RESULT_CP = ROOT / 'CHECKPOINT_20260830_M15_V2_ROUND1_POSTPEAK_POWER_RESULT.md'

DTRC = 13.5
ALPHA = 6.407985379809223
P_MIN = 0.50
P_MAX = 1.50
BLOCKS = [(2000, 2004), (2005, 2008), (2009, 2012), (2013, 2016)]
TARGET_BASE_RMSE = 2.796223546
TARGET_BASE_HIGH_RMSE = 4.634433256
TARGET_BASE_N = 5917
TOL_RMSE = 1e-6
TOL_POINTWISE = 1e-12


def mean(xs):
    return statistics.mean(xs) if xs else float('nan')


def metric(rows, pred_fn):
    if not rows:
        return {'n': 0, 'rmse': float('nan'), 'mae': float('nan'), 'mbe': float('nan'), 'r2': float('nan')}
    obs = [float(r['obs']) if 'obs' in r else float(r['obs_c']) for r in rows]
    pred = [pred_fn(r) for r in rows]
    err = [p - o for o, p in zip(obs, pred)]
    rm = math.sqrt(mean([e * e for e in err]))
    ma = mean([abs(e) for e in err])
    mb = mean(err)
    mo, mp = mean(obs), mean(pred)
    so = sum((x - mo) ** 2 for x in obs)
    sp = sum((x - mp) ** 2 for x in pred)
    if so > 0 and sp > 0:
        rr = sum((o - mo) * (p - mp) for o, p in zip(obs, pred)) / math.sqrt(so * sp)
        r2 = rr * rr
    else:
        r2 = float('nan')
    return {'n': len(rows), 'rmse': rm, 'mae': ma, 'mbe': mb, 'r2': r2}


def write_csv(path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def m15_power(h, tx, tn, dl, su, sd, cl, p):
    """Frozen M15-13.5 with only post-peak normalized progress warped by p."""
    # Hard nesting: this delegates p=1 to the audited frozen implementation.
    if abs(p - 1.0) <= 1e-15:
        return base.m15(h, tx, tn, dl, su, sd, cl, DTRC, ALPHA)

    p0 = base.pl(h, tx, tn, dl, su, sd)
    dtr = tx - tn
    if dtr <= DTRC or cl <= 0:
        return p0, 0.0, False

    mn, mx, ts0, _ti0, hd = base.parts(tx, tn, dl, su, sd)
    delta = ALPHA * (dtr - DTRC) * cl
    ts1 = max(tn, ts0 - delta)
    capped = (ts0 - delta) < tn

    if mx < h <= sd:
        den = tx - ts0
        if den <= 1e-12:
            return p0, ts0 - ts1, capped
        r = min(max((tx - p0) / den, 0.0), 1.0)
        rp = r ** p
        return tx - (tx - ts1) * rp, ts0 - ts1, capped

    if h > sd or h < mn:
        eb = math.exp(-base.B)
        ti1 = (tn - ts1 * eb) / (1.0 - eb)
        tt = 24.0 + h - sd if h < mn else h - sd
        return ti1 + (ts1 - ti1) * math.exp(-base.B * tt / hd), ts0 - ts1, capped

    return p0, ts0 - ts1, capped


def load_dense_rows():
    """Rebuild dense Diwopu rows from the already-audited loaders."""
    srad = dense.load_srad()
    byday = dense.load_dense()
    rows = []
    for date, vals in sorted(byday.items()):
        key = date.isoformat()
        if key not in srad or not (5 <= date.month <= 9):
            continue
        vals = sorted(vals)
        if len({v[0].hour for v in vals}) < 20:
            continue
        temps = [float(v[1]) for v in vals]
        tx, tn = max(temps), min(temps)
        dtr = tx - tn
        dl, su, sd = ds.daylen(date.timetuple().tm_yday)
        cl, _sclear = dense.clouds(date, srad[key])
        mx = su + base.C + dl / 2.0 + base.A
        for sol, obs in vals:
            h = sol.hour + sol.minute / 60.0 + sol.second / 3600.0
            rows.append({
                'date': key,
                'year': date.year,
                'month': date.month,
                'hour': h,
                'obs': float(obs),
                'tmax': tx,
                'tmin': tn,
                'dtr': dtr,
                'dayl': dl,
                'snup': su,
                'sndn': sd,
                'clouds': cl,
                'tmax_model_h': mx,
            })
    return rows


def dense_pred(r, p):
    return m15_power(r['hour'], r['tmax'], r['tmin'], r['dayl'], r['snup'], r['sndn'], r['clouds'], p)[0]


def dense_active_postpeak(r):
    return r['dtr'] > DTRC and r['clouds'] > 0 and r['tmax_model_h'] < r['hour'] <= r['sndn']


def target_pred(r, p):
    return m15_power(
        float(r['solar_hour']), float(r['tmax_ghcn_c']), float(r['tmin_ghcn_c']),
        r['dayl'], r['snup'], r['sndn'], r['clouds'], p
    )[0]


def score_p(cal_post, p, baseline_blocks=None):
    block_scores = []
    for y0, y1 in BLOCKS:
        q = [r for r in cal_post if y0 <= r['year'] <= y1]
        m = metric(q, lambda r, pp=p: dense_pred(r, pp))
        block_scores.append(m['rmse'])
    allm = metric(cal_post, lambda r, pp=p: dense_pred(r, pp))
    wins = ''
    if baseline_blocks is not None:
        wins = sum(a < b - 1e-12 for a, b in zip(block_scores, baseline_blocks))
    return {
        'p': p,
        'objective_mean_block_rmse': mean(block_scores),
        'cal_active_postpeak_rmse': allm['rmse'],
        'block_2000_2004_rmse': block_scores[0],
        'block_2005_2008_rmse': block_scores[1],
        'block_2009_2012_rmse': block_scores[2],
        'block_2013_2016_rmse': block_scores[3],
        'blocks_better_than_p1': wins,
    }


def physical_qa(target_val, p):
    meta = {}
    for r in target_val:
        meta.setdefault(r['solar_date'], r)
    active = bad = caps = 0
    max_above = max_below = max_postpeak_inc = 0.0
    for r in meta.values():
        tx = float(r['tmax_ghcn_c']); tn = float(r['tmin_ghcn_c'])
        if tx - tn <= DTRC or r['clouds'] <= 0:
            continue
        active += 1
        vals = []
        cap = False
        for i in range(481):
            h = i * 0.05
            pred, _d, cp = m15_power(h, tx, tn, r['dayl'], r['snup'], r['sndn'], r['clouds'], p)
            vals.append((h, pred)); cap = cap or cp
        mn = r['snup'] + base.C
        mx = mn + r['dayl'] / 2.0 + base.A
        rise = [z for z in vals if mn <= z[0] <= mx]
        aft = [z for z in vals if mx <= z[0] <= 24]
        pre = [z for z in vals if 0 <= z[0] <= mn]
        rd = [rise[i+1][1] - rise[i][1] for i in range(len(rise)-1)]
        ad = [aft[i+1][1] - aft[i][1] for i in range(len(aft)-1)]
        pd = [pre[i+1][1] - pre[i][1] for i in range(len(pre)-1)]
        above = max(0.0, max(v for _, v in vals) - tx)
        below = max(0.0, tn - min(v for _, v in vals))
        post_inc = max(ad) if ad else 0.0
        viol = ((rd and min(rd) < -1e-8) or (ad and max(ad) > 1e-8) or
                (pd and max(pd) > 1e-8) or above > 1e-6 or below > 1e-6)
        bad += int(bool(viol)); caps += int(cap)
        max_above = max(max_above, above); max_below = max(max_below, below)
        max_postpeak_inc = max(max_postpeak_inc, post_inc)
    return {
        'p': p, 'active_days': active, 'shape_violations': bad, 'ts_caps': caps,
        'max_above_tmax_c': max_above, 'max_below_tmin_c': max_below,
        'max_postpeak_increment_0p05h_c': max_postpeak_inc,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # ----------------------- CALIBRATION ONLY -----------------------
    # Loading can contain all years, but no post-2016 score is computed until p is frozen.
    dense_rows = load_dense_rows()
    dense_cal = [r for r in dense_rows if r['year'] <= 2016]
    cal_post = [r for r in dense_cal if dense_active_postpeak(r)]
    if not cal_post:
        raise RuntimeError('No dense calibration active post-peak observations found.')

    p1 = score_p(cal_post, 1.0)
    baseline_blocks = [p1[k] for k in (
        'block_2000_2004_rmse', 'block_2005_2008_rmse',
        'block_2009_2012_rmse', 'block_2013_2016_rmse')]

    coarse = []
    for i in range(int(round((P_MAX - P_MIN) / 0.05)) + 1):
        p = round(P_MIN + i * 0.05, 10)
        coarse.append(score_p(cal_post, p, baseline_blocks))
    coarse_best = min(coarse, key=lambda r: (r['objective_mean_block_rmse'], abs(r['p'] - 1.0)))

    fine_lo = max(P_MIN, coarse_best['p'] - 0.05)
    fine_hi = min(P_MAX, coarse_best['p'] + 0.05)
    fine_ps = {1.0}
    n_fine = int(round((fine_hi - fine_lo) / 0.005))
    for i in range(n_fine + 1):
        fine_ps.add(round(fine_lo + i * 0.005, 10))
    fine = [score_p(cal_post, p, baseline_blocks) for p in sorted(fine_ps)]

    eligible = [r for r in fine if abs(r['p'] - 1.0) > 1e-12 and
                int(r['blocks_better_than_p1']) >= 3 and
                r['cal_active_postpeak_rmse'] < p1['cal_active_postpeak_rmse'] - 1e-12]
    if eligible:
        chosen = min(eligible, key=lambda r: (r['objective_mean_block_rmse'], r['cal_active_postpeak_rmse'], abs(r['p'] - 1.0)))
        p_frozen = float(chosen['p'])
        calibration_status = 'NONUNIT_PARAMETER_FROZEN'
    else:
        chosen = p1
        p_frozen = 1.0
        calibration_status = 'CALIBRATION_UNSTABLE_FREEZE_P1'

    write_csv(OUT / 'coarse_grid.csv', coarse)
    write_csv(OUT / 'fine_grid.csv', fine)

    # From this line onward p_frozen is immutable. Validation cannot influence selection.
    frozen_selection = {
        'DTRc_C': DTRC, 'alpha': ALPHA, 'p_frozen': p_frozen,
        'calibration_status': calibration_status,
        'selection_objective': 'mean contiguous-block active-postpeak RMSE on Diwopu 2000-2016',
        'calibration_active_postpeak_n': len(cal_post),
        'calibration_p1_objective': p1['objective_mean_block_rmse'],
        'calibration_chosen_objective': chosen['objective_mean_block_rmse'],
        'calibration_blocks_better_than_p1': int(chosen['blocks_better_than_p1']) if chosen['blocks_better_than_p1'] != '' else 0,
    }
    (OUT / 'frozen_selection.json').write_text(json.dumps(frozen_selection, indent=2), encoding='utf-8')

    # ----------------------- INDEPENDENT VALIDATION -----------------------
    dense_val = [r for r in dense_rows if r['year'] >= 2017]
    dense_val_post = [r for r in dense_val if dense_active_postpeak(r)]
    dense_metrics = []
    for name, p in [('P1_FROZEN_M15', 1.0), ('P_FROZEN_V2', p_frozen)]:
        for scope, q in [
            ('May-Sep', dense_val),
            ('ActivePostpeak', dense_val_post),
            ('DTR>=15', [r for r in dense_val if r['dtr'] >= 15.0]),
        ]:
            z = metric(q, lambda r, pp=p: dense_pred(r, pp))
            dense_metrics.append({'model': name, 'p': p, 'scope': scope, **z})
    write_csv(OUT / 'dense_validation_metrics.csv', dense_metrics)

    target_rows = base.load_target_rows()
    target_val = [r for r in target_rows if r['year'] >= 2017]

    # Hard baseline identity checks before candidate evaluation.
    max_diff = 0.0
    for r in target_val:
        args = (float(r['solar_hour']), float(r['tmax_ghcn_c']), float(r['tmin_ghcn_c']),
                r['dayl'], r['snup'], r['sndn'], r['clouds'])
        a = m15_power(*args, 1.0)[0]
        b = base.m15(*args, DTRC, ALPHA)[0]
        max_diff = max(max_diff, abs(a - b))
    b_all = metric(target_val, lambda r: target_pred(r, 1.0))
    target_high = [r for r in target_val if float(r['formal_dtr_c']) >= 15.0]
    b_hi = metric(target_high, lambda r: target_pred(r, 1.0))
    if max_diff > TOL_POINTWISE:
        raise RuntimeError(f'p=1 pointwise mismatch: max_abs_diff={max_diff}')
    if b_all['n'] != TARGET_BASE_N or abs(b_all['rmse'] - TARGET_BASE_RMSE) > TOL_RMSE:
        raise RuntimeError(f'Frozen May-Sep baseline drift: n={b_all["n"]}, rmse={b_all["rmse"]}')
    if abs(b_hi['rmse'] - TARGET_BASE_HIGH_RMSE) > TOL_RMSE:
        raise RuntimeError(f'Frozen DTR>=15 baseline drift: rmse={b_hi["rmse"]}')

    target_metrics = []
    for name, p in [('P1_FROZEN_M15', 1.0), ('P_FROZEN_V2', p_frozen)]:
        for scope, q in [('May-Sep', target_val), ('DTR>=15', target_high)]:
            z = metric(q, lambda r, pp=p: target_pred(r, pp))
            target_metrics.append({'model': name, 'p': p, 'scope': scope, **z})
    write_csv(OUT / 'target_validation_metrics.csv', target_metrics)

    yearly = []
    worse_years = 0
    valid_years = []
    for year in sorted({r['year'] for r in target_val}):
        q = [r for r in target_val if r['year'] == year]
        if not q:
            continue
        valid_years.append(year)
        mb = metric(q, lambda r: target_pred(r, 1.0))
        mc = metric(q, lambda r: target_pred(r, p_frozen))
        if mc['rmse'] > mb['rmse'] + 1e-12:
            worse_years += 1
        yearly.extend([
            {'year': year, 'model': 'P1_FROZEN_M15', 'p': 1.0, **mb},
            {'year': year, 'model': 'P_FROZEN_V2', 'p': p_frozen, **mc},
        ])
    write_csv(OUT / 'target_year_by_year.csv', yearly)

    qa = physical_qa(target_val, p_frozen)
    write_csv(OUT / 'physical_qa_summary.csv', [qa])

    def get(rows, model, scope):
        return next(r for r in rows if r['model'] == model and r['scope'] == scope)
    d0 = get(dense_metrics, 'P1_FROZEN_M15', 'ActivePostpeak')
    d1 = get(dense_metrics, 'P_FROZEN_V2', 'ActivePostpeak')
    t0 = get(target_metrics, 'P1_FROZEN_M15', 'May-Sep')
    t1 = get(target_metrics, 'P_FROZEN_V2', 'May-Sep')
    h0 = get(target_metrics, 'P1_FROZEN_M15', 'DTR>=15')
    h1 = get(target_metrics, 'P_FROZEN_V2', 'DTR>=15')
    target_gain = t0['rmse'] - t1['rmse']

    keep = (
        abs(p_frozen - 1.0) > 1e-12 and
        d1['rmse'] <= d0['rmse'] + 1e-12 and
        target_gain >= 0.03 - 1e-12 and
        h1['rmse'] <= h0['rmse'] + 0.01 + 1e-12 and
        qa['shape_violations'] == 0 and
        worse_years <= 2
    )
    decision = 'KEEP_FOR_DSSAT_CROP_PROPAGATION' if keep else 'DROP_POSTPEAK_POWER'

    manifest = {
        **frozen_selection,
        'baseline_pointwise_max_abs_diff_C': max_diff,
        'baseline_target_n': b_all['n'],
        'baseline_target_rmse_C': b_all['rmse'],
        'baseline_target_highDTR_rmse_C': b_hi['rmse'],
        'dense_validation_active_postpeak_rmse_p1_C': d0['rmse'],
        'dense_validation_active_postpeak_rmse_candidate_C': d1['rmse'],
        'target_validation_rmse_p1_C': t0['rmse'],
        'target_validation_rmse_candidate_C': t1['rmse'],
        'target_validation_rmse_gain_C': target_gain,
        'target_highDTR_rmse_p1_C': h0['rmse'],
        'target_highDTR_rmse_candidate_C': h1['rmse'],
        'target_valid_years': valid_years,
        'target_years_worse_than_p1': worse_years,
        'physical_shape_violations': qa['shape_violations'],
        'ts_caps': qa['ts_caps'],
        'decision': decision,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    text = f'''# M15-V2 Round 1 result — post-peak power warp

## Frozen parameter selection

- DTRc: **{DTRC:.1f} C**.
- Frozen M15 alpha: **{ALPHA:.12f}**.
- Selected post-peak exponent: **p = {p_frozen:.3f}**.
- Calibration status: **{calibration_status}**.
- Calibration active post-peak observations: **{len(cal_post)}**.
- p=1 mean four-block RMSE: **{p1['objective_mean_block_rmse']:.6f} C**.
- selected-p mean four-block RMSE: **{chosen['objective_mean_block_rmse']:.6f} C**.
- Calibration blocks improved versus p=1: **{int(chosen['blocks_better_than_p1']) if chosen['blocks_better_than_p1'] != '' else 0}/4**.

Parameter selection used only Diwopu 2000-2016 temperature observations. The parameter was frozen before any 2017-2024 validation metric below was computed.

## Hard baseline reproduction

- p=1 maximum pointwise difference versus audited M15: **{max_diff:.3e} C**.
- Target May-Sep: **n={b_all['n']}**, RMSE **{b_all['rmse']:.9f} C** (frozen reference {TARGET_BASE_RMSE:.9f}).
- Target DTR>=15 RMSE: **{b_hi['rmse']:.9f} C** (frozen reference {TARGET_BASE_HIGH_RMSE:.9f}).
- Baseline consistency: **PASS**.

## Independent dense-station validation, 2017-2024

|Model|p|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
'''
    for r in dense_metrics:
        text += f"|{r['model']}|{r['p']:.3f}|{r['scope']}|{r['n']}|{r['rmse']:.4f}|{r['mae']:.4f}|{r['mbe']:+.4f}|{r['r2']:.4f}|\n"
    text += '''
## Independent target-station validation, 2017-2024

|Model|p|Scope|n|RMSE|MAE|Bias|R2|
|---|---:|---|---:|---:|---:|---:|---:|
'''
    for r in target_metrics:
        text += f"|{r['model']}|{r['p']:.3f}|{r['scope']}|{r['n']}|{r['rmse']:.4f}|{r['mae']:.4f}|{r['mbe']:+.4f}|{r['r2']:.4f}|\n"
    text += f'''
- Target May-Sep RMSE gain versus frozen M15-13.5: **{target_gain:+.4f} C**.
- Target years with worse May-Sep RMSE than p=1: **{worse_years}/{len(valid_years)}**.

## Physical QA

- Active target-validation days: **{qa['active_days']}**.
- Shape violations: **{qa['shape_violations']}**.
- TS caps: **{qa['ts_caps']}**.
- Maximum above Tmax: **{qa['max_above_tmax_c']:.3e} C**.
- Maximum below Tmin: **{qa['max_below_tmin_c']:.3e} C**.

## Prespecified decision

**{decision}**

KEEP requires: non-unit stable calibration; dense active-postpeak validation no worse; target May-Sep gain >=0.03 C; target DTR>=15 degradation <=0.01 C; zero physical violations; <=2 target years worse than p=1.

If decision is `DROP_POSTPEAK_POWER`, the next mechanism is the separately prespecified bounded nighttime-decay refinement. Crop results cannot rescue this round if the temperature gate fails.
'''
    (OUT / 'README_M15_V2_POSTPEAK_POWER_ROUND1.md').write_text(text, encoding='utf-8')
    RESULT_CP.write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
