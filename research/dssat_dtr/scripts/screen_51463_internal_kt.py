#!/usr/bin/env python3
"""Test an internally computable clearness index for Urumqi HTEMP.

Goal: replace NASA POWER clear-sky radiation with a quantity DSSAT can compute from
variables already available in a weather run.

Extraterrestrial radiation Ra is calculated with the FAO-56 astronomical equation
from latitude and day-of-year. Define Kt = SRAD / Ra. The prototype SRAD comes from
NASA POWER at the station only for this screening stage; the final DSSAT implementation
would use the WTH SRAD field.

Calibration 2000-2016; independent validation 2017-2024; DTRc=14.8 C fixed from
calibration-only residual breakpoint diagnostics.
"""
import csv,math,statistics
from datetime import datetime
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'/'processed_51463';INFILE=DATA/'main51463_dtr_srad_daily.csv';OUT=DATA/'main51463_internal_kt_models.csv';README=DATA/'README_MAIN51463_INTERNAL_KT.md'
LAT=43.7833;DTRC=14.8

def ra_mj(doy):
 phi=math.radians(LAT);gsc=0.0820;dr=1+0.033*math.cos(2*math.pi*doy/365);delta=0.409*math.sin(2*math.pi*doy/365-1.39);arg=-math.tan(phi)*math.tan(delta);arg=min(1,max(-1,arg));ws=math.acos(arg);return (24*60/math.pi)*gsc*dr*(ws*math.sin(phi)*math.sin(delta)+math.cos(phi)*math.cos(delta)*math.sin(ws))
def fit_eval(cal,val,features,response):
 X=np.array([[1]+[r[f] for f in features] for r in cal],float);y=np.array([r[response] for r in cal]);b=np.linalg.lstsq(X,y,rcond=None)[0]
 def ev(rows):
  xx=np.array([[1]+[r[f] for f in features] for r in rows],float);yy=np.array([r[response] for r in rows]);pr=xx@b;e=pr-yy;ss=np.sum((yy-np.mean(yy))**2);return math.sqrt(np.mean(e*e)),1-np.sum(e*e)/ss if ss>0 else float('nan')
 return b,ev(val),ev([r for r in val if r['dtr']>=15])
def main():
 rows=[]
 with INFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   d=datetime.strptime(r['date'],'%Y-%m-%d').date();ra=ra_mj(d.timetuple().tm_yday);x={k:float(r[k]) for k in ['dtr','srad','clearness','daily_rmse','afternoon_bias']};x.update({'date':d,'year':int(r['year']),'ra':ra,'kt':float(r['srad'])/ra});rows.append(x)
 cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];mkt=statistics.mean(r['kt'] for r in cal);ms=statistics.mean(r['srad'] for r in cal);mc=statistics.mean(r['clearness'] for r in cal)
 for r in rows:
  r['dtrplus']=max(0,r['dtr']-DTRC);r['kt_c']=r['kt']-mkt;r['srad_c']=r['srad']-ms;r['clear_c']=r['clearness']-mc;r['dtr_kt']=r['dtrplus']*r['kt_c'];r['dtr_srad']=r['dtrplus']*r['srad_c'];r['dtr_clear']=r['dtrplus']*r['clear_c']
 specs=[('DTR',['dtrplus']),('DTR+SRAD+INT',['dtrplus','srad_c','dtr_srad']),('DTR+KT',['dtrplus','kt_c']),('DTR+KT+INT',['dtrplus','kt_c','dtr_kt']),('DTR+CLEAR+INT',['dtrplus','clear_c','dtr_clear'])]
 out=[]
 for response in ['daily_rmse','afternoon_bias']:
  for name,fs in specs:
   b,allm,high=fit_eval(cal,val,fs,response);out.append({'response':response,'model':name,'features':'+'.join(fs),'coefficients':';'.join(f'{z:.6f}' for z in b),'val_rmse':allm[0],'val_r2':allm[1],'highdtr_rmse':high[0],'highdtr_r2':high[1]})
 with OUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
 daily=[r for r in out if r['response']=='daily_rmse'];dtr=next(r for r in daily if r['model']=='DTR');kt=next(r for r in daily if r['model']=='DTR+KT+INT');clear=next(r for r in daily if r['model']=='DTR+CLEAR+INT');gain=100*(dtr['highdtr_rmse']-kt['highdtr_rmse'])/dtr['highdtr_rmse'];gap=100*(kt['highdtr_rmse']-clear['highdtr_rmse'])/clear['highdtr_rmse']
 aft=[r for r in out if r['response']=='afternoon_bias'];ka=next(r for r in aft if r['model']=='DTR+KT+INT');da=next(r for r in aft if r['model']=='DTR');gaina=100*(da['highdtr_rmse']-ka['highdtr_rmse'])/da['highdtr_rmse']
 txt=f'''# Main 51463 internal astronomical clearness-index screen\n\n`Ra` is computed from latitude + DOY using FAO-56 extraterrestrial radiation. `Kt = SRAD/Ra`. This requires no clear-sky radiation input and can be computed inside DSSAT from existing weather/astronomical variables.\n\n- Calibration mean Kt = **{mkt:.4f}**\n- Formal DTR trigger = **{DTRC:.1f} C**\n\n## Independent high-DTR validation: daily RMSE prediction\n| Model | RMSE | R2 |\n|---|---:|---:|\n'''
 for r in daily:txt+=f"| {r['model']} | {r['highdtr_rmse']:.4f} | {r['highdtr_r2']:.4f} |\n"
 txt+=f'''\n`DTR+Kt+interaction` gain over DTR-only = **{gain:.2f}%**.\nIts RMSE is **{gap:+.2f}%** relative to the NASA clear-sky-ratio interaction model (positive means worse).\n\nFor afternoon-bias prediction, `DTR+Kt+interaction` improves high-DTR RMSE by **{gaina:.2f}%** relative to DTR-only.\n\nDecision: if Kt retains most of the CLEAR-model gain, use Kt in the source-level prototype because it is internally computable and does not require a new weather input.\n''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
