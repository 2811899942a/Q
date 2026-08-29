#!/usr/bin/env python3
"""Test a physically monotonic Urumqi-specific post-peak time-warp for DSSAT HTEMP.

Mechanism derived from local observations:
- PL-XJ handles ordinary/regional timing better.
- Above DTRc=14.5 C, remaining error is concentrated in the early post-peak warm shoulder.
- Additive cooling improved checkpoints but failed physical monotonicity QA.

New one-parameter structure preserves the PL-XJ temperature trajectory and only
advances progress along it after the peak:

  q = (t-tpeak)/(sunset-tpeak)
  a = 1 / (1 + gamma * max(0,DTR-DTRc))
  q_eff = q**a
  t_eff = tpeak + q_eff*(sunset-tpeak)
  Tnew(t) = T_PLXJ(t_eff)

For gamma>=0, 0<a<=1, so q_eff>=q, monotonic and anchored at q=0 and q=1.
Peak and sunset temperatures are unchanged, and nighttime is exactly PL-XJ.
"""
import csv, math
from pathlib import Path
import test_dtr_phase_compression_51463 as base
import test_dtr_cooling_pulse_51463 as cp

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463';DTRC=14.5
GRID=DATA/'monotonic_warp_grid.csv';VAL=DATA/'monotonic_warp_validation.csv';BD=DATA/'monotonic_warp_by_dtr.csv';BH=DATA/'monotonic_warp_by_hour.csv';README=DATA/'README_MONOTONIC_WARP.md'

def plxj_at(r,hs):
    A,B,C=base.PL_XJ_BAL
    return base.htemp(hs,r['tmax'],r['tmin'],r['dayl'],r['snup'],r['sndn'],A,B,C,0.0)

def warp(r,gamma):
    tpl=cp.pl_xj(r);e=max(0.0,r['dtr']-DTRC)
    if e<=0 or gamma<=0:return tpl
    A,B,C=base.PL_XJ_BAL;tmin_time=r['snup']+C;tpeak=tmin_time+r['dayl']/2+A
    if not(tpeak<r['hs']<r['sndn']):return tpl
    q=(r['hs']-tpeak)/(r['sndn']-tpeak);a=1/(1+gamma*e);qeff=q**a;heff=tpeak+qeff*(r['sndn']-tpeak)
    return plxj_at(r,heff)

def write(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
def main():
    rows=cp.load_rows();cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];high=[r for r in cal if r['dtr']>=DTRC]
    grid=[];best=None
    for i in range(251):
        g=i*.002
        fn=lambda r,G=g:warp(r,G);ma=base.metric(cal,fn);mh=base.metric(high,fn);obj=.5*ma['rmse']+.5*mh['rmse'];rec={'gamma':g,'cal_all_rmse':ma['rmse'],'cal_high_rmse':mh['rmse'],'objective':obj};grid.append(rec)
        if best is None or obj<best['objective']:best=rec
    g=best['gamma'];boundary=g in {0.0,.5}
    models=[('M0_DSSAT',cp.original),('M1_PL_XJ',cp.pl_xj),('M2_MONOTONIC_WARP',lambda r:warp(r,g))]
    metrics=[]
    for split,subset in [('Calibration_2000_2016',cal),('Validation_2017_2024',val)]:
        for scope,s in [('May-Sep',subset),('DTR>=15',[r for r in subset if r['dtr']>=15])]:
            for name,fn in models:
                m=base.metric(s,fn);metrics.append({'split':split,'scope':scope,'model':name,'gamma':g if name=='M2_MONOTONIC_WARP' else '',**{x:round(v,4) if isinstance(v,float) else v for x,v in m.items()}})
    bd=[]
    for b in ['<10','10-<15','15-<18','18-<20','>=20']:
        s=[r for r in val if base.dtr_bin(r['dtr'])==b]
        for name,fn in models:
            m=base.metric(s,fn);bd.append({'dtr_bin':b,'model':name,**{x:round(v,4) if isinstance(v,float) else v for x,v in m.items()}})
    bh=[]
    for h in range(24):
        s=[r for r in val if r['hour_bin']==h]
        if not s:continue
        for name,fn in models:
            m=base.metric(s,fn);bh.append({'solar_hour':h,'model':name,**{x:round(v,4) if isinstance(v,float) else v for x,v in m.items()}})
    write(GRID,[{x:round(v,6) if isinstance(v,float) else v for x,v in r.items()} for r in grid]);write(VAL,metrics);write(BD,bd);write(BH,bh)
    # Continuous physical QA at 5-min resolution.
    days={}
    for r in rows:
        if r['dtr']>=DTRC:days.setdefault(r['date'],r)
    bad=0;max_inc=0
    for r in days.values():
        A,B,C=base.PL_XJ_BAL;tpeak=r['snup']+C+r['dayl']/2+A;h=tpeak;ts=[]
        while h<=r['sndn']+1e-9:
            rr=dict(r);rr['hs']=h;ts.append(warp(rr,g));h+=1/12
        inc=max([ts[i+1]-ts[i] for i in range(len(ts)-1)] or [0]);max_inc=max(max_inc,inc)
        if inc>0.02:bad+=1
    mp={(r['split'],r['scope'],r['model']):r for r in metrics};o=mp[('Validation_2017_2024','DTR>=15','M0_DSSAT')];b=mp[('Validation_2017_2024','DTR>=15','M1_PL_XJ')];m=mp[('Validation_2017_2024','DTR>=15','M2_MONOTONIC_WARP')];oa=mp[('Validation_2017_2024','May-Sep','M0_DSSAT')];ba=mp[('Validation_2017_2024','May-Sep','M1_PL_XJ')];ma=mp[('Validation_2017_2024','May-Sep','M2_MONOTONIC_WARP')]
    imp=100*(o['rmse']-m['rmse'])/o['rmse'];imp1=100*(b['rmse']-m['rmse'])/b['rmse'];impall=100*(oa['rmse']-ma['rmse'])/oa['rmse']
    txt=f'''# Urumqi DTR-triggered monotonic post-peak time warp

- Fixed DTRc: **14.5 C**.
- Calibrated gamma: **{g:.3f} per C**.
- Optimum at search boundary: **{'YES' if boundary else 'NO'}**.
- Formula: `q_eff = q^[1/(1+gamma*(DTR-14.5)+)]`, then evaluate the original PL-XJ post-peak curve at the advanced effective time.
- Peak, sunset and nighttime values are preserved exactly.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| Official | {oa['rmse']:.4f} | {o['rmse']:.4f} | {o['mae']:.4f} | {o['mbe']:.4f} | {o['r2']:.4f} |
| PL-XJ | {ba['rmse']:.4f} | {b['rmse']:.4f} | {b['mae']:.4f} | {b['mbe']:.4f} | {b['r2']:.4f} |
| PL-XJ + monotonic warp | {ma['rmse']:.4f} | {m['rmse']:.4f} | {m['mae']:.4f} | {m['mbe']:.4f} | {m['r2']:.4f} |

- May-Sep improvement vs official: **{impall:.2f}%**.
- DTR>=15 improvement vs official: **{imp:.2f}%**.
- Additional DTR>=15 improvement beyond PL-XJ: **{imp1:.2f}%**.

## Physical QA
- High-DTR May-Sep days checked at 5-min resolution: **{len(days)}**.
- Days with >0.02 C post-peak increase before sunset: **{bad}**.
- Maximum detected 5-min increase: **{max_inc:.4f} C**.

This candidate is source-code eligible only if the physical-QA count is zero (or numerical noise only) and independent validation retains a meaningful gain over PL-XJ.
''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
