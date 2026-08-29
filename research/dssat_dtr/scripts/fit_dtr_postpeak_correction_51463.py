#!/usr/bin/env python3
"""Fit a minimal Urumqi-specific post-peak correction to original DSSAT HTEMP.

Mechanism hypothesis:
When May-Sep DTR exceeds the locally diagnosed breakpoint (~14.5 C),
DSSAT keeps temperatures too warm during the post-peak daylight period.

Correction form (applied only after the DSSAT daytime peak and before sunset):

  T_new = T_PL - alpha * max(0, DTR-DTRc) * 4*u*(1-u)

where u=(t-tpeak)/(sunset-tpeak) in [0,1].
This preserves T at the modeled peak and at sunset and modifies only the
interior post-peak daylight curve. It adds only one fitted parameter, alpha.

Calibration: 2000-2016 May-Sep.
Independent validation: 2017-2024 May-Sep.
"""

from __future__ import annotations

import csv, math, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed_51463'
INFILE=DATA/'htemp_pointwise_2000_2024.csv'
OUT_GRID=DATA/'postpeak_alpha_grid.csv'
OUT_METRICS=DATA/'postpeak_validation_metrics.csv'
OUT_DTR=DATA/'postpeak_validation_by_dtr.csv'
OUT_HOUR=DATA/'postpeak_validation_by_solar_hour.csv'
README=DATA/'README_POSTPEAK_CORRECTION.md'

DTRC=14.5
A=2.0
C=1.0


def mean(x): return statistics.mean(x) if x else float('nan')
def rmse(e): return math.sqrt(mean([v*v for v in e])) if e else float('nan')
def mae(e): return mean([abs(v) for v in e]) if e else float('nan')
def r2(obs,pred):
    if len(obs)<3: return float('nan')
    mo,mp=mean(obs),mean(pred)
    so=sum((x-mo)**2 for x in obs); sp=sum((x-mp)**2 for x in pred)
    if so<=0 or sp<=0: return float('nan')
    r=sum((o-mo)*(p-mp) for o,p in zip(obs,pred))/math.sqrt(so*sp)
    return r*r

def dtrbin(x):
    if x<10:return '<10'
    if x<15:return '10-<15'
    if x<20:return '15-<20'
    return '>=20'

def corr_amount(r,alpha):
    dtr=float(r['formal_dtr_c'])
    if dtr<=DTRC:return 0.0
    hs=float(r['solar_hour'])
    snup=float(r['snup_solar_h']); sndn=float(r['sndn_solar_h']); dayl=float(r['dayl_h'])
    tpeak=snup+C+dayl/2.0+A
    if hs<=tpeak or hs>=sndn or sndn<=tpeak:return 0.0
    u=(hs-tpeak)/(sndn-tpeak)
    shape=4.0*u*(1.0-u)
    return alpha*(dtr-DTRC)*shape

def eval_rows(rows,alpha):
    obs=[]; pred=[]
    for r in rows:
        o=float(r['obs_c']); p=float(r['pred_c'])-corr_amount(r,alpha)
        obs.append(o); pred.append(p)
    e=[p-o for p,o in zip(pred,obs)]
    return {'n':len(rows),'rmse':rmse(e),'mae':mae(e),'mbe':mean(e),'r2':r2(obs,pred)}

def main():
    rows=[]
    with INFILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if int(r['month']) not in [5,6,7,8,9]:continue
            r['year']=int(r['solar_date'][:4])
            rows.append(r)
    cal=[r for r in rows if r['year']<=2016]
    val=[r for r in rows if r['year']>=2017]

    grid=[]
    for i in range(0,301):
        alpha=i/200.0  # 0..1.5 step 0.005
        m_all=eval_rows(cal,alpha)
        cal_hi=[r for r in cal if float(r['formal_dtr_c'])>=15]
        m_hi=eval_rows(cal_hi,alpha)
        # balanced objective, both normalized to official RMSE
        base_all=eval_rows(cal,0.0)['rmse']; base_hi=eval_rows(cal_hi,0.0)['rmse']
        score=0.5*(m_all['rmse']/base_all)+0.5*(m_hi['rmse']/base_hi)
        grid.append({'alpha':alpha,'cal_rmse_all':m_all['rmse'],'cal_rmse_dtr_ge15':m_hi['rmse'],'balanced_score':score})
    best=min(grid,key=lambda r:r['balanced_score'])
    alpha=float(best['alpha'])

    with OUT_GRID.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(grid[0].keys())); w.writeheader(); w.writerows(grid)

    groups=[
        ('May-Sep',val),
        ('May-Sep DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),
        ('May-Sep DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18]),
    ]
    metrics=[]
    for label,rs in groups:
        for model,a in [('DSSAT-OFFICIAL',0.0),('DTR-POSTPEAK',alpha)]:
            m=eval_rows(rs,a); m.update({'model':model,'group':label}); metrics.append(m)
    with OUT_METRICS.open('w',newline='',encoding='utf-8-sig') as f:
        fields=['model','group','n','rmse','mae','mbe','r2']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows([{k:r[k] for k in fields} for r in metrics])

    by_dtr=[]
    for b in ['<10','10-<15','15-<20','>=20']:
        rs=[r for r in val if dtrbin(float(r['formal_dtr_c']))==b]
        for model,a in [('DSSAT-OFFICIAL',0.0),('DTR-POSTPEAK',alpha)]:
            m=eval_rows(rs,a); m.update({'model':model,'dtr_bin':b}); by_dtr.append(m)
    with OUT_DTR.open('w',newline='',encoding='utf-8-sig') as f:
        fields=['model','dtr_bin','n','rmse','mae','mbe','r2']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows([{k:r[k] for k in fields} for r in by_dtr])

    by_hour=[]
    for h in range(24):
        rs=[r for r in val if int(float(r['solar_hour']))==h]
        for model,a in [('DSSAT-OFFICIAL',0.0),('DTR-POSTPEAK',alpha)]:
            m=eval_rows(rs,a); m.update({'model':model,'solar_hour':h}); by_hour.append(m)
    with OUT_HOUR.open('w',newline='',encoding='utf-8-sig') as f:
        fields=['model','solar_hour','n','rmse','mae','mbe','r2']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows([{k:r[k] for k in fields} for r in by_hour])

    mm={(r['model'],r['group']):r for r in metrics}
    off=mm[('DSSAT-OFFICIAL','May-Sep')]; new=mm[('DTR-POSTPEAK','May-Sep')]
    offh=mm[('DSSAT-OFFICIAL','May-Sep DTR>=15')]; newh=mm[('DTR-POSTPEAK','May-Sep DTR>=15')]
    imp_all=100*(off['rmse']-new['rmse'])/off['rmse']
    imp_hi=100*(offh['rmse']-newh['rmse'])/offh['rmse']
    text=f'''# Urumqi threshold-triggered post-peak correction\n\n## Formula\n\nFor DTR <= {DTRC:.1f} C, original DSSAT HTEMP is unchanged.\nFor DTR > {DTRC:.1f} C and only between the DSSAT daytime peak and sunset:\n\n`T_new = T_PL - alpha*(DTR-{DTRC:.1f})*4*u*(1-u)`\n\nwhere `u=(t-tpeak)/(sunset-tpeak)`. The correction is exactly zero at peak and sunset.\n\n## Calibration\n\n- Period: 2000-2016 May-Sep\n- One fitted parameter only: alpha\n- Selected alpha: **{alpha:.3f}**\n\n## Independent validation 2017-2024\n\n| Scope | Official RMSE | New RMSE | Improvement | Official Bias | New Bias |\n|---|---:|---:|---:|---:|---:|\n| May-Sep | {off['rmse']:.4f} | {new['rmse']:.4f} | {imp_all:.2f}% | {off['mbe']:.4f} | {new['mbe']:.4f} |\n| DTR>=15 C | {offh['rmse']:.4f} | {newh['rmse']:.4f} | {imp_hi:.2f}% | {offh['mbe']:.4f} | {newh['mbe']:.4f} |\n\n## Interpretation\n\nThis is a deliberately minimal mechanism test. A meaningful independent-validation improvement would support the hypothesis that excessive post-peak thermal persistence is a real component of Urumqi HTEMP error. If improvement is weak, the mechanism must be revised before any Fortran source modification.\n'''
    README.write_text(text,encoding='utf-8')
    print(text)

if __name__=='__main__': main()
