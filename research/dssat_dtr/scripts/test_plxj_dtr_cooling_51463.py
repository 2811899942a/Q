#!/usr/bin/env python3
"""Combine Urumqi regional PL parameters with DTR-triggered post-peak cooling.

M0: official DSSAT PL.
M1: PL-XJ-BAL regional A/B/C.
M2: PL-XJ-BAL + DTR-triggered cooling shape.

DTRc=14.5 C is fixed from the independent breakpoint diagnosis. The structural
term is zero below DTRc and zero at the PL-XJ peak and sunset, preserving the
regionalized baseline outside the affected post-peak interval.
"""
import csv,math
from pathlib import Path
import test_dtr_phase_compression_51463 as base
import test_dtr_cooling_pulse_51463 as cp

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463';DTRC=14.5
GRID=DATA/'plxj_dtr_cooling_grid.csv';VAL=DATA/'plxj_dtr_cooling_validation.csv';BD=DATA/'plxj_dtr_cooling_by_dtr.csv';BH=DATA/'plxj_dtr_cooling_by_hour.csv';README=DATA/'README_PLXJ_DTR_COOLING.md'

def modified(r,lam,p):
    tpl=cp.pl_xj(r);ex=max(0.0,r['dtr']-DTRC)
    if ex<=0:return tpl
    A,B,C=base.PL_XJ_BAL;tmin_time=r['snup']+C;tpeak=tmin_time+r['dayl']/2+A
    if not(tpeak<r['hs']<r['sndn']):return tpl
    q=(r['hs']-tpeak)/(r['sndn']-tpeak);shape=max(0.0,math.sin(math.pi*q))**p
    return max(r['tmin'],tpl-lam*ex*shape)

def write(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
def main():
    rows=cp.load_rows();cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];high=[r for r in cal if r['dtr']>=DTRC]
    grid=[];best=None;pvals=[0.05+i*0.05 for i in range(20)]
    for p in pvals:
        for i in range(81):
            lam=i*.05;fn=lambda r,L=lam,P=p:modified(r,L,P);ma=base.metric(cal,fn);mh=base.metric(high,fn);obj=.5*ma['rmse']+.5*mh['rmse'];rec={'lambda':lam,'p':p,'cal_all_rmse':ma['rmse'],'cal_high_rmse':mh['rmse'],'objective':obj};grid.append(rec)
            if best is None or obj<best['objective']:best=rec
    lam=best['lambda'];p=best['p'];boundary=(lam in {0.0,4.0} or p in {pvals[0],pvals[-1]})
    models=[('M0_DSSAT',cp.original),('M1_PL_XJ',cp.pl_xj),('M2_PLXJ_DTR_COOL',lambda r:modified(r,lam,p))]
    metrics=[]
    for split,subset in [('Calibration_2000_2016',cal),('Validation_2017_2024',val)]:
        for scope,s in [('May-Sep',subset),('DTR>=15',[r for r in subset if r['dtr']>=15])]:
            for name,fn in models:
                m=base.metric(s,fn);metrics.append({'split':split,'scope':scope,'model':name,'lambda':lam if name.startswith('M2') else '','p':p if name.startswith('M2') else '',**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})
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
    write(GRID,[{k:round(v,6) if isinstance(v,float) else v for k,v in x.items()} for x in grid]);write(VAL,metrics);write(BD,bd);write(BH,bh)
    mp={(r['split'],r['scope'],r['model']):r for r in metrics};o=mp[('Validation_2017_2024','DTR>=15','M0_DSSAT')];b=mp[('Validation_2017_2024','DTR>=15','M1_PL_XJ')];m=mp[('Validation_2017_2024','DTR>=15','M2_PLXJ_DTR_COOL')];oa=mp[('Validation_2017_2024','May-Sep','M0_DSSAT')];ba=mp[('Validation_2017_2024','May-Sep','M1_PL_XJ')];ma=mp[('Validation_2017_2024','May-Sep','M2_PLXJ_DTR_COOL')]
    imp0=100*(o['rmse']-m['rmse'])/o['rmse'];imp1=100*(b['rmse']-m['rmse'])/b['rmse'];impall0=100*(oa['rmse']-ma['rmse'])/oa['rmse'];impall1=100*(ba['rmse']-ma['rmse'])/ba['rmse']
    txt=f'''# PL-XJ + DTR-triggered post-peak cooling

- Fixed DTRc: **14.5 C**.
- Calibrated lambda: **{lam:.2f}**.
- Calibrated p: **{p:.2f}**.
- Optimum at search boundary: **{'YES' if boundary else 'NO'}**.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 MAE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|---:|
| Official DSSAT | {oa['rmse']:.4f} | {o['rmse']:.4f} | {o['mae']:.4f} | {o['mbe']:.4f} | {o['r2']:.4f} |
| PL-XJ | {ba['rmse']:.4f} | {b['rmse']:.4f} | {b['mae']:.4f} | {b['mbe']:.4f} | {b['r2']:.4f} |
| PL-XJ + DTR cooling | {ma['rmse']:.4f} | {m['rmse']:.4f} | {m['mae']:.4f} | {m['mbe']:.4f} | {m['r2']:.4f} |

- All May-Sep improvement vs official: **{impall0:.2f}%**; additional improvement vs PL-XJ: **{impall1:.2f}%**.
- DTR>=15 improvement vs official: **{imp0:.2f}%**; additional improvement vs PL-XJ: **{imp1:.2f}%**.

Interpretation: a positive independent gain beyond PL-XJ supports a two-layer Urumqi formulation: regional baseline parameters for ordinary conditions plus a DTR-threshold structural correction for post-peak cooling. If the added gain is negligible, retain PL-XJ as the practical baseline and continue mechanism discovery before source-code modification.
''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
