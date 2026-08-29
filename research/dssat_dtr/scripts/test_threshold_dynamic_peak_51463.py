#!/usr/bin/env python3
"""Test Urumqi-local DTR-threshold mechanisms for the DSSAT HTEMP hot shoulder.

Models are activated only when DTR > 14.5 C:
M0: official HTEMP A=2, B=2.2, C=1.
M1: dynamic A = max(0, 2 - gamma*(DTR-14.5)).
M2: post-peak shoulder correction with analytically fitted alpha.
M3: dynamic A plus shoulder correction, alpha fitted conditionally.

Calibration 2000-2016 May-Sep; independent validation 2017-2024 May-Sep.
No crop variables are used and DTR<=14.5 C is left exactly unchanged.
"""
from __future__ import annotations
import csv, math, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed_51463'
INFILE=DATA/'htemp_pointwise_2000_2024.csv'
OUT=DATA/'dynamic_peak_model_comparison.csv'
HOUR=DATA/'dynamic_peak_validation_by_hour.csv'
DTR=DATA/'dynamic_peak_validation_by_dtr.csv'
README=DATA/'README_DYNAMIC_PEAK_TEST.md'
DTRC=14.5; B=2.2; C=1.0; PI=3.14159

def mean(x): return statistics.mean(x) if x else float('nan')
def metric(rows,predfun):
    obs=[]; pred=[]
    for r in rows:
        obs.append(float(r['obs_c'])); pred.append(predfun(r))
    e=[p-o for p,o in zip(pred,obs)]
    rmse=math.sqrt(mean([z*z for z in e])); mae=mean([abs(z) for z in e]); mbe=mean(e)
    mo,mp=mean(obs),mean(pred); so=sum((x-mo)**2 for x in obs); sp=sum((x-mp)**2 for x in pred)
    rr=sum((o-mo)*(p-mp) for o,p in zip(obs,pred))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan')
    return {'n':len(rows),'rmse':rmse,'mae':mae,'mbe':mbe,'r2':rr*rr}

def htemp(r,A):
    hs=float(r['solar_hour']); tmax=float(r['tmax_ghcn_c']); tmin=float(r['tmin_ghcn_c'])
    dayl=float(r['dayl_h']); snup=float(r['snup_solar_h']); sndn=float(r['sndn_solar_h'])
    tmin_time=snup+C; tmax_time=tmin_time+dayl/2.0+A
    t=0.5*PI*(sndn-tmin_time)/(tmax_time-tmin_time)
    tsndn=tmin+(tmax-tmin)*math.sin(t)
    tmini=(tmin-tsndn*math.exp(-B))/(1.0-math.exp(-B))
    hdecay=24.0+C-dayl
    if hs>=snup+C and hs<=sndn:
        t=0.5*PI*(hs-tmin_time)/(tmax_time-tmin_time)
        return tmin+(tmax-tmin)*math.sin(t)
    if hs<snup+C: t=24.0+hs-sndn
    else: t=hs-sndn
    return tmini+(tsndn-tmini)*math.exp(-B*t/hdecay)

def adyn(r,gamma):
    d=float(r['formal_dtr_c'])
    return 2.0 if d<=DTRC else max(0.0,2.0-gamma*(d-DTRC))

def shoulder_x(r,A):
    d=float(r['formal_dtr_c'])
    if d<=DTRC:return 0.0
    hs=float(r['solar_hour']); snup=float(r['snup_solar_h']); sndn=float(r['sndn_solar_h']); dayl=float(r['dayl_h'])
    tpeak=snup+C+dayl/2.0+A
    if hs<=tpeak or hs>=sndn or sndn<=tpeak:return 0.0
    u=(hs-tpeak)/(sndn-tpeak)
    return (d-DTRC)*4.0*u*(1.0-u)

def fit_alpha(rows,basepred,Afun):
    num=0.0; den=0.0
    for r in rows:
        x=shoulder_x(r,Afun(r)); e=basepred(r)-float(r['obs_c'])
        num+=x*e; den+=x*x
    return max(0.0,num/den) if den>0 else 0.0

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
                r['year']=int(r['solar_date'][:4]); rows.append(r)
    cal=[r for r in rows if r['year']<=2016]; val=[r for r in rows if r['year']>=2017]
    cal_hi=[r for r in cal if float(r['formal_dtr_c'])>=15]

    # M1 gamma: balanced normalized RMSE all/high.
    base_all=metric(cal,lambda r:htemp(r,2.0))['rmse']; base_hi=metric(cal_hi,lambda r:htemp(r,2.0))['rmse']
    bestg=None
    for i in range(0,401):
        g=i/200.0 # 0..2 step .005
        pf=lambda r,g=g: htemp(r,adyn(r,g))
        ma=metric(cal,pf)['rmse']; mh=metric(cal_hi,pf)['rmse']
        score=.5*ma/base_all+.5*mh/base_hi
        if bestg is None or score<bestg[0]:bestg=(score,g)
    gamma=bestg[1]

    # M2 analytic alpha with official A.
    p0=lambda r:htemp(r,2.0)
    alpha_off=fit_alpha(cal,p0,lambda r:2.0)
    p2=lambda r: p0(r)-alpha_off*shoulder_x(r,2.0)

    # M3 dynamic A + analytic shoulder alpha.
    p1=lambda r:htemp(r,adyn(r,gamma))
    alpha_dyn=fit_alpha(cal,p1,lambda r:adyn(r,gamma))
    p3=lambda r:p1(r)-alpha_dyn*shoulder_x(r,adyn(r,gamma))

    models=[('M0_OFFICIAL',p0),('M1_DYNAMIC_A',p1),('M2_POSTPEAK',p2),('M3_DYNAMIC_A_POSTPEAK',p3)]
    groups=[('May-Sep',val),('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
    rec=[]
    for name,pf in models:
        for gl,rs in groups:
            m=metric(rs,pf); m.update({'model':name,'group':gl}); rec.append(m)
    fields=['model','group','n','rmse','mae','mbe','r2']
    with OUT.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r[k] for k in fields} for r in rec])

    hrs=[]
    for name,pf in models:
        for h in [11,12,14,15,17,18,20,23]:
            rs=[r for r in val if int(float(r['solar_hour']))==h]
            m=metric(rs,pf) if rs else {'n':0,'rmse':'','mae':'','mbe':'','r2':''}
            m.update({'model':name,'solar_hour':h});hrs.append(m)
    hf=['model','solar_hour','n','rmse','mae','mbe','r2']
    with HOUR.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=hf);w.writeheader();w.writerows([{k:r[k] for k in hf} for r in hrs])

    dr=[]
    for name,pf in models:
        for b in ['<10','10-<15','15-<20','>=20']:
            rs=[r for r in val if dtrbin(float(r['formal_dtr_c']))==b]
            m=metric(rs,pf);m.update({'model':name,'dtr_bin':b});dr.append(m)
    df=['model','dtr_bin','n','rmse','mae','mbe','r2']
    with DTR.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=df);w.writeheader();w.writerows([{k:r[k] for k in df} for r in dr])

    mm={(r['model'],r['group']):r for r in rec}; base=mm[('M0_OFFICIAL','DTR>=15')]
    lines=['# Urumqi DTR-threshold hot-shoulder mechanism test','',f'- Fixed local threshold: **{DTRC:.1f} C**',f'- Fitted dynamic-A gamma: **{gamma:.3f} h per C excess DTR**',f'- Analytic post-peak alpha with official A: **{alpha_off:.3f}**',f'- Analytic post-peak alpha after dynamic A: **{alpha_dyn:.3f}**','','## Independent validation 2017-2024, DTR>=15 C','','| Model | RMSE | Improvement | MAE | Bias | R2 |','|---|---:|---:|---:|---:|---:|']
    for name,_ in models:
        m=mm[(name,'DTR>=15')]; imp=100*(base['rmse']-m['rmse'])/base['rmse']
        lines.append(f"| {name} | {m['rmse']:.4f} | {imp:.2f}% | {m['mae']:.4f} | {m['mbe']:.4f} | {m['r2']:.4f} |")
    lines += ['','## Scientific decision','','M1 tests whether high-DTR days need a DTR-dependent peak-delay parameter. M2 tests excessive post-peak persistence alone. M3 tests whether both mechanisms are complementary. DTR<=14.5 C remains identical to official DSSAT in all modified models.']
    README.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))
if __name__=='__main__':main()
