#!/usr/bin/env python3
"""Fit a Urumqi-specific DTR-triggered asymmetric curvature correction for DSSAT HTEMP.

Formal model-development rule:
- DTR threshold is fixed from the 2000-2016 calibration-period breakpoint diagnosis,
  not from the full 2000-2024 record. We use DTRc=14.8 C (calibration-period
  AM-PM asymmetry breakpoint).
- 2017-2024 is untouched independent validation.

Mechanism:
For DTR <= DTRc, retain official DSSAT HTEMP exactly.
For DTR > DTRc, preserve the original DSSAT anchors and alter only daytime curvature:

Rising branch (Tmin-time -> modeled Tmax):
  F = (T_PL - Tmin)/(Tmax-Tmin)
  p_rise = exp(-k_rise * (DTR-DTRc))
  T_new = Tmin + (Tmax-Tmin) * F**p_rise

Falling branch (modeled Tmax -> sunset):
  G = (T_PL - T_sunset)/(Tmax-T_sunset)
  p_fall = exp(+k_fall * (DTR-DTRc))
  T_new = T_sunset + (Tmax-T_sunset) * G**p_fall

Thus rising curvature may warm the cold-biased morning (p_rise<1), while falling
curvature narrows the overly warm afternoon shoulder (p_fall>1). Tmin, Tmax and
sunset temperature remain exact anchors. Only two fitted parameters are added.
"""
from __future__ import annotations
import csv, math, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed_51463'
INFILE=DATA/'htemp_pointwise_2000_2024.csv'
README=DATA/'README_ASYMMETRIC_POWER_HTEMP.md'
PARAM_OUT=DATA/'asymmetric_power_parameters.csv'
VAL_OUT=DATA/'asymmetric_power_validation.csv'
DTR_OUT=DATA/'asymmetric_power_validation_by_dtr.csv'
HOUR_OUT=DATA/'asymmetric_power_validation_by_hour.csv'

DTRC=14.8  # calibration-period asymmetry-gap breakpoint
A=2.0
C=1.0


def mean(x): return statistics.mean(x) if x else float('nan')
def clip(x,a=0.0,b=1.0): return min(max(x,a),b)

def t_sunset(r):
    tmin=float(r['tmin_ghcn_c']); tmax=float(r['tmax_ghcn_c'])
    snup=float(r['snup_solar_h']); sndn=float(r['sndn_solar_h']); dayl=float(r['dayl_h'])
    tmin_time=snup+C; tpeak=tmin_time+dayl/2.0+A
    theta=0.5*math.pi*(sndn-tmin_time)/(tpeak-tmin_time)
    return tmin+(tmax-tmin)*math.sin(theta)

def branch_info(r):
    d=float(r['formal_dtr_c']); hs=float(r['solar_hour'])
    if d<=DTRC:return 'none',0.0,0.0
    snup=float(r['snup_solar_h']); sndn=float(r['sndn_solar_h']); dayl=float(r['dayl_h'])
    tmin_time=snup+C; tpeak=tmin_time+dayl/2.0+A
    if hs<tmin_time or hs>sndn:return 'none',0.0,0.0
    pred=float(r['pred_c']); tmin=float(r['tmin_ghcn_c']); tmax=float(r['tmax_ghcn_c'])
    ex=d-DTRC
    if hs<=tpeak:
        den=tmax-tmin
        if abs(den)<1e-9:return 'none',0.0,0.0
        frac=clip((pred-tmin)/den)
        return 'rise',ex,frac
    ts=t_sunset(r); den=tmax-ts
    if abs(den)<1e-9:return 'none',0.0,0.0
    frac=clip((pred-ts)/den)
    return 'fall',ex,frac

def pred_new(r,kr,kf):
    branch,ex,frac=branch_info(r)
    if branch=='none':return float(r['pred_c'])
    tmin=float(r['tmin_ghcn_c']);tmax=float(r['tmax_ghcn_c'])
    if branch=='rise':
        p=math.exp(-kr*ex)
        return tmin+(tmax-tmin)*(frac**p)
    ts=t_sunset(r); p=math.exp(kf*ex)
    return ts+(tmax-ts)*(frac**p)

def metric(rows,pf):
    obs=[float(r['obs_c']) for r in rows]; pred=[pf(r) for r in rows]
    if not rows:return {'n':0,'rmse':float('nan'),'mae':float('nan'),'mbe':float('nan'),'r2':float('nan')}
    e=[p-o for p,o in zip(pred,obs)]
    rm=math.sqrt(mean([z*z for z in e])); ma=mean([abs(z) for z in e]); mb=mean(e)
    mo,mp=mean(obs),mean(pred); so=sum((x-mo)**2 for x in obs); sp=sum((x-mp)**2 for x in pred)
    rr=sum((o-mo)*(p-mp) for o,p in zip(obs,pred))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan')
    return {'n':len(rows),'rmse':rm,'mae':ma,'mbe':mb,'r2':rr*rr}

def fit_one(rows,branch,kmax,step):
    affected=[r for r in rows if branch_info(r)[0]==branch]
    best=None
    n=int(round(kmax/step))
    for i in range(n+1):
        k=i*step
        if branch=='rise': pf=lambda r,k=k:pred_new(r,k,0.0)
        else: pf=lambda r,k=k:pred_new(r,0.0,k)
        sse=sum((pf(r)-float(r['obs_c']))**2 for r in affected)
        rec=(sse,k)
        if best is None or rec[0]<best[0]:best=rec
    return best[1],len(affected),best[0]

def dtrbin(d):
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
                r['year']=int(r['solar_date'][:4]); rows.append(r)
    cal=[r for r in rows if r['year']<=2016]
    val=[r for r in rows if r['year']>=2017]

    # Separate branch SSEs are independent because the branches do not overlap.
    kr,nrise,sser=fit_one(cal,'rise',0.30,0.001)
    kf,nfall,ssef=fit_one(cal,'fall',0.60,0.001)

    with PARAM_OUT.open('w',newline='',encoding='utf-8-sig') as f:
        fields=['dtr_threshold_c','k_rise','k_fall','n_cal_rise','n_cal_fall','cal_sse_rise','cal_sse_fall']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerow({
            'dtr_threshold_c':DTRC,'k_rise':kr,'k_fall':kf,'n_cal_rise':nrise,'n_cal_fall':nfall,
            'cal_sse_rise':sser,'cal_sse_fall':ssef})

    models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M5_ASYM_POWER',lambda r:pred_new(r,kr,kf))]
    groups=[
        ('May-Sep',val),
        ('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),
        ('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),
        ('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18]),
    ]
    rec=[]
    for name,pf in models:
        for gl,rs in groups:
            m=metric(rs,pf);m.update({'model':name,'group':gl});rec.append(m)
    fields=['model','group','n','rmse','mae','mbe','r2']
    with VAL_OUT.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r[k] for k in fields} for r in rec])

    dr=[]
    for name,pf in models:
        for b in ['<10','10-<15','15-<18','18-<20','>=20']:
            rs=[r for r in val if dtrbin(float(r['formal_dtr_c']))==b]
            m=metric(rs,pf);m.update({'model':name,'dtr_bin':b});dr.append(m)
    with DTR_OUT.open('w',newline='',encoding='utf-8-sig') as f:
        ff=['model','dtr_bin','n','rmse','mae','mbe','r2'];w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerows([{k:r[k] for k in ff} for r in dr])

    hr=[]
    for name,pf in models:
        for h in [5,8,9,11,12,14,15,17,18,20,23]:
            rs=[r for r in val if int(float(r['solar_hour']))==h]
            m=metric(rs,pf);m.update({'model':name,'solar_hour':h});hr.append(m)
    with HOUR_OUT.open('w',newline='',encoding='utf-8-sig') as f:
        ff=['model','solar_hour','n','rmse','mae','mbe','r2'];w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerows([{k:r[k] for k in ff} for r in hr])

    mm={(r['model'],r['group']):r for r in rec}
    bo=mm[('M0_OFFICIAL','DTR>=15')]; bn=mm[('M5_ASYM_POWER','DTR>=15')]
    ba=mm[('M0_OFFICIAL','May-Sep')]; na=mm[('M5_ASYM_POWER','May-Sep')]
    low0=mm[('M0_OFFICIAL','DTR<14.8')]; low1=mm[('M5_ASYM_POWER','DTR<14.8')]
    imp=100*(bo['rmse']-bn['rmse'])/bo['rmse']; impall=100*(ba['rmse']-na['rmse'])/ba['rmse']
    text=f'''# Urumqi calibration-only DTR asymmetric-curvature HTEMP\n\n## Formal threshold\n\n- DTR trigger = **{DTRC:.1f} C**, taken only from the 2000-2016 calibration-period AM-PM asymmetry breakpoint.\n- 2017-2024 was not used to determine the threshold or curvature parameters.\n\n## Fitted curvature response\n\n- `k_rise = {kr:.3f}`\n- `k_fall = {kf:.3f}`\n- calibration affected points: rising={nrise}, falling={nfall}\n\nFor DTR>DTRc, rising and falling normalized temperature fractions are transformed by DTR-dependent powers. Tmin, modeled Tmax and modeled sunset temperature remain exact anchors.\n\n## Independent validation 2017-2024\n\n| Scope | Official RMSE | M5 RMSE | Improvement | Official Bias | M5 Bias | Official R2 | M5 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {ba['rmse']:.4f} | {na['rmse']:.4f} | {impall:.2f}% | {ba['mbe']:.4f} | {na['mbe']:.4f} | {ba['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {bo['rmse']:.4f} | {bn['rmse']:.4f} | {imp:.2f}% | {bo['mbe']:.4f} | {bn['mbe']:.4f} | {bo['r2']:.4f} | {bn['r2']:.4f} |\n| DTR<14.8 C | {low0['rmse']:.4f} | {low1['rmse']:.4f} | 0.00% by construction | {low0['mbe']:.4f} | {low1['mbe']:.4f} | {low0['r2']:.4f} | {low1['r2']:.4f} |\n\n## Decision criterion\n\nThis structural form is preferred over additive shoulder subtraction only if it matches or exceeds the ~9% high-DTR RMSE improvement while avoiding very large empirical coefficients and preserving anchor continuity.\n'''
    README.write_text(text,encoding='utf-8');print(text)

if __name__=='__main__': main()
