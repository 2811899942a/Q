#!/usr/bin/env python3
"""Calibrate station-specific Parton-Logan A/B/C at dense Diwopu station 51463599999.

Purpose: separate ordinary station/regional parameter-transfer error from the high-DTR
structural error. A/B/C are calibrated only on all May-Sep 2000-2016 observations.
2017-2024 is untouched independent validation. High-DTR diagnostics are evaluated
only after calibration and are not included in the objective.
"""
import csv,io,math,statistics,urllib.request
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path
import numpy as np
from scipy.optimize import differential_evolution
import analyze_dense_514635_shape as ds
OUT=Path(__file__).resolve().parents[1]/'data'/'processed_514635';ST='51463599999'
def load_points():
    rec=[]
    for y in range(2000,2025):
        url=f'https://www.ncei.noaa.gov/data/global-hourly/access/{y}/{ST}.csv';req=urllib.request.Request(url,headers={'User-Agent':'DSSAT-DTR-research/1.0'})
        with urllib.request.urlopen(req,timeout=60) as rr:text=rr.read().decode('utf-8-sig',errors='replace')
        for r in csv.DictReader(io.StringIO(text)):
            t,q=ds.parse_tmp(r.get('TMP',''))
            if t is None or q in ds.BAD:continue
            try:d=datetime.fromisoformat(r['DATE'].replace('Z',''))
            except:continue
            sol=ds.solar(d+timedelta(hours=8));slot=sol.replace(minute=0,second=0,microsecond=0);rec.append((slot,sol,t))
    g=defaultdict(list)
    for slot,sol,t in rec:g[slot].append((sol,t))
    hourly=[min(v,key=lambda z:abs((z[0]-slot).total_seconds())) for slot,v in g.items()]
    bd=defaultdict(list)
    for sol,t in hourly:bd[sol.date()].append((sol,t))
    pts=[]
    for date,rs in bd.items():
        if len({z[0].hour for z in rs})<20 or not 5<=date.month<=9:continue
        vals=[z[1] for z in rs];tmax=max(vals);tmin=min(vals);dtr=tmax-tmin;dl,su,sd=ds.daylen(date.timetuple().tm_yday)
        for sol,t in rs:
            hs=sol.hour+sol.minute/60+sol.second/3600;pts.append((date.year,dtr,hs,t,tmax,tmin,dl,su,sd))
    return pts
def predict(p,arr):
    A,B,C=p;hs=arr[:,2];tmax=arr[:,4];tmin=arr[:,5];dayl=arr[:,6];snup=arr[:,7];sndn=arr[:,8];tmin_time=snup+C;tmax_time=tmin_time+dayl/2+A;theta_s=.5*np.pi*(sndn-tmin_time)/(tmax_time-tmin_time);ts=tmin+(tmax-tmin)*np.sin(theta_s);eb=np.exp(-B);tmini=(tmin-ts*eb)/(1-eb);hdecay=24+C-dayl
    out=np.empty(len(arr));day=(hs>=snup+C)&(hs<=sndn);theta=.5*np.pi*(hs[day]-tmin_time[day])/(tmax_time[day]-tmin_time[day]);out[day]=tmin[day]+(tmax[day]-tmin[day])*np.sin(theta);night=~day;tt=np.where(hs[night]<snup[night]+C,24+hs[night]-sndn[night],hs[night]-sndn[night]);out[night]=tmini[night]+(ts[night]-tmini[night])*np.exp(-B*tt/hdecay[night]);return out
def metric(arr,p):
    pred=predict(p,arr);e=pred-arr[:,3];return (float(np.sqrt(np.mean(e*e))),float(np.mean(np.abs(e))),float(np.mean(e)),float(np.corrcoef(arr[:,3],pred)[0,1]**2))
def main():
    pts=load_points();arr=np.array(pts,float);cal=arr[arr[:,0]<=2016];val=arr[arr[:,0]>=2017]
    def obj(p):return metric(cal,p)[0]
    res=differential_evolution(obj,[(0,4),(.5,5),(0,2.5)],seed=42,maxiter=30,popsize=10,tol=1e-5,polish=True,workers=1);best=res.x;off=np.array([2.,2.2,1.])
    rows=[]
    for scope,s in [('May-Sep',val),('DTR>=13',val[val[:,1]>=13]),('DTR>=14.5',val[val[:,1]>=14.5]),('DTR14.5-18',val[(val[:,1]>=14.5)&(val[:,1]<18)])]:
        for name,p in [('Official',off),('Diwopu-PL',best)]:
            m=metric(s,p);rows.append({'scope':scope,'model':name,'A':p[0],'B':p[1],'C':p[2],'n':len(s),'rmse':m[0],'mae':m[1],'bias':m[2],'r2':m[3]})
    with (OUT/'diwopu_pl_validation.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    # validation residual by hour for main high-DTR bin
    hr=[];s=val[(val[:,1]>=14.5)&(val[:,1]<18)]
    for h in range(24):
        sh=s[np.floor(s[:,2]).astype(int)%24==h]
        if len(sh)==0:continue
        for name,p in [('Official',off),('Diwopu-PL',best)]:
            m=metric(sh,p);hr.append({'solar_hour':h,'model':name,'n':len(sh),'rmse':m[0],'mae':m[1],'bias':m[2],'r2':m[3]})
    with (OUT/'diwopu_pl_highdtr_by_hour.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(hr[0].keys()));w.writeheader();w.writerows(hr)
    mp={(r['scope'],r['model']):r for r in rows};o=mp[('May-Sep','Official')];b=mp[('May-Sep','Diwopu-PL')];oh=mp[('DTR14.5-18','Official')];bh=mp[('DTR14.5-18','Diwopu-PL')]
    txt=f'''# Dense Diwopu station-specific PL calibration

- Calibration objective: all May-Sep 2000-2016 hourly observations only.
- Optimized parameters: **A={best[0]:.3f}, B={best[1]:.3f}, C={best[2]:.3f}**.
- Official parameters: A=2.0, B=2.2, C=1.0.
- Optimizer success: **{res.success}**; evaluations: **{res.nfev}**.

## Independent 2017-2024 validation
- All May-Sep RMSE: official **{o['rmse']:.3f} C** -> Diwopu-PL **{b['rmse']:.3f} C**.
- DTR 14.5-18 RMSE: official **{oh['rmse']:.3f} C** -> Diwopu-PL **{bh['rmse']:.3f} C**.
- DTR 14.5-18 Bias: official **{oh['bias']:.3f} C** -> Diwopu-PL **{bh['bias']:.3f} C**.
- DTR 14.5-18 R2: official **{oh['r2']:.3f}** -> Diwopu-PL **{bh['r2']:.3f}**.

If station-specific A/B/C substantially improves ordinary conditions but a large, time-structured high-DTR residual remains, that independently reproduces the parameter-transfer + structural-error decomposition seen at 51463.
''';(OUT/'README_DIWOPU_PL_CALIBRATION.md').write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
