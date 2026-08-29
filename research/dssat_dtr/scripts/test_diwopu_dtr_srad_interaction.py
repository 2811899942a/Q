#!/usr/bin/env python3
"""Test whether daily solar radiation adds explanatory value beyond DTR for Diwopu HTEMP error.

Rationale: DSSAT weather files already contain SRAD, but the original HTEMP reconstruction
uses Tmax/Tmin/daylength only. Dense Diwopu data show that DTR identifies an error-regime
transition but DTR alone does not determine the daily curve shape.

Data:
- NOAA 51463599999 real hourly temperature, >=20 local-solar-hour days.
- Fixed station PL parameters A=1.849, B=0.740, C=0.242 calibrated on 2000-2016.
- NASA POWER daily ALLSKY_SFC_SW_DWN and CLRSKY_SFC_SW_DWN at Diwopu, LST.

We test whether SRAD/clearness improves independent 2017-2024 prediction of daily
HTEMP RMSE beyond DTR excess alone. This is mechanism screening, not a correction model.
"""
import csv,io,json,math,statistics,urllib.request
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path
import numpy as np
import analyze_dense_514635_shape as ds

OUT=Path(__file__).resolve().parents[1]/'data'/'processed_514635';ST='51463599999';A,B,C=1.849,.740,.242;DTRC=12.8
CSVOUT=OUT/'diwopu_dtr_srad_daily.csv';MODELS=OUT/'diwopu_dtr_srad_models.csv';STRATA=OUT/'diwopu_highdtr_srad_strata.csv';README=OUT/'README_DIWOPU_DTR_SRAD.md'

def pl(hs,tmax,tmin,dayl,snup,sndn):
    tmin_time=snup+C;tpeak=tmin_time+dayl/2+A;th=.5*math.pi*(sndn-tmin_time)/(tpeak-tmin_time);ts=tmin+(tmax-tmin)*math.sin(th);eb=math.exp(-B);tmini=(tmin-ts*eb)/(1-eb);hd=24+C-dayl
    if tmin_time<=hs<=sndn:
        th=.5*math.pi*(hs-tmin_time)/(tpeak-tmin_time);return tmin+(tmax-tmin)*math.sin(th)
    tt=24+hs-sndn if hs<tmin_time else hs-sndn;return tmini+(ts-tmini)*math.exp(-B*tt/hd)
def power():
    url=('https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN'
         '&community=AG&longitude=87.474244&latitude=43.907106&start=20000101&end=20241231&format=JSON&time-standard=LST')
    req=urllib.request.Request(url,headers={'User-Agent':'DSSAT-DTR-research/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r:j=json.loads(r.read().decode())
    a=j['properties']['parameter']['ALLSKY_SFC_SW_DWN'];c=j['properties']['parameter']['CLRSKY_SFC_SW_DWN'];out={}
    for k,v in a.items():
        if v is None or float(v)<-900:continue
        cv=c.get(k)
        if cv is None or float(cv)<=0 or float(cv)<-900:continue
        out[datetime.strptime(k,'%Y%m%d').date()]={'srad':float(v),'clear_srad':float(cv),'clearness':float(v)/float(cv)}
    return out
def noaa_days():
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
    days=[]
    for date,rs in sorted(bd.items()):
        if len({z[0].hour for z in rs})<20 or not 5<=date.month<=9:continue
        vals=[z[1] for z in rs];tmax=max(vals);tmin=min(vals);dtr=tmax-tmin;dl,su,sd=ds.daylen(date.timetuple().tm_yday);errs=[];aft=[]
        for sol,t in rs:
            hs=sol.hour+sol.minute/60+sol.second/3600;e=pl(hs,tmax,tmin,dl,su,sd)-t;errs.append(e)
            if 14<=hs<20:aft.append(e)
        days.append({'date':date,'year':date.year,'dtr':dtr,'dtrplus':max(0,dtr-DTRC),'rmse':math.sqrt(statistics.mean([e*e for e in errs])),'bias':statistics.mean(errs),'aft_rmse':math.sqrt(statistics.mean([e*e for e in aft])) if aft else float('nan'),'aft_bias':statistics.mean(aft) if aft else float('nan')})
    return days
def fit_eval(cal,val,features,response):
    X=np.array([[1.]+[r[f] for f in features] for r in cal],float);y=np.array([r[response] for r in cal]);beta=np.linalg.lstsq(X,y,rcond=None)[0]
    def ev(rows):
        xx=np.array([[1.]+[r[f] for f in features] for r in rows],float);yy=np.array([r[response] for r in rows]);pr=xx@beta;e=pr-yy;ss=np.sum((yy-np.mean(yy))**2);r2=1-np.sum(e*e)/ss if ss>0 else float('nan');return math.sqrt(np.mean(e*e)),np.mean(np.abs(e)),r2
    return beta,ev(val),ev([r for r in val if r['dtr']>=DTRC])
def main():
    solar=power();days=noaa_days();rows=[]
    for r in days:
        s=solar.get(r['date'])
        if not s:continue
        x=dict(r);x.update(s);rows.append(x)
    # Center radiation predictors on calibration means so interactions are interpretable.
    cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017]
    ms=statistics.mean([r['srad'] for r in cal]);mc=statistics.mean([r['clearness'] for r in cal])
    for r in rows:
        r['srad_c']=r['srad']-ms;r['clear_c']=r['clearness']-mc;r['dtr_srad']=r['dtrplus']*r['srad_c'];r['dtr_clear']=r['dtrplus']*r['clear_c']
    with CSVOUT.open('w',newline='',encoding='utf-8-sig') as f:
        fields=['date','year','dtr','dtrplus','srad','clear_srad','clearness','rmse','bias','aft_rmse','aft_bias'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:(v.isoformat() if k=='date' else v) for k,v in r.items() if k in fields} for r in rows])
    specs=[('DTR',['dtrplus']),('DTR+SRAD',['dtrplus','srad_c']),('DTR+CLEAR',['dtrplus','clear_c']),('DTR+SRAD+INT',['dtrplus','srad_c','dtr_srad']),('DTR+CLEAR+INT',['dtrplus','clear_c','dtr_clear']),('FULL',['dtrplus','srad_c','clear_c','dtr_srad','dtr_clear'])]
    out=[]
    for response in ['rmse','aft_rmse']:
        for name,fs in specs:
            beta,allm,high=fit_eval(cal,val,fs,response);out.append({'response':response,'model':name,'features':'+'.join(fs),'coefficients':';'.join(f'{x:.5f}' for x in beta),'val_rmse':round(allm[0],4),'val_mae':round(allm[1],4),'val_r2':round(allm[2],4),'val_highdtr_rmse':round(high[0],4),'val_highdtr_mae':round(high[1],4),'val_highdtr_r2':round(high[2],4)})
    with MODELS.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
    # Calibration SRAD tertiles, applied unchanged to validation high-DTR days.
    highcal=[r for r in cal if r['dtr']>=DTRC];q1,q2=np.quantile([r['srad'] for r in highcal],[1/3,2/3]);strata=[]
    for label,lo,hi in [('LowSRAD',-1e9,q1),('MidSRAD',q1,q2),('HighSRAD',q2,1e9)]:
        s=[r for r in val if r['dtr']>=DTRC and lo<=r['srad']<hi]
        if s:strata.append({'stratum':label,'srad_lo':round(lo,3) if lo>-1e8 else '','srad_hi':round(hi,3) if hi<1e8 else '','n_days':len(s),'mean_dtr':round(statistics.mean(r['dtr'] for r in s),3),'mean_srad':round(statistics.mean(r['srad'] for r in s),3),'mean_rmse':round(statistics.mean(r['rmse'] for r in s),4),'mean_aft_rmse':round(statistics.mean(r['aft_rmse'] for r in s),4),'mean_aft_bias':round(statistics.mean(r['aft_bias'] for r in s),4)})
    with STRATA.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(strata[0].keys()));w.writeheader();w.writerows(strata)
    dtr=[r for r in out if r['response']=='rmse' and r['model']=='DTR'][0];best=min([r for r in out if r['response']=='rmse'],key=lambda r:r['val_highdtr_rmse']);gain=100*(dtr['val_highdtr_rmse']-best['val_highdtr_rmse'])/dtr['val_highdtr_rmse']
    txt=f'''# Diwopu DTR × solar-radiation mechanism screening

- Dense NOAA temperature days merged with NASA POWER daily solar radiation: **{len(rows)}** May-Sep days.
- Calibration 2000-2016; independent validation 2017-2024.
- DTR excess trigger for this screen fixed from calibration-only Diwopu breakpoint: **{DTRC:.1f} C**.
- Radiation variables: ALLSKY surface shortwave and ALLSKY/CLRSKY clearness ratio.

## Independent prediction of daily HTEMP RMSE
| Model | Validation RMSE | High-DTR RMSE | High-DTR R2 |
|---|---:|---:|---:|
'''
    for r in out:
        if r['response']=='rmse':txt+=f"| {r['model']} | {r['val_rmse']:.4f} | {r['val_highdtr_rmse']:.4f} | {r['val_highdtr_r2']:.4f} |\n"
    txt+=f'''\nBest high-DTR explanatory model: **{best['model']}**; gain over DTR-only error prediction: **{gain:.2f}%**.

## High-DTR validation days stratified by calibration SRAD tertiles
| Group | N | Mean DTR | Mean SRAD | Mean daily RMSE | Mean afternoon RMSE | Afternoon Bias |
|---|---:|---:|---:|---:|---:|---:|
'''
    for r in strata:txt+=f"| {r['stratum']} | {r['n_days']} | {r['mean_dtr']:.2f} | {r['mean_srad']:.2f} | {r['mean_rmse']:.3f} | {r['mean_aft_rmse']:.3f} | {r['mean_aft_bias']:.3f} |\n"
    txt+='''\nRetain SRAD as a source-level HTEMP driver only if it adds material independent-validation explanatory power beyond DTR and yields a coherent physical stratification.\n''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
