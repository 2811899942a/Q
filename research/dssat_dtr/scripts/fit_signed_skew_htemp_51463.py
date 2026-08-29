#!/usr/bin/env python3
"""Fit a calibration-only Urumqi DTR-triggered signed-skew HTEMP correction.

The correction is derived from the observed local residual structure rather than an
external temperature model.

Formal trigger: DTRc=14.8 C, estimated from 2000-2016 calibration-period asymmetry.
Validation 2017-2024 is untouched.

For DTR>DTRc:
1) Rising branch x=(t-tmin_time)/(tpeak-tmin_time), x in [0,1]
   B_rise = x(1-x)(0.5-x) / BMAX, BMAX=0.0481125224.
   B_rise is + in early warming and - in late warming, and zero at x=0,0.5,1.
   T_new = T_PL + beta_rise*(DTR-DTRc)*B_rise.
   Thus beta_rise>0 simultaneously warms the observed cold-biased morning and cools
   the late pre-peak hot shoulder while preserving Tmin, mid-rise crossing, and Tmax.

2) Falling daylight branch u=(t-tpeak)/(sunset-tpeak), u in [0,1]
   B_fall=4u(1-u), zero at peak and sunset.
   T_new = T_PL - beta_fall*(DTR-DTRc)*B_fall.

Both beta parameters have the interpretable unit C correction per C excess DTR at
maximum basis amplitude. They are fitted analytically by least squares using only
2000-2016 May-Sep data.
"""
from __future__ import annotations
import csv, math, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed_51463'
INFILE=DATA/'htemp_pointwise_2000_2024.csv'
README=DATA/'README_SIGNED_SKEW_HTEMP.md'
PARAM=DATA/'signed_skew_parameters.csv'
VAL=DATA/'signed_skew_validation.csv'
DTR=DATA/'signed_skew_validation_by_dtr.csv'
HOUR=DATA/'signed_skew_validation_by_hour.csv'

DTRC=14.8; A=2.0; C=1.0; BMAX=0.04811252243246881

def mean(x): return statistics.mean(x) if x else float('nan')
def basis(r):
    d=float(r['formal_dtr_c']); hs=float(r['solar_hour'])
    if d<=DTRC:return 0.0,0.0
    snup=float(r['snup_solar_h']); sndn=float(r['sndn_solar_h']); dayl=float(r['dayl_h'])
    t0=snup+C; tp=t0+dayl/2.0+A; ex=d-DTRC
    br=bf=0.0
    if t0 < hs < tp and tp>t0:
        x=(hs-t0)/(tp-t0)
        br=ex*(x*(1-x)*(0.5-x)/BMAX)
    elif tp < hs < sndn and sndn>tp:
        u=(hs-tp)/(sndn-tp)
        bf=ex*4*u*(1-u)
    return br,bf

def fit(cal):
    # New error = e + beta_r*br - beta_f*bf. Branches are disjoint.
    sr=tr=sf=tf=0.0; nr=nf=0
    for r in cal:
        br,bf=basis(r); e=float(r['pred_c'])-float(r['obs_c'])
        if br!=0:
            sr+=br*br; tr+=br*e; nr+=1
        if bf!=0:
            sf+=bf*bf; tf+=bf*e; nf+=1
    beta_r=-tr/sr if sr>0 else 0.0
    beta_f=tf/sf if sf>0 else 0.0
    return beta_r,beta_f,nr,nf

def pnew(r,brc,bfc):
    br,bf=basis(r)
    return float(r['pred_c'])+brc*br-bfc*bf

def metric(rows,pf):
    if not rows:return {'n':0,'rmse':float('nan'),'mae':float('nan'),'mbe':float('nan'),'r2':float('nan')}
    obs=[float(r['obs_c']) for r in rows]; pred=[pf(r) for r in rows]; e=[p-o for p,o in zip(pred,obs)]
    rm=math.sqrt(mean([z*z for z in e]));ma=mean([abs(z) for z in e]);mb=mean(e)
    mo,mp=mean(obs),mean(pred);so=sum((o-mo)**2 for o in obs);sp=sum((p-mp)**2 for p in pred)
    rr=sum((o-mo)*(p-mp) for o,p in zip(obs,pred))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan')
    return {'n':len(rows),'rmse':rm,'mae':ma,'mbe':mb,'r2':rr*rr}
def dbin(d):
    if d<10:return '<10'
    if d<15:return '10-<15'
    if d<18:return '15-<18'
    if d<20:return '18-<20'
    return '>=20'

def main():
    rows=[]
    with INFILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if int(r['month']) in [5,6,7,8,9]:
                r['year']=int(r['solar_date'][:4]);rows.append(r)
    cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017]
    brc,bfc,nr,nf=fit(cal)
    with PARAM.open('w',newline='',encoding='utf-8-sig') as f:
        ff=['dtr_threshold_c','beta_rise','beta_fall','n_cal_rise','n_cal_fall'];w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerow({'dtr_threshold_c':DTRC,'beta_rise':brc,'beta_fall':bfc,'n_cal_rise':nr,'n_cal_fall':nf})
    models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M6_SIGNED_SKEW',lambda r:pnew(r,brc,bfc))]
    groups=[('May-Sep',val),('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
    rec=[]
    for name,pf in models:
        for gl,rs in groups:
            m=metric(rs,pf);m.update({'model':name,'group':gl});rec.append(m)
    ff=['model','group','n','rmse','mae','mbe','r2']
    with VAL.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerows([{k:r[k] for k in ff} for r in rec])
    dr=[]
    for name,pf in models:
        for b in ['<10','10-<15','15-<18','18-<20','>=20']:
            rs=[r for r in val if dbin(float(r['formal_dtr_c']))==b];m=metric(rs,pf);m.update({'model':name,'dtr_bin':b});dr.append(m)
    ff2=['model','dtr_bin','n','rmse','mae','mbe','r2']
    with DTR.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=ff2);w.writeheader();w.writerows([{k:r[k] for k in ff2} for r in dr])
    hr=[]
    for name,pf in models:
        for h in [5,8,9,11,12,14,15,17,18,20,23]:
            rs=[r for r in val if int(float(r['solar_hour']))==h];m=metric(rs,pf);m.update({'model':name,'solar_hour':h});hr.append(m)
    ff3=['model','solar_hour','n','rmse','mae','mbe','r2']
    with HOUR.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=ff3);w.writeheader();w.writerows([{k:r[k] for k in ff3} for r in hr])
    mm={(r['model'],r['group']):r for r in rec};bo=mm[('M0_OFFICIAL','DTR>=15')];bn=mm[('M6_SIGNED_SKEW','DTR>=15')];ba=mm[('M0_OFFICIAL','May-Sep')];na=mm[('M6_SIGNED_SKEW','May-Sep')]
    imp=100*(bo['rmse']-bn['rmse'])/bo['rmse'];impa=100*(ba['rmse']-na['rmse'])/ba['rmse']
    text=f'''# Urumqi DTR-triggered signed-skew HTEMP\n\n- Formal trigger from calibration only: **DTR > {DTRC:.1f} C**\n- `beta_rise = {brc:.4f} C/C-excess`\n- `beta_fall = {bfc:.4f} C/C-excess`\n- Calibration affected points: rise={nr}, fall={nf}\n\nThe rising correction is sign-changing by construction: positive in early warming, negative in late warming, and zero at Tmin, the mid-rise crossing, and Tmax. The falling correction is negative in the interior and zero at Tmax and sunset.\n\n## Independent validation 2017-2024\n\n| Scope | Official RMSE | M6 RMSE | Improvement | Official Bias | M6 Bias | Official R2 | M6 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {ba['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {ba['mbe']:.4f} | {na['mbe']:.4f} | {ba['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {bo['rmse']:.4f} | {bn['rmse']:.4f} | {imp:.2f}% | {bo['mbe']:.4f} | {bn['mbe']:.4f} | {bo['r2']:.4f} | {bn['r2']:.4f} |\n\nDecision: retain only if validation improvement is competitive with the previous 9.07% exploratory shoulder model while coefficients remain interpretable and no low-DTR weather is changed.\n'''
    README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
