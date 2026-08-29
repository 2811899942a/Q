#!/usr/bin/env python3
"""Test a local DTR-triggered post-peak cooling-pulse modification for Urumqi.

Motivation from local residuals:
- DTR breakpoint ~14.5 C.
- Main nonlinear error growth occurs in the afternoon.
- The previous phase-compression model reduced warm bias but also altered sunset
  temperature and propagated changes into nighttime, degrading some night hours.

New one-parameter structure:
  T_new = T_PL - lambda * max(0, DTR-DTRc) * sin(pi*q)
  q = (t - t_peak) / (sunset - t_peak)

Only active for t_peak < t < sunset and DTR>DTRc.
Therefore correction is exactly zero at the PL peak and at sunset; the original
nighttime branch is preserved exactly. This is a hypothesis test, not a final formula.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
import test_dtr_phase_compression_51463 as base

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463'
GRID=DATA/'dtr_cooling_pulse_grid.csv'
METRICS=DATA/'dtr_cooling_pulse_validation.csv'
BY_DTR=DATA/'dtr_cooling_pulse_by_dtr.csv'
BY_HOUR=DATA/'dtr_cooling_pulse_by_hour.csv'
README=DATA/'README_DTR_COOLING_PULSE.md'
DTR_C=14.5


def load_rows():
    rows=[]
    with base.INFILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            year=int(r['solar_date'][:4]); month=int(r['month'])
            if not 5<=month<=9: continue
            rows.append({'date':r['solar_date'],'year':year,'month':month,
                'hs':float(r['solar_hour']),'obs':float(r['obs_c']),
                'tmax':float(r['tmax_ghcn_c']),'tmin':float(r['tmin_ghcn_c']),
                'dtr':float(r['formal_dtr_c']),'dayl':float(r['dayl_h']),
                'snup':float(r['snup_solar_h']),'sndn':float(r['sndn_solar_h']),
                'hour_bin':int(float(r['solar_hour']))%24})
    return rows


def original(r):
    A,B,C=base.OFFICIAL
    return base.htemp(r['hs'],r['tmax'],r['tmin'],r['dayl'],r['snup'],r['sndn'],A,B,C,0.0)


def pl_xj(r):
    A,B,C=base.PL_XJ_BAL
    return base.htemp(r['hs'],r['tmax'],r['tmin'],r['dayl'],r['snup'],r['sndn'],A,B,C,0.0)


def phase_compression(r):
    A,B,C=base.OFFICIAL
    return base.htemp(r['hs'],r['tmax'],r['tmin'],r['dayl'],r['snup'],r['sndn'],A,B,C,0.280)


def cooling_pulse(r,lam):
    tpl=original(r)
    excess=max(0.0,r['dtr']-DTR_C)
    if excess<=0: return tpl
    A,B,C=base.OFFICIAL
    tmin_time=r['snup']+C
    tpeak=tmin_time+r['dayl']/2.0+A
    if not (tpeak < r['hs'] < r['sndn']): return tpl
    den=r['sndn']-tpeak
    if den<=0: return tpl
    q=(r['hs']-tpeak)/den
    shape=math.sin(math.pi*q)
    pred=tpl-lam*excess*shape
    return max(r['tmin'],pred)


def write(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)


def main():
    rows=load_rows(); cal=[r for r in rows if r['year']<=2016]; val=[r for r in rows if r['year']>=2017]
    high_cal=[r for r in cal if r['dtr']>=DTR_C]
    grid=[];best=None
    for i in range(401):
        lam=i*0.005
        fn=lambda r,L=lam: cooling_pulse(r,L)
        ma=base.metric(cal,fn);mh=base.metric(high_cal,fn)
        obj=.5*ma['rmse']+.5*mh['rmse']
        rec={'lambda':lam,'cal_all_rmse':ma['rmse'],'cal_high_rmse':mh['rmse'],'objective':obj}
        grid.append(rec)
        if best is None or obj<best['objective']:best=rec
    lam=best['lambda']; boundary=lam in {grid[0]['lambda'],grid[-1]['lambda']}

    models=[('M0_DSSAT_OFFICIAL',original),('M1_PL_XJ_BAL',pl_xj),('M2_PHASE_COMPRESSION',phase_compression),('M3_COOLING_PULSE',lambda r:cooling_pulse(r,lam))]
    metrics=[]
    for split,subset in [('Calibration_2000_2016',cal),('Validation_2017_2024',val)]:
        for scope,s in [('May-Sep',subset),('DTR>=14.5',[r for r in subset if r['dtr']>=14.5]),('DTR>=15',[r for r in subset if r['dtr']>=15])]:
            for name,fn in models:
                m=base.metric(s,fn);metrics.append({'split':split,'scope':scope,'model':name,'lambda':lam if name=='M3_COOLING_PULSE' else 0.0,**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})
    bd=[]
    for b in ['<10','10-<15','15-<18','18-<20','>=20']:
        s=[r for r in val if base.dtr_bin(r['dtr'])==b]
        for name,fn in models:
            m=base.metric(s,fn);bd.append({'dtr_bin':b,'model':name,**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})
    bh=[]
    for h in range(24):
        s=[r for r in val if r['hour_bin']==h]
        if not s:continue
        for name,fn in models:
            m=base.metric(s,fn);bh.append({'solar_hour':h,'model':name,**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})
    write(GRID,[{k:round(v,6) if isinstance(v,float) else v for k,v in x.items()} for x in grid]);write(METRICS,metrics);write(BY_DTR,bd);write(BY_HOUR,bh)

    mp={(r['split'],r['scope'],r['model']):r for r in metrics}
    names=['M0_DSSAT_OFFICIAL','M1_PL_XJ_BAL','M2_PHASE_COMPRESSION','M3_COOLING_PULSE']
    lines=['# Urumqi DTR-triggered afternoon cooling pulse','',f'- Fixed DTR trigger: **{DTR_C:.1f} C**.',f'- Calibrated lambda: **{lam:.3f}**.','- Search range lambda 0.000-2.000, step 0.005.',f"- Optimum at boundary: **{'YES' if boundary else 'NO'}**.",'','## Independent validation','', '| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |','|---|---:|---:|---:|---:|---:|']
    for name in names:
        a=mp[('Validation_2017_2024','May-Sep',name)];h=mp[('Validation_2017_2024','DTR>=15',name)]
        lines.append(f"| {name} | {a['rmse']:.4f} | {h['rmse']:.4f} | {h['mae']:.4f} | {h['mbe']:.4f} | {h['r2']:.4f} |")
    m0=mp[('Validation_2017_2024','DTR>=15','M0_DSSAT_OFFICIAL')];m3=mp[('Validation_2017_2024','DTR>=15','M3_COOLING_PULSE')]
    imp=100*(m0['rmse']-m3['rmse'])/m0['rmse']
    aft=[r for r in val if 14<=r['hour_bin']<=18]
    a0=base.metric(aft,original);a3=base.metric(aft,lambda r:cooling_pulse(r,lam))
    night=[r for r in val if r['hour_bin']>=20 or r['hour_bin']<=5]
    n0=base.metric(night,original);n3=base.metric(night,lambda r:cooling_pulse(r,lam))
    lines += ['',f'- DTR>=15 RMSE improvement vs official: **{imp:.2f}%**.',f'- Afternoon 14-18 RMSE/Bias: official **{a0["rmse"]:.4f}/{a0["mbe"]:.4f} C**, M3 **{a3["rmse"]:.4f}/{a3["mbe"]:.4f} C**.',f'- Night (20-05) RMSE: official **{n0["rmse"]:.4f} C**, M3 **{n3["rmse"]:.4f} C**. These should be identical by construction.','','## Interpretation','M3 is a stronger local-mechanism candidate than phase compression only if it improves high-DTR afternoon errors while leaving night and low-DTR predictions unchanged.']
    README.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))

if __name__=='__main__':main()
