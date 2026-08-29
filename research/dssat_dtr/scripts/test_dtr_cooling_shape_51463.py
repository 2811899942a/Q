#!/usr/bin/env python3
"""Test a two-parameter Urumqi-specific post-peak cooling shape.

The one-parameter cooling pulse established that localizing correction between the
PL peak and sunset preserves night behavior, but amplitude-only calibration overfits.
This test adds only one shape parameter p:

  T_new = T_PL - lambda * max(0,DTR-14.5) * sin(pi*q)^p
  q = (t-t_peak)/(sunset-t_peak), 0<q<1

lambda controls magnitude; p controls where the cooling anomaly is concentrated.
p<1 broadens correction toward the shoulders (including later afternoon), while
p>1 concentrates it near the midpoint. Peak and sunset remain exact anchors and
nighttime remains unchanged.
"""
from __future__ import annotations
import csv, math
from pathlib import Path
import test_dtr_phase_compression_51463 as base
import test_dtr_cooling_pulse_51463 as cp

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463'
GRID=DATA/'dtr_cooling_shape_grid.csv'; VAL=DATA/'dtr_cooling_shape_validation.csv'
BD=DATA/'dtr_cooling_shape_by_dtr.csv'; BH=DATA/'dtr_cooling_shape_by_hour.csv'
README=DATA/'README_DTR_COOLING_SHAPE.md'; DTR_C=14.5


def shaped(r,lam,p):
    tpl=cp.original(r); excess=max(0.0,r['dtr']-DTR_C)
    if excess<=0:return tpl
    A,B,C=base.OFFICIAL; tmin_time=r['snup']+C; tpeak=tmin_time+r['dayl']/2.0+A
    if not(tpeak<r['hs']<r['sndn']):return tpl
    q=(r['hs']-tpeak)/(r['sndn']-tpeak)
    s=max(0.0,math.sin(math.pi*q))**p
    return max(r['tmin'],tpl-lam*excess*s)


def write(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)


def main():
    rows=cp.load_rows(); cal=[r for r in rows if r['year']<=2016]; val=[r for r in rows if r['year']>=2017]
    high=[r for r in cal if r['dtr']>=DTR_C]
    grid=[];best=None
    # 81 lambda values x 24 p values = 1944 candidates.
    pvals=[0.2+i*0.1 for i in range(24)]  # 0.2..2.5
    for p in pvals:
        for i in range(81):
            lam=i*0.05
            fn=lambda r,L=lam,P=p:shaped(r,L,P)
            ma=base.metric(cal,fn); mh=base.metric(high,fn); obj=.5*ma['rmse']+.5*mh['rmse']
            rec={'lambda':lam,'p':p,'cal_all_rmse':ma['rmse'],'cal_high_rmse':mh['rmse'],'objective':obj}
            grid.append(rec)
            if best is None or obj<best['objective']:best=rec
    lam=best['lambda'];p=best['p'];boundary=(lam in {0.0,4.0} or p in {pvals[0],pvals[-1]})
    # Single-parameter M3 uses its calibration optimum from expanded search (lambda=3.35,p=1).
    models=[('M0_DSSAT',cp.original),('M1_PL_XJ',cp.pl_xj),('M2_PHASE',cp.phase_compression),('M3_PULSE_1P',lambda r:shaped(r,3.35,1.0)),('M4_SHAPED_2P',lambda r:shaped(r,lam,p))]
    metrics=[]
    for split,subset in [('Calibration_2000_2016',cal),('Validation_2017_2024',val)]:
        for scope,s in [('May-Sep',subset),('DTR>=15',[r for r in subset if r['dtr']>=15])]:
            for name,fn in models:
                m=base.metric(s,fn);metrics.append({'split':split,'scope':scope,'model':name,'lambda':lam if name=='M4_SHAPED_2P' else '', 'p':p if name=='M4_SHAPED_2P' else '',**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})
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
    write(GRID,[{k:round(v,6) if isinstance(v,float) else v for k,v in r.items()} for r in grid]);write(VAL,metrics);write(BD,bd);write(BH,bh)
    mp={(r['split'],r['scope'],r['model']):r for r in metrics};m0=mp[('Validation_2017_2024','DTR>=15','M0_DSSAT')];m4=mp[('Validation_2017_2024','DTR>=15','M4_SHAPED_2P')];a0=mp[('Validation_2017_2024','May-Sep','M0_DSSAT')];a4=mp[('Validation_2017_2024','May-Sep','M4_SHAPED_2P')]
    imp=100*(m0['rmse']-m4['rmse'])/m0['rmse']; impall=100*(a0['rmse']-a4['rmse'])/a0['rmse']
    aft=[r for r in val if 14<=r['hour_bin']<=18];af0=base.metric(aft,cp.original);af4=base.metric(aft,lambda r:shaped(r,lam,p));night=[r for r in val if r['hour_bin']>=20 or r['hour_bin']<=5];n0=base.metric(night,cp.original);n4=base.metric(night,lambda r:shaped(r,lam,p))
    txt=f'''# Urumqi DTR-triggered two-parameter cooling shape

- Fixed DTRc: **14.5 C**
- Calibrated lambda: **{lam:.2f}**
- Calibrated shape p: **{p:.2f}**
- Optimum at search boundary: **{'YES' if boundary else 'NO'}**
- Formula: `Tnew = TPL - lambda*(DTR-14.5)+*sin(pi*q)^p`, peak<time<sunset.
- Peak, sunset, low-DTR and nighttime predictions are unchanged by construction.

## Independent validation
- May-Sep RMSE: **{a0['rmse']:.4f} -> {a4['rmse']:.4f} C** ({impall:.2f}% improvement).
- DTR>=15 RMSE: **{m0['rmse']:.4f} -> {m4['rmse']:.4f} C** ({imp:.2f}% improvement).
- DTR>=15 MAE: **{m0['mae']:.4f} -> {m4['mae']:.4f} C**.
- DTR>=15 Bias: **{m0['mbe']:.4f} -> {m4['mbe']:.4f} C**.
- DTR>=15 R2: **{m0['r2']:.4f} -> {m4['r2']:.4f}**.
- Afternoon 14-18 RMSE/Bias: official **{af0['rmse']:.4f}/{af0['mbe']:.4f}**, M4 **{af4['rmse']:.4f}/{af4['mbe']:.4f} C**.
- Night RMSE: official **{n0['rmse']:.4f}**, M4 **{n4['rmse']:.4f} C**.

Interpret p physically as the temporal concentration of the extra post-peak cooling. If p is interior and validation improvement exceeds the one-parameter pulse without harming night/low-DTR, this is the first structurally defensible local candidate for source-level DSSAT testing.
'''
    README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
