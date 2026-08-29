#!/usr/bin/env python3
"""Diagnose whether DSSAT HTEMP sunset temperature itself is biased at dense Diwopu.

Uses only >=20-hour/day NOAA 51463599999 days and existing NASA POWER SRAD.
For each May-Sep day, compare official Parton-Logan temperature exactly at SNDN
against the real observation closest to SNDN (within 45 min).

The key mechanism test is whether sunset-anchor error increases with
X = max(0, DTR-14.8) * DSSAT_CLOUDS.
A one-parameter through-origin slope is fitted on 2000-2016 only and evaluated
without refitting on 2017-2024. This is a diagnosis, not yet a source correction.
"""
import csv, io, math, statistics, urllib.request
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import analyze_dense_514635_shape as ds

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'processed_514635'
SRAD_FILE=OUT/'diwopu_dtr_srad_daily.csv'
DAILY=OUT/'dense_sunset_anchor_daily.csv'
SUMMARY=OUT/'dense_sunset_anchor_summary.csv'
README=OUT/'README_DENSE_SUNSET_ANCHOR.md'
ST='51463599999';LAT=43.907106;DTRC=14.8
PI=3.14159;RAD=PI/180.;S0N=1368.;AMTRCS=.77

def mean(x): return statistics.mean(x) if x else float('nan')
def rmse(x): return math.sqrt(mean([v*v for v in x])) if x else float('nan')
def pearson(x,y):
    if len(x)<3:return float('nan')
    mx,my=mean(x),mean(y);sx=sum((a-mx)**2 for a in x);sy=sum((b-my)**2 for b in y)
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(sx*sy) if sx>0 and sy>0 else float('nan')
def clouds(date,srad):
    doy=date.timetuple().tm_yday;dl,su,sd=ds.daylen(doy)
    dec=-23.45*math.cos(2*PI*(doy+10.)/365.)
    ss=math.sin(RAD*dec)*math.sin(RAD*LAT);cc=math.cos(RAD*dec)*math.cos(RAD*LAT)
    z=ss/cc if abs(cc)>1e-12 else 0.;z=min(max(z,-1.),1.)
    dsinb=3600.*(dl*ss+24./PI*cc*math.sqrt(max(0.,1.-z*z)))
    sclear=AMTRCS*S0N*dsinb*1e-6
    return min(max(1.-srad/sclear,0.),1.) if sclear>0 else 0.,sclear
def load_srad():
    out={}
    with SRAD_FILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):out[r['date']]=float(r['srad'])
    return out
def load_dense():
    rec=[]
    for y in range(2000,2025):
        url=f'https://www.ncei.noaa.gov/data/global-hourly/access/{y}/{ST}.csv'
        req=urllib.request.Request(url,headers={'User-Agent':'DSSAT-DTR-research/1.0'})
        with urllib.request.urlopen(req,timeout=60) as rr:text=rr.read().decode('utf-8-sig',errors='replace')
        for r in csv.DictReader(io.StringIO(text)):
            t,q=ds.parse_tmp(r.get('TMP',''))
            if t is None or q in ds.BAD:continue
            try:d=datetime.fromisoformat(r['DATE'].replace('Z',''))
            except:continue
            sol=ds.solar(d+timedelta(hours=8));slot=sol.replace(minute=0,second=0,microsecond=0);rec.append((slot,sol,t))
    g=defaultdict(list)
    for slot,sol,t in rec:g[slot].append((sol,t))
    hourly=[]
    for slot,vals in g.items():
        sol,t=min(vals,key=lambda z:abs((z[0]-slot).total_seconds()));hourly.append((sol,t))
    bd=defaultdict(list)
    for sol,t in hourly:bd[sol.date()].append((sol,t))
    return bd
def main():
    srad=load_srad();bd=load_dense();rows=[]
    for date,vals in sorted(bd.items()):
        if date.isoformat() not in srad or not 5<=date.month<=9:continue
        vals=sorted(vals);hours={v[0].hour for v in vals}
        if len(hours)<20:continue
        temps=[v[1] for v in vals];tx=max(temps);tn=min(temps);dtr=tx-tn;dl,su,sd=ds.daylen(date.timetuple().tm_yday)
        # nearest real report to astronomical/DSSAT sunset
        target=datetime.combine(date,datetime.min.time())+timedelta(hours=sd)
        obs_dt,obs_t=min(vals,key=lambda z:abs((z[0]-target).total_seconds()))
        gap=abs((obs_dt-target).total_seconds())/3600.
        if gap>.75:continue
        ts=ds.htemp(sd,tx,tn,dl,su,sd)
        cl,sc=clouds(date,srad[date.isoformat()]);x=max(0.,dtr-DTRC)*cl;err=ts-obs_t
        rows.append({'date':date.isoformat(),'year':date.year,'dtr_c':dtr,'srad':srad[date.isoformat()],'clouds':cl,'sclear':sc,'sndn_h':sd,'obs_sunset_h':obs_dt.hour+obs_dt.minute/60+obs_dt.second/3600,'obs_gap_h':gap,'tmax_c':tx,'tmin_c':tn,'official_ts_c':ts,'observed_near_sunset_c':obs_t,'sunset_error_c':err,'dtr_cloud_x':x})
    fields=list(rows[0].keys())
    with DAILY.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    cal=[r for r in rows if r['year']<=2016 and r['dtr_c']>DTRC];val=[r for r in rows if r['year']>=2017 and r['dtr_c']>DTRC]
    sx2=sum(r['dtr_cloud_x']**2 for r in cal);sxy=sum(r['dtr_cloud_x']*r['sunset_error_c'] for r in cal);alpha=max(0.,sxy/sx2) if sx2>0 else 0.
    def assess(rs):
        raw=[r['sunset_error_c'] for r in rs];corr=[r['sunset_error_c']-alpha*r['dtr_cloud_x'] for r in rs]
        return {'n':len(rs),'mean_dtr':mean([r['dtr_c'] for r in rs]),'mean_clouds':mean([r['clouds'] for r in rs]),'raw_bias':mean(raw),'raw_rmse':rmse(raw),'corrected_bias':mean(corr),'corrected_rmse':rmse(corr),'r_error_vs_dtrcloud':pearson([r['dtr_cloud_x'] for r in rs],[r['sunset_error_c'] for r in rs])}
    out=[]
    for name,rs in [('Calibration_2000_2016',cal),('Validation_2017_2024',val)]:
        a=assess(rs);a.update({'split':name,'alpha_from_calibration':alpha});out.append(a)
    # fixed CLOUDS tertiles from calibration high-DTR days
    cs=sorted(r['clouds'] for r in cal);q1=cs[len(cs)//3];q2=cs[2*len(cs)//3]
    for lab,lo,hi in [('LowCloud',-1,q1),('MidCloud',q1,q2),('HighCloud',q2,2)]:
        rs=[r for r in val if lo<=r['clouds']<hi]
        a=assess(rs);a.update({'split':'Validation_'+lab,'alpha_from_calibration':alpha});out.append(a)
    with SUMMARY.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
    va=out[1];gain=100*(va['raw_rmse']-va['corrected_rmse'])/va['raw_rmse'] if va['raw_rmse'] else float('nan')
    text=f'''# Dense Diwopu sunset-anchor mechanism diagnosis\n\n- May-Sep dense days with a real observation within 45 min of DSSAT sunset: **{len(rows)}**.\n- High-DTR calibration days (>14.8 C): **{len(cal)}**.\n- High-DTR validation days: **{len(val)}**.\n- Calibration-only slope for `TS error = alpha * (DTR-14.8)+ * CLOUDS`: **alpha={alpha:.4f} C per C-DTR-excess per unit CLOUDS**.\n\n## High-DTR sunset-anchor error\n| Split | N | Raw Bias | Raw RMSE | Corrected Bias | Corrected RMSE | r(error, DTRxCLOUDS) |\n|---|---:|---:|---:|---:|---:|---:|\n'''
    for r in out:text+=f"| {r['split']} | {r['n']} | {r['raw_bias']:+.3f} | {r['raw_rmse']:.3f} | {r['corrected_bias']:+.3f} | {r['corrected_rmse']:.3f} | {r['r_error_vs_dtrcloud']:.3f} |\n"
    text+=f'''\nIndependent validation RMSE gain from the calibration-only sunset-anchor relation: **{gain:.2f}%**.\n\nInterpretation rule: changing the DSSAT sunset anchor is justified only if the raw high-DTR sunset bias is materially positive, the DTRxCLOUDS relationship persists in validation, and the frozen calibration slope reduces validation sunset RMSE without inducing a large negative bias.\n'''
    README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
