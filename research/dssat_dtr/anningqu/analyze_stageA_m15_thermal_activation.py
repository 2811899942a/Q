#!/usr/bin/env python3
"""Quantify frozen M15 activation over the five public Anningqu sowing-harvest windows."""
from pathlib import Path
from datetime import date, timedelta
import csv, math, statistics

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'anningqu'/'formal_ghcn_rain'
OUT=ROOT/'data'/'anningqu'/'stageA_thermal_activation'
OUT.mkdir(parents=True,exist_ok=True)
LAT=43.95; PI=3.14159; RAD=PI/180.; SC=1368.; A=2.; B=2.2; C=1.; ALPHA=7.8094; DTRC=14.8
windows={'A':((4,21),(9,4)),'B':((4,26),(9,7)),'C':((5,6),(9,15)),'D':((5,16),(9,27)),'E':((5,26),(10,13))}

def daygeom(d,srad):
 doy=d.timetuple().tm_yday; dec=-23.45*math.cos(2*PI*(doy+10)/365.); soc=math.tan(RAD*dec)*math.tan(RAD*LAT);soc=max(-1,min(1,soc));dayl=max(0,min(24,12+24*math.asin(soc)/PI));sn=12-dayl/2;sd=12+dayl/2
 ss=math.sin(RAD*dec)*math.sin(RAD*LAT);cc=math.cos(RAD*dec)*math.cos(RAD*LAT);q=ss/cc if abs(cc)>1e-12 else 0;q=max(-1,min(1,q));ds=3600*(dayl*ss+24/PI*cc*math.sqrt(max(0,1-q*q)));s0d=SC*ds;sclear=.77*s0d*1e-6;cloud=max(0,min(1,1-srad/sclear)) if sclear>0 else 0
 return dayl,sn,sd,cloud

def htemp(h,dayl,sn,sd,tmax,tmin):
 tminhr=sn+C;tmaxhr=tminhr+dayl/2+A;t=.5*PI*(sd-tminhr)/(tmaxhr-tminhr);ts=tmin+(tmax-tmin)*math.sin(t);eb=math.exp(-B);tmini=(tmin-ts*eb)/(1-eb);hdec=24+C-dayl
 if tminhr<=h<=sd:
  arg=.5*PI*(h-tminhr)/(tmaxhr-tminhr);return tmin+(tmax-tmin)*math.sin(arg)
 tt=24+h-sd if h<tminhr else h-sd;return tmini+(ts-tmini)*math.exp(-B*tt/hdec)

def m15(h,base,dayl,sn,sd,tmax,tmin,cloud):
 dtr=tmax-tmin
 if dtr<=DTRC or cloud<=0:return base
 tminhr=sn+C;tmaxhr=tminhr+dayl/2+A;t=.5*PI*(sd-tminhr)/(tmaxhr-tminhr);ts0=tmin+(tmax-tmin)*math.sin(t);ts1=max(tmin,ts0-ALPHA*(dtr-DTRC)*cloud)
 if h>tmaxhr and h<=sd:
  den=tmax-ts0
  if abs(den)>1e-6:
   r=max(0,min(1,(tmax-base)/den));return tmax-(tmax-ts1)*r
 elif h>sd or h<tminhr:
  eb=math.exp(-B);tmini1=(tmin-ts1*eb)/(1-eb);hdec=24+C-dayl;tt=24+h-sd if h<tminhr else h-sd;return tmini1+(ts1-tmini1)*math.exp(-B*tt/hdec)
 return base

def readw(year):
 rows=[]
 p=DATA/f'ANQH{year%100:02d}01.WTH'
 with p.open(encoding='utf-8-sig') as f:
  for line in f:
   if not line.strip() or line[0] in '*@!':continue
   q=line.split()
   if len(q)<5:continue
   code=q[0]; yy=int(code[:2]);doy=int(code[2:]);d=date(year,1,1)+timedelta(days=doy-1)
   rows.append((d,float(q[1]),float(q[2]),float(q[3])))
 return rows

allrows=[]
for year in (2021,2022):
 wx={d:(sr,tx,tn) for d,sr,tx,tn in readw(year)}
 for code,(sm,hm) in windows.items():
  start=date(year,*sm);end=date(year,*hm);d=start;nd=active=hours=0;sumdiff=0;absdiff=[];highdtr=0
  while d<=end:
   if d in wx:
    sr,tx,tn=wx[d];dayl,sn,sd,cl=daygeom(d,sr);dtr=tx-tn;nd+=1;highdtr+=dtr>DTRC;day_changed=False
    for h in range(1,25):
     t0=htemp(float(h),dayl,sn,sd,tx,tn);t1=m15(float(h),t0,dayl,sn,sd,tx,tn,cl);diff=t1-t0;sumdiff+=diff
     if abs(diff)>1e-9:hours+=1;day_changed=True;absdiff.append(abs(diff))
    active+=day_changed
   d+=timedelta(days=1)
  allrows.append({'year':year,'sowing':code,'start':start.isoformat(),'end':end.isoformat(),'n_days':nd,'high_dtr_days':highdtr,'m15_active_days':active,'changed_hours':hours,'mean_hourly_delta_c':sumdiff/(nd*24) if nd else 0,'cumulative_degree_hours_delta':sumdiff,'mean_abs_changed_hour_c':statistics.mean(absdiff) if absdiff else 0,'max_abs_hour_delta_c':max(absdiff) if absdiff else 0})

with (OUT/'anningqu_stageA_thermal_activation.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(allrows[0].keys()));w.writeheader();w.writerows(allrows)
md=['# Anningqu 2021-2022 M15 thermal activation','', 'Frozen M15 is evaluated over the public expected sowing-to-harvest windows. This is a weather/HTEMP propagation diagnostic, not crop calibration.','', '|Year|Sowing|Days|DTR>14.8 d|M15 active d|Changed h|Mean hourly ΔT (C)|Degree-hour Δ|Max hourly |ΔT| (C)|','|---:|:---:|---:|---:|---:|---:|---:|---:|---:|']
for r in allrows:md.append(f"|{r['year']}|{r['sowing']}|{r['n_days']}|{r['high_dtr_days']}|{r['m15_active_days']}|{r['changed_hours']}|{r['mean_hourly_delta_c']:.3f}|{r['cumulative_degree_hours_delta']:.1f}|{r['max_abs_hour_delta_c']:.2f}|")
md+=['',f"Across 10 crop windows, M15 activates in **{sum(r['m15_active_days'] for r in allrows)} crop-window days** and changes **{sum(r['changed_hours'] for r in allrows)} hourly states** (windows overlap, so these are scenario exposure counts, not unique calendar-day counts)."]
(OUT/'README_STAGEA_THERMAL_ACTIVATION.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print('\n'.join(md))
