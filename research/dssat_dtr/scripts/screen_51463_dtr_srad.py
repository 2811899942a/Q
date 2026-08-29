#!/usr/bin/env python3
"""Screen DTR x solar-radiation interaction for the main Urumqi station 51463099999.

Uses the already validated daily HTEMP residual table for the main station and NASA POWER
LST daily solar radiation at the exact station coordinate (87.6167E, 43.7833N).

Formal split: calibration 2000-2016; independent validation 2017-2024.
Formal DTR excess trigger: 14.8 C, from calibration-only Urumqi breakpoint diagnostics.
This is a mechanism screen, not yet a correction formula.
"""
import csv,json,math,statistics,urllib.request
from datetime import datetime
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'/'processed_51463'
INFILE=DATA/'dtr_asymmetry_daily.csv';DAILY=DATA/'main51463_dtr_srad_daily.csv';MODELS=DATA/'main51463_dtr_srad_models.csv';STRATA=DATA/'main51463_highdtr_srad_strata.csv';README=DATA/'README_MAIN51463_DTR_SRAD.md'
DTRC=14.8;LON=87.6167;LAT=43.7833

def power():
 url=('https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN'
      f'&community=AG&longitude={LON}&latitude={LAT}&start=20000101&end=20241231&format=JSON&time-standard=LST')
 req=urllib.request.Request(url,headers={'User-Agent':'DSSAT-DTR-research/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:j=json.loads(r.read().decode())
 a=j['properties']['parameter']['ALLSKY_SFC_SW_DWN'];c=j['properties']['parameter']['CLRSKY_SFC_SW_DWN'];out={}
 for k,v in a.items():
  cv=c.get(k)
  if v is None or cv is None or float(v)<-900 or float(cv)<=0 or float(cv)<-900:continue
  d=datetime.strptime(k,'%Y%m%d').date();out[d]={'srad':float(v),'clear_srad':float(cv),'clearness':float(v)/float(cv)}
 return out

def fit_eval(cal,val,features,response,high_selector):
 X=np.array([[1.]+[r[f] for f in features] for r in cal],float);y=np.array([r[response] for r in cal],float);beta=np.linalg.lstsq(X,y,rcond=None)[0]
 def ev(rows):
  if not rows:return (float('nan'),float('nan'),float('nan'))
  xx=np.array([[1.]+[r[f] for f in features] for r in rows],float);yy=np.array([r[response] for r in rows],float);pr=xx@beta;e=pr-yy;ss=np.sum((yy-np.mean(yy))**2);r2=1-np.sum(e*e)/ss if ss>0 else float('nan');return math.sqrt(np.mean(e*e)),np.mean(np.abs(e)),r2
 return beta,ev(val),ev([r for r in val if high_selector(r)])

def main():
 solar=power();rows=[]
 with INFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if r['season']!='May-Sep':continue
   d=datetime.strptime(r['solar_date'],'%Y-%m-%d').date();s=solar.get(d)
   if not s:continue
   x={'date':d,'year':d.year,'dtr':float(r['dtr_c']),'daily_rmse':float(r['daily_rmse_c']),'daily_bias':float(r['daily_bias_c']),
      'afternoon_bias':float(r['afternoon_bias_c']) if r['afternoon_bias_c']!='' else float('nan'),
      'afternoon_rmse':float(r['afternoon_rmse_c']) if r['afternoon_rmse_c']!='' else float('nan'),
      'tmax':float(r['tmax_c']),'tmin':float(r['tmin_c'])};x.update(s);rows.append(x)
 cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017]
 ms=statistics.mean(r['srad'] for r in cal);mc=statistics.mean(r['clearness'] for r in cal)
 for r in rows:
  r['dtrplus']=max(0,r['dtr']-DTRC);r['srad_c']=r['srad']-ms;r['clear_c']=r['clearness']-mc;r['dtr_srad']=r['dtrplus']*r['srad_c'];r['dtr_clear']=r['dtrplus']*r['clear_c']
 fields=['date','year','dtr','dtrplus','tmax','tmin','srad','clear_srad','clearness','daily_rmse','daily_bias','afternoon_rmse','afternoon_bias']
 with DAILY.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:(v.isoformat() if k=='date' else v) for k,v in r.items() if k in fields} for r in rows])
 specs=[('DTR',['dtrplus']),('DTR+SRAD',['dtrplus','srad_c']),('DTR+CLEAR',['dtrplus','clear_c']),('DTR+SRAD+INT',['dtrplus','srad_c','dtr_srad']),('DTR+CLEAR+INT',['dtrplus','clear_c','dtr_clear']),('FULL',['dtrplus','srad_c','clear_c','dtr_srad','dtr_clear'])]
 out=[]
 for response in ['daily_rmse','afternoon_rmse','afternoon_bias']:
  ccal=[r for r in cal if math.isfinite(r[response])];vval=[r for r in val if math.isfinite(r[response])]
  for name,fs in specs:
   beta,allm,high=fit_eval(ccal,vval,fs,response,lambda r:r['dtr']>=15.0);out.append({'response':response,'model':name,'features':'+'.join(fs),'coefficients':';'.join(f'{x:.6f}' for x in beta),'val_rmse':round(allm[0],4),'val_mae':round(allm[1],4),'val_r2':round(allm[2],4),'highdtr_rmse':round(high[0],4),'highdtr_mae':round(high[1],4),'highdtr_r2':round(high[2],4)})
 with MODELS.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
 highcal=[r for r in cal if r['dtr']>=15];q1,q2=np.quantile([r['srad'] for r in highcal],[1/3,2/3]);strata=[]
 for label,lo,hi in [('LowSRAD',-1e9,q1),('MidSRAD',q1,q2),('HighSRAD',q2,1e9)]:
  s=[r for r in val if r['dtr']>=15 and lo<=r['srad']<hi]
  if s:strata.append({'stratum':label,'n_days':len(s),'mean_dtr':statistics.mean(r['dtr'] for r in s),'mean_srad':statistics.mean(r['srad'] for r in s),'mean_clearness':statistics.mean(r['clearness'] for r in s),'mean_daily_rmse':statistics.mean(r['daily_rmse'] for r in s),'mean_afternoon_rmse':statistics.mean(r['afternoon_rmse'] for r in s if math.isfinite(r['afternoon_rmse'])),'mean_afternoon_bias':statistics.mean(r['afternoon_bias'] for r in s if math.isfinite(r['afternoon_bias']))})
 with STRATA.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(strata[0].keys()));w.writeheader();w.writerows(strata)
 daily=[r for r in out if r['response']=='daily_rmse'];dtr=next(r for r in daily if r['model']=='DTR');best=min(daily,key=lambda r:r['highdtr_rmse']);gain=100*(dtr['highdtr_rmse']-best['highdtr_rmse'])/dtr['highdtr_rmse']
 aft=[r for r in out if r['response']=='afternoon_bias'];best_a=min(aft,key=lambda r:r['highdtr_rmse']);dtr_a=next(r for r in aft if r['model']=='DTR');gain_a=100*(dtr_a['highdtr_rmse']-best_a['highdtr_rmse'])/dtr_a['highdtr_rmse']
 txt=f'''# Main Urumqi 51463 DTR x solar-radiation screening\n\n- Station: **51463099999**, {LON} E, {LAT} N\n- Matched May-Sep days: **{len(rows)}**\n- Calibration: 2000-2016; validation: 2017-2024\n- Formal DTR trigger: **{DTRC:.1f} C**, from calibration only\n- SRAD source: NASA POWER daily LST at the station coordinate\n\n## Daily RMSE prediction, independent high-DTR validation\n| Model | High-DTR RMSE | High-DTR R2 |\n|---|---:|---:|\n'''
 for r in daily:txt+=f"| {r['model']} | {r['highdtr_rmse']:.4f} | {r['highdtr_r2']:.4f} |\n"
 txt+=f'''\nBest daily-RMSE model: **{best['model']}**, improvement over DTR-only error prediction: **{gain:.2f}%**.\n\nBest afternoon-bias model: **{best_a['model']}**, improvement over DTR-only prediction: **{gain_a:.2f}%**.\n\n## High-DTR validation SRAD strata\n| Group | N | Mean DTR | Mean SRAD | Daily RMSE | Afternoon RMSE | Afternoon Bias |\n|---|---:|---:|---:|---:|---:|---:|\n'''
 for r in strata:txt+=f"| {r['stratum']} | {r['n_days']} | {r['mean_dtr']:.2f} | {r['mean_srad']:.2f} | {r['mean_daily_rmse']:.3f} | {r['mean_afternoon_rmse']:.3f} | {r['mean_afternoon_bias']:.3f} |\n"
 txt+='''\nDecision rule: only promote SRAD into the Urumqi HTEMP formula if it adds material independent-validation information beyond DTR and the high-DTR strata show a coherent residual shift.\n''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
