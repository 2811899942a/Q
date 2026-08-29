#!/usr/bin/env python3
"""Fit a calibration-only three-lobe DTR-adaptive HTEMP correction for Urumqi.

Trigger DTRc=14.8 C comes from the 2000-2016 calibration-period asymmetry breakpoint.
2017-2024 remains independent validation.

For DTR>DTRc, define rising normalized time x=(t-tmin_time)/(tpeak-tmin_time):
  B_morning = x*(1-x)^4 / 0.08192        (peak near x=0.2)
  B_prepeak = x^4*(1-x) / 0.08192        (peak near x=0.8)
and falling normalized time u=(t-tpeak)/(sunset-tpeak):
  B_fall = 4*u*(1-u)                     (peak near u=0.5)

Correction:
  T_new = T_PL + beta_m*excess*B_morning - beta_p*excess*B_prepeak
          - beta_f*excess*B_fall
where excess=max(0,DTR-DTRc).

The three coefficients directly represent maximum degC correction per degC excess DTR.
All basis functions are zero at their physical anchors, preserving modeled Tmin, Tmax,
and sunset continuity. beta_m,beta_p,beta_f are constrained nonnegative and fitted only
on 2000-2016 May-Sep observations.
"""
from __future__ import annotations
import csv, math, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed_51463'
INFILE=DATA/'htemp_pointwise_2000_2024.csv'
README=DATA/'README_THREE_LOBE_HTEMP.md'
PARAM=DATA/'three_lobe_parameters.csv'
VAL=DATA/'three_lobe_validation.csv'
DTR=DATA/'three_lobe_validation_by_dtr.csv'
HOUR=DATA/'three_lobe_validation_by_hour.csv'
DTRC=14.8; A=2.0; C=1.0; NORM=0.08192

def mean(x): return statistics.mean(x) if x else float('nan')
def bases(r):
    d=float(r['formal_dtr_c']);hs=float(r['solar_hour'])
    if d<=DTRC:return (0.0,0.0,0.0)
    sn=float(r['snup_solar_h']);sd=float(r['sndn_solar_h']);dl=float(r['dayl_h'])
    t0=sn+C;tp=t0+dl/2+A;ex=d-DTRC
    bm=bp=bf=0.0
    if t0<hs<tp:
        x=(hs-t0)/(tp-t0)
        bm=ex*(x*(1-x)**4/NORM)
        bp=ex*(x**4*(1-x)/NORM)
    elif tp<hs<sd:
        u=(hs-tp)/(sd-tp)
        bf=ex*4*u*(1-u)
    return bm,bp,bf

def nnls2(cal):
    # Error_new = e + bm*beta_m - bp*beta_p. Solve for coefficients c1=beta_m, c2=beta_p
    # with design z1=bm, z2=-bp and enforce c>=0.
    s11=s22=s12=t1=t2=0.0
    for r in cal:
        bm,bp,_=bases(r);z1=bm;z2=-bp;e=float(r['pred_c'])-float(r['obs_c'])
        s11+=z1*z1;s22+=z2*z2;s12+=z1*z2;t1+=z1*e;t2+=z2*e
    den=s11*s22-s12*s12
    if abs(den)>1e-12:
        c1=-(t1*s22-t2*s12)/den;c2=-(-t1*s12+t2*s11)/den
    else:c1=c2=0.0
    candidates=[]
    if c1>=0 and c2>=0:candidates.append((c1,c2))
    c1_only=max(0.0,-t1/s11) if s11>0 else 0.0
    c2_only=max(0.0,-t2/s22) if s22>0 else 0.0
    candidates += [(c1_only,0.0),(0.0,c2_only),(0.0,0.0)]
    def sse(c):
        a,b=c;return sum((float(r['pred_c'])-float(r['obs_c'])+a*bases(r)[0]-b*bases(r)[1])**2 for r in cal)
    return min(candidates,key=sse)

def fit_fall(cal):
    s=t=0.0
    for r in cal:
        _,_,bf=bases(r);e=float(r['pred_c'])-float(r['obs_c']);s+=bf*bf;t+=bf*e
    return max(0.0,t/s) if s>0 else 0.0

def pred(r,bmcoef,bpcoef,bfcoef):
    bm,bp,bf=bases(r)
    return float(r['pred_c'])+bmcoef*bm-bpcoef*bp-bfcoef*bf

def metric(rows,pf):
    if not rows:return {'n':0,'rmse':float('nan'),'mae':float('nan'),'mbe':float('nan'),'r2':float('nan')}
    o=[float(r['obs_c']) for r in rows];p=[pf(r) for r in rows];e=[b-a for a,b in zip(o,p)]
    rm=math.sqrt(mean([x*x for x in e]));ma=mean([abs(x) for x in e]);mb=mean(e)
    mo,mp=mean(o),mean(p);so=sum((x-mo)**2 for x in o);sp=sum((x-mp)**2 for x in p)
    rr=sum((a-mo)*(b-mp) for a,b in zip(o,p))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan')
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
            if int(r['month']) in [5,6,7,8,9]:r['year']=int(r['solar_date'][:4]);rows.append(r)
    cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017]
    bm,bp=nnls2(cal);bf=fit_fall(cal)
    with PARAM.open('w',newline='',encoding='utf-8-sig') as f:
        ff=['dtr_threshold_c','beta_morning','beta_prepeak','beta_fall'];w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerow({'dtr_threshold_c':DTRC,'beta_morning':bm,'beta_prepeak':bp,'beta_fall':bf})
    models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M7_THREE_LOBE',lambda r:pred(r,bm,bp,bf))]
    groups=[('May-Sep',val),('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
    rec=[]
    for name,pf in models:
        for gl,rs in groups:m=metric(rs,pf);m.update({'model':name,'group':gl});rec.append(m)
    ff=['model','group','n','rmse','mae','mbe','r2']
    with VAL.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerows([{k:r[k] for k in ff} for r in rec])
    dr=[]
    for name,pf in models:
        for b in ['<10','10-<15','15-<18','18-<20','>=20']:
            rs=[r for r in val if dbin(float(r['formal_dtr_c']))==b];m=metric(rs,pf);m.update({'model':name,'dtr_bin':b});dr.append(m)
    ff2=['model','dtr_bin','n','rmse','mae','mbe','r2']
    with DTR.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=ff2);w.writeheader();w.writerows([{k:r[k] for k in ff2} for r in dr])
    hr=[]
    for name,pf in models:
        for h in [5,8,9,11,12,14,15,17,18,20,23]:
            rs=[r for r in val if int(float(r['solar_hour']))==h];m=metric(rs,pf);m.update({'model':name,'solar_hour':h});hr.append(m)
    ff3=['model','solar_hour','n','rmse','mae','mbe','r2']
    with HOUR.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=ff3);w.writeheader();w.writerows([{k:r[k] for k in ff3} for r in hr])
    mm={(r['model'],r['group']):r for r in rec};bo=mm[('M0_OFFICIAL','DTR>=15')];bn=mm[('M7_THREE_LOBE','DTR>=15')];ba=mm[('M0_OFFICIAL','May-Sep')];na=mm[('M7_THREE_LOBE','May-Sep')]
    imp=100*(bo['rmse']-bn['rmse'])/bo['rmse'];impa=100*(ba['rmse']-na['rmse'])/ba['rmse']
    text=f'''# Urumqi calibration-only three-lobe DTR-adaptive HTEMP\n\n- Trigger: **DTR > {DTRC:.1f} C** (calibration period only)\n- Morning warming coefficient: **beta_m={bm:.4f} C/C-excess**\n- Late pre-peak shoulder cooling coefficient: **beta_p={bp:.4f} C/C-excess**\n- Post-peak persistence cooling coefficient: **beta_f={bf:.4f} C/C-excess**\n\nAll three terms vanish at physical branch anchors; low-DTR weather is unchanged.\n\n## Independent validation 2017-2024\n\n| Scope | Official RMSE | M7 RMSE | Improvement | Official Bias | M7 Bias | Official R2 | M7 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {ba['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {ba['mbe']:.4f} | {na['mbe']:.4f} | {ba['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {bo['rmse']:.4f} | {bn['rmse']:.4f} | {imp:.2f}% | {bo['mbe']:.4f} | {bn['mbe']:.4f} | {bo['r2']:.4f} | {bn['r2']:.4f} |\n\nRetain only if it improves on the 9.07% exploratory two-sided shoulder benchmark with stable, interpretable coefficients.\n'''
    README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
