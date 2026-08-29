#!/usr/bin/env python3
"""Test a Urumqi-specific dual-stage monotonic post-peak phase warp.

Local phase inversion (calibration only) shows positive phase advance immediately
after the peak and negative phase advance later in the afternoon. The zero crossing
is estimated robustly from calibration medians, then fixed before parameter fitting.

For DTR>DTRc and q=(t-tpeak)/(sunset-tpeak):
  early q<=q0: qeff = q0 * (q/q0)^a,       a=1/(1+alpha*E) <=1
  late  q> q0: qeff = q0+(1-q0)*x^b,       b=1+beta*E >=1
where E=DTR-DTRc and x=(q-q0)/(1-q0).

Thus early cooling advances, late cooling retards, and qeff remains monotonic with
exact anchors qeff(0)=0, qeff(q0)=q0, qeff(1)=1. Temperature is always evaluated on
the original PL-XJ post-peak branch; night remains unchanged.
"""
import csv,math,statistics
from pathlib import Path
import test_dtr_phase_compression_51463 as base
import test_dtr_cooling_pulse_51463 as cp
DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463';INV=DATA/'postpeak_phase_inversion_points.csv';DTRC=14.5
GRID=DATA/'dual_phase_warp_grid.csv';VAL=DATA/'dual_phase_warp_validation.csv';BD=DATA/'dual_phase_warp_by_dtr.csv';BH=DATA/'dual_phase_warp_by_hour.csv';README=DATA/'README_DUAL_PHASE_WARP.md'

def med(xs):return statistics.median(xs)
def derive_q0():
    pts=[]
    with INV.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['split']!='Calibration' or r['status']!='MAPPABLE':continue
            d=float(r['dtr_c']);q=float(r['q_actual']);adv=float(r['phase_advance'])
            if 14.5<=d<18:pts.append((q,adv))
    early=[z for z in pts if z[0]<.2];late=[z for z in pts if .6<=z[0]<.8]
    q1,a1=med([z[0] for z in early]),med([z[1] for z in early]);q2,a2=med([z[0] for z in late]),med([z[1] for z in late])
    q0=q1+(0-a1)*(q2-q1)/(a2-a1)
    return q0,(q1,a1,q2,a2,len(early),len(late))
def plxj_at(r,hs):
    A,B,C=base.PL_XJ_BAL;return base.htemp(hs,r['tmax'],r['tmin'],r['dayl'],r['snup'],r['sndn'],A,B,C,0)
def warp(r,alpha,beta,q0):
    tpl=cp.pl_xj(r);E=max(0.0,r['dtr']-DTRC)
    if E<=0:return tpl
    A,B,C=base.PL_XJ_BAL;tpeak=r['snup']+C+r['dayl']/2+A
    if not(tpeak<r['hs']<r['sndn']):return tpl
    q=(r['hs']-tpeak)/(r['sndn']-tpeak)
    if q<=q0:
        a=1/(1+alpha*E);qeff=q0*((q/q0)**a)
    else:
        b=1+beta*E;x=(q-q0)/(1-q0);qeff=q0+(1-q0)*(x**b)
    heff=tpeak+qeff*(r['sndn']-tpeak);return plxj_at(r,heff)
def write(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
def main():
    q0,diag=derive_q0();rows=cp.load_rows();cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];high=[r for r in cal if r['dtr']>=DTRC]
    grid=[];best=None
    alphas=[i*.1 for i in range(51)];betas=[i*.1 for i in range(31)]
    for alpha in alphas:
        for beta in betas:
            fn=lambda r,A=alpha,B=beta:warp(r,A,B,q0);ma=base.metric(cal,fn);mh=base.metric(high,fn);obj=.5*ma['rmse']+.5*mh['rmse'];rec={'alpha':alpha,'beta':beta,'q0':q0,'cal_all_rmse':ma['rmse'],'cal_high_rmse':mh['rmse'],'objective':obj};grid.append(rec)
            if best is None or obj<best['objective']:best=rec
    alpha=best['alpha'];beta=best['beta'];boundary=(alpha in {alphas[0],alphas[-1]} or beta in {betas[0],betas[-1]})
    models=[('M0_DSSAT',cp.original),('M1_PL_XJ',cp.pl_xj),('M2_DUAL_PHASE',lambda r:warp(r,alpha,beta,q0))]
    metrics=[]
    for split,subset in [('Calibration_2000_2016',cal),('Validation_2017_2024',val)]:
        for scope,s in [('May-Sep',subset),('DTR>=15',[r for r in subset if r['dtr']>=15])]:
            for name,fn in models:
                m=base.metric(s,fn);metrics.append({'split':split,'scope':scope,'model':name,'q0':round(q0,4) if name=='M2_DUAL_PHASE' else '','alpha':alpha if name=='M2_DUAL_PHASE' else '','beta':beta if name=='M2_DUAL_PHASE' else '',**{x:round(v,4) if isinstance(v,float) else v for x,v in m.items()}})
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
    # physical QA
    days={}
    for r in rows:
        if r['dtr']>=DTRC:days.setdefault(r['date'],r)
    bad=0;maxinc=0
    for r in days.values():
        A,B,C=base.PL_XJ_BAL;tpeak=r['snup']+C+r['dayl']/2+A;h=tpeak;ts=[]
        while h<=r['sndn']+1e-9:
            rr=dict(r);rr['hs']=h;ts.append(warp(rr,alpha,beta,q0));h+=1/12
        inc=max([ts[i+1]-ts[i] for i in range(len(ts)-1)] or [0]);maxinc=max(maxinc,inc)
        if inc>.02:bad+=1
    mp={(r['split'],r['scope'],r['model']):r for r in metrics};o=mp[('Validation_2017_2024','DTR>=15','M0_DSSAT')];b=mp[('Validation_2017_2024','DTR>=15','M1_PL_XJ')];m=mp[('Validation_2017_2024','DTR>=15','M2_DUAL_PHASE')];oa=mp[('Validation_2017_2024','May-Sep','M0_DSSAT')];ma=mp[('Validation_2017_2024','May-Sep','M2_DUAL_PHASE')]
    imp=100*(o['rmse']-m['rmse'])/o['rmse'];imp1=100*(b['rmse']-m['rmse'])/b['rmse'];impall=100*(oa['rmse']-ma['rmse'])/oa['rmse'];q1,a1,q2,a2,n1,n2=diag
    txt=f'''# Urumqi dual-stage monotonic post-peak phase warp

## Calibration-only shape discovery
- Early cluster: n={n1}, median q={q1:.3f}, median phase advance={a1:.3f}.
- Late cluster: n={n2}, median q={q2:.3f}, median phase advance={a2:.3f}.
- Interpolated phase-crossing q0 fixed at **{q0:.3f}** before alpha/beta fitting.

## Fitted DTR response
- DTRc: **14.5 C**.
- alpha (early acceleration): **{alpha:.2f} per C**.
- beta (late retardation): **{beta:.2f} per C**.
- Optimum at search boundary: **{'YES' if boundary else 'NO'}**.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| Official | {mp[('Validation_2017_2024','May-Sep','M0_DSSAT')]['rmse']:.4f} | {o['rmse']:.4f} | {o['mae']:.4f} | {o['mbe']:.4f} | {o['r2']:.4f} |
| PL-XJ | {mp[('Validation_2017_2024','May-Sep','M1_PL_XJ')]['rmse']:.4f} | {b['rmse']:.4f} | {b['mae']:.4f} | {b['mbe']:.4f} | {b['r2']:.4f} |
| Dual-phase warp | {ma['rmse']:.4f} | {m['rmse']:.4f} | {m['mae']:.4f} | {m['mbe']:.4f} | {m['r2']:.4f} |

- May-Sep improvement vs official: **{impall:.2f}%**.
- DTR>=15 improvement vs official: **{imp:.2f}%**.
- Additional DTR>=15 improvement beyond PL-XJ: **{imp1:.2f}%**.

## Physical QA
- High-DTR May-Sep days checked at 5-min resolution: **{len(days)}**.
- Days with >0.02 C post-peak increase: **{bad}**.
- Maximum 5-min increase: **{maxinc:.4f} C**.

This form directly encodes the calibration-observed sign reversal: accelerated early post-peak cooling followed by relative late-afternoon retardation, while preserving a monotonic temperature decline and fixed peak/sunset anchors.
''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
