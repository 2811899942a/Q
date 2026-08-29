#!/usr/bin/env python3
"""Fit a Urumqi-specific two-sided hot-shoulder narrowing correction.

For DTR > 14.5 C only, preserve the official DSSAT HTEMP value at:
- solar noon shoulder start (12:00 apparent solar time),
- official modeled Tmax time,
- sunset.

Between noon and modeled Tmax, subtract alpha_pre*(DTR-DTRc)*4*v*(1-v).
Between modeled Tmax and sunset, subtract alpha_post*(DTR-DTRc)*4*u*(1-u).

Thus Tmax remains an exact anchor while the overly broad hot shoulder can narrow on
both sides. alpha_pre and alpha_post are fitted analytically on 2000-2016 May-Sep
and evaluated independently on 2017-2024 May-Sep.
"""
from __future__ import annotations
import csv, math, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed_51463'
INFILE=DATA/'htemp_pointwise_2000_2024.csv'
OUT=DATA/'two_sided_shoulder_validation.csv'
DTR_OUT=DATA/'two_sided_shoulder_by_dtr.csv'
HOUR_OUT=DATA/'two_sided_shoulder_by_hour.csv'
README=DATA/'README_TWO_SIDED_SHOULDER.md'
DTRC=14.5; A=2.0; C=1.0

def mean(x): return statistics.mean(x) if x else float('nan')
def metric(rows,pf):
    obs=[]; pred=[]
    for r in rows: obs.append(float(r['obs_c'])); pred.append(pf(r))
    e=[p-o for p,o in zip(pred,obs)]
    rm=math.sqrt(mean([z*z for z in e])); ma=mean([abs(z) for z in e]); mb=mean(e)
    mo,mp=mean(obs),mean(pred); so=sum((x-mo)**2 for x in obs); sp=sum((x-mp)**2 for x in pred)
    rr=sum((o-mo)*(p-mp) for o,p in zip(obs,pred))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan')
    return {'n':len(rows),'rmse':rm,'mae':ma,'mbe':mb,'r2':rr*rr}

def basis(r):
    d=float(r['formal_dtr_c']); hs=float(r['solar_hour'])
    if d<=DTRC:return (0.0,0.0)
    snup=float(r['snup_solar_h']); sndn=float(r['sndn_solar_h']); dayl=float(r['dayl_h'])
    tpeak=snup+C+dayl/2.0+A
    ex=d-DTRC
    xp=xq=0.0
    if 12.0 < hs < tpeak and tpeak>12.0:
        v=(hs-12.0)/(tpeak-12.0); xp=ex*4.0*v*(1-v)
    if tpeak < hs < sndn and sndn>tpeak:
        u=(hs-tpeak)/(sndn-tpeak); xq=ex*4.0*u*(1-u)
    return xp,xq

def solve2(rows):
    # e0 ~= a_pre*xpre + a_post*xpost; disjoint bases but solve general 2x2.
    s11=s22=s12=t1=t2=0.0
    for r in rows:
        x1,x2=basis(r); e=float(r['pred_c'])-float(r['obs_c'])
        s11+=x1*x1; s22+=x2*x2; s12+=x1*x2; t1+=x1*e; t2+=x2*e
    den=s11*s22-s12*s12
    if abs(den)<1e-12:return 0.0,0.0
    a1=(t1*s22-t2*s12)/den; a2=(t2*s11-t1*s12)/den
    return max(0.0,a1),max(0.0,a2)

def dtrbin(d):
    if d<10:return '<10'
    if d<15:return '10-<15'
    if d<20:return '15-<20'
    return '>=20'

def main():
    rows=[]
    with INFILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if int(r['month']) in [5,6,7,8,9]:
                r['year']=int(r['solar_date'][:4]);rows.append(r)
    cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017]
    ap,aq=solve2(cal)
    p0=lambda r:float(r['pred_c'])
    pnew=lambda r:float(r['pred_c'])-ap*basis(r)[0]-aq*basis(r)[1]
    models=[('M0_OFFICIAL',p0),('M4_TWO_SIDED_SHOULDER',pnew)]
    groups=[('May-Sep',val),('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
    rec=[]
    for name,pf in models:
        for gl,rs in groups:
            m=metric(rs,pf);m.update({'model':name,'group':gl});rec.append(m)
    fields=['model','group','n','rmse','mae','mbe','r2']
    with OUT.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r[k] for k in fields} for r in rec])
    dr=[]
    for name,pf in models:
        for b in ['<10','10-<15','15-<20','>=20']:
            rs=[r for r in val if dtrbin(float(r['formal_dtr_c']))==b]
            m=metric(rs,pf);m.update({'model':name,'dtr_bin':b});dr.append(m)
    with DTR_OUT.open('w',newline='',encoding='utf-8-sig') as f:
        ff=['model','dtr_bin','n','rmse','mae','mbe','r2'];w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerows([{k:r[k] for k in ff} for r in dr])
    hr=[]
    for name,pf in models:
        for h in [11,12,14,15,17,18,20,23]:
            rs=[r for r in val if int(float(r['solar_hour']))==h]
            m=metric(rs,pf) if rs else {'n':0,'rmse':'','mae':'','mbe':'','r2':''};m.update({'model':name,'solar_hour':h});hr.append(m)
    with HOUR_OUT.open('w',newline='',encoding='utf-8-sig') as f:
        ff=['model','solar_hour','n','rmse','mae','mbe','r2'];w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerows([{k:r[k] for k in ff} for r in hr])
    mm={(r['model'],r['group']):r for r in rec};bo=mm[('M0_OFFICIAL','DTR>=15')];bn=mm[('M4_TWO_SIDED_SHOULDER','DTR>=15')]
    imp=100*(bo['rmse']-bn['rmse'])/bo['rmse']
    text=f'''# Urumqi two-sided DTR-triggered hot-shoulder narrowing\n\n- DTR trigger: **>{DTRC:.1f} C**\n- Fitted pre-peak shoulder coefficient: **alpha_pre={ap:.3f}**\n- Fitted post-peak shoulder coefficient: **alpha_post={aq:.3f}**\n- Calibration: 2000-2016 May-Sep\n- Independent validation: 2017-2024 May-Sep\n\nThe correction is zero at solar noon, official modeled Tmax time, and sunset; therefore the daily Tmax anchor is retained.\n\n## Independent validation DTR>=15 C\n\n| Model | RMSE | MAE | Bias | R2 |\n|---|---:|---:|---:|---:|\n| Official | {bo['rmse']:.4f} | {bo['mae']:.4f} | {bo['mbe']:.4f} | {bo['r2']:.4f} |\n| Two-sided shoulder | {bn['rmse']:.4f} | {bn['mae']:.4f} | {bn['mbe']:.4f} | {bn['r2']:.4f} |\n\nRMSE improvement: **{imp:.2f}%**.\n'''
    README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
