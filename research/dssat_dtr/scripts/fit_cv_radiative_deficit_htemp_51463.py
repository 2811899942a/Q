#!/usr/bin/env python3
"""Fit a cross-validated radiative-deficit-gated HTEMP correction for Urumqi 51463.

DTRc=14.8 C is fixed from calibration-only DTR breakpoint analysis.
Radiation is a continuous gate, not claimed as a second physical threshold.

Kt = SRAD/Ra, with Ra from latitude + DOY.
For a candidate Kt0, define normalized radiative deficit:
  Rdef = max(0, Kt0-Kt) / 0.1
so one unit means Kt is 0.1 below the cutoff scale.

For DTR>DTRc:
  pre-peak basis:  Bpre=4v(1-v), solar noon -> modeled Tmax
  post-peak basis: Bpost=4u(1-u), modeled Tmax -> sunset
  Tnew = TPL - beta_pre * (DTR-DTRc) * Rdef * Bpre
              - beta_post* (DTR-DTRc) * Rdef * Bpost

Kt0 is chosen only within 2000-2016 by leave-one-year-out cross-validation over
candidate values 0.45..0.90 step 0.01. For each fold, beta_pre/beta_post are fitted
analytically on the other calibration years. 2017-2024 is untouched final validation.
DTR<=14.8 C is exactly official DSSAT.
"""
from __future__ import annotations
import csv,math,statistics
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'/'processed_51463'
PFILE=DATA/'htemp_pointwise_2000_2024.csv';SFILE=DATA/'main51463_dtr_srad_daily.csv'
README=DATA/'README_CV_RADDEF_HTEMP.md';CVOUT=DATA/'cv_raddef_kt0_grid.csv';PARAM=DATA/'cv_raddef_parameters.csv';VAL=DATA/'cv_raddef_validation.csv';DTR=DATA/'cv_raddef_by_dtr.csv';HOUR=DATA/'cv_raddef_by_hour.csv';STRATA=DATA/'cv_raddef_by_kt_strata.csv'
DTRC=14.8;LAT=43.7833;A=2.0;C=1.0

def mean(x):return statistics.mean(x) if x else float('nan')
def ra(doy):
 phi=math.radians(LAT);dr=1+0.033*math.cos(2*math.pi*doy/365);de=0.409*math.sin(2*math.pi*doy/365-1.39);arg=max(-1,min(1,-math.tan(phi)*math.tan(de)));ws=math.acos(arg);return (24*60/math.pi)*0.0820*dr*(ws*math.sin(phi)*math.sin(de)+math.cos(phi)*math.cos(de)*math.sin(ws))
def branch(r):
 hs=float(r['solar_hour']);sn=float(r['snup_solar_h']);sd=float(r['sndn_solar_h']);dl=float(r['dayl_h']);tp=sn+C+dl/2+A
 if 12.0<hs<tp and tp>12:
  v=(hs-12)/(tp-12);return 'pre',4*v*(1-v)
 if tp<hs<sd and sd>tp:
  u=(hs-tp)/(sd-tp);return 'post',4*u*(1-u)
 return 'none',0.0
def rdef(r,kt0):return max(0.0,kt0-r['kt'])/0.1
def fit_beta(rows,kt0,which):
 s=t=0.0;n=0
 for r in rows:
  b,bv=branch(r)
  if b!=which or float(r['formal_dtr_c'])<=DTRC:continue
  x=(float(r['formal_dtr_c'])-DTRC)*rdef(r,kt0)*bv
  if x<=0:continue
  e=float(r['pred_c'])-float(r['obs_c']);s+=x*x;t+=x*e;n+=1
 return (max(0.0,t/s) if s>0 else 0.0),n
def pred(r,kt0,bpre,bpost):
 if float(r['formal_dtr_c'])<=DTRC:return float(r['pred_c'])
 which,bv=branch(r)
 if which=='none':return float(r['pred_c'])
 x=(float(r['formal_dtr_c'])-DTRC)*rdef(r,kt0)*bv
 if which=='pre':return float(r['pred_c'])-bpre*x
 return float(r['pred_c'])-bpost*x
def metric(rows,pf):
 if not rows:return {'n':0,'rmse':float('nan'),'mae':float('nan'),'mbe':float('nan'),'r2':float('nan')}
 o=[float(r['obs_c']) for r in rows];p=[pf(r) for r in rows];e=[b-a for a,b in zip(o,p)];rm=math.sqrt(mean([z*z for z in e]));ma=mean([abs(z) for z in e]);mb=mean(e);mo,mp=mean(o),mean(p);so=sum((x-mo)**2 for x in o);sp=sum((x-mp)**2 for x in p);rr=sum((a-mo)*(b-mp) for a,b in zip(o,p))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan');return {'n':len(rows),'rmse':rm,'mae':ma,'mbe':mb,'r2':rr*rr}
def dbin(d):
 if d<10:return '<10'
 if d<15:return '10-<15'
 if d<18:return '15-<18'
 if d<20:return '18-<20'
 return '>=20'
def main():
 kt_by_date={}
 with SFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   d=datetime.strptime(r['date'],'%Y-%m-%d').date();kt_by_date[r['date']]=float(r['srad'])/ra(d.timetuple().tm_yday)
 rows=[]
 with PFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in kt_by_date:continue
   r['year']=int(r['solar_date'][:4]);r['kt']=kt_by_date[r['solar_date']];rows.append(r)
 cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];years=sorted(set(r['year'] for r in cal));high=lambda r:float(r['formal_dtr_c'])>=15
 grid=[]
 for i in range(46):
  kt0=0.45+i*0.01;sse=n=0
  for y in years:
   tr=[r for r in cal if r['year']!=y];te=[r for r in cal if r['year']==y and high(r)]
   bp,_=fit_beta(tr,kt0,'pre');bq,_=fit_beta(tr,kt0,'post')
   for r in te:
    e=pred(r,kt0,bp,bq)-float(r['obs_c']);sse+=e*e;n+=1
  grid.append({'kt0':round(kt0,3),'loyo_n':n,'loyo_rmse':math.sqrt(sse/n) if n else float('nan')})
 best=min(grid,key=lambda z:z['loyo_rmse']);kt0=float(best['kt0']);bp,np=fit_beta(cal,kt0,'pre');bq,nq=fit_beta(cal,kt0,'post')
 with CVOUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(grid[0].keys()));w.writeheader();w.writerows(grid)
 with PARAM.open('w',newline='',encoding='utf-8-sig') as f:
  ff=['dtr_threshold_c','kt0_cv','beta_pre','beta_post','n_cal_pre','n_cal_post','loyo_rmse'];w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerow({'dtr_threshold_c':DTRC,'kt0_cv':kt0,'beta_pre':bp,'beta_post':bq,'n_cal_pre':np,'n_cal_post':nq,'loyo_rmse':best['loyo_rmse']})
 models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M10_CV_RADDEF',lambda r:pred(r,kt0,bp,bq))];groups=[('May-Sep',val),('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),('DTR>=15',[r for r in val if high(r)]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
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
  for h in [11,12,14,15,17,18,20,23]:
   rs=[r for r in val if int(float(r['solar_hour']))==h];m=metric(rs,pf);m.update({'model':name,'solar_hour':h});hr.append(m)
 ff3=['model','solar_hour','n','rmse','mae','mbe','r2']
 with HOUR.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=ff3);w.writeheader();w.writerows([{k:r[k] for k in ff3} for r in hr])
 # Calibration high-DTR Kt tertiles for robustness reporting only.
 caldays={r['solar_date']:r['kt'] for r in cal if high(r)};ks=sorted(caldays.values());q1=ks[len(ks)//3];q2=ks[2*len(ks)//3];sr=[]
 for label,lo,hi in [('LowKt',-9,q1),('MidKt',q1,q2),('HighKt',q2,9)]:
  rs=[r for r in val if high(r) and lo<=r['kt']<hi]
  for name,pf in models:
   m=metric(rs,pf);m.update({'model':name,'kt_group':label,'n_days':len(set(r['solar_date'] for r in rs))});sr.append(m)
 ff4=['model','kt_group','n_days','n','rmse','mae','mbe','r2']
 with STRATA.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=ff4);w.writeheader();w.writerows([{k:r[k] for k in ff4} for r in sr])
 mm={(r['model'],r['group']):r for r in rec};bo=mm[('M0_OFFICIAL','DTR>=15')];bn=mm[('M10_CV_RADDEF','DTR>=15')];ba=mm[('M0_OFFICIAL','May-Sep')];na=mm[('M10_CV_RADDEF','May-Sep')];imp=100*(bo['rmse']-bn['rmse'])/bo['rmse'];impa=100*(ba['rmse']-na['rmse'])/ba['rmse']
 text=f'''# Urumqi cross-validated radiative-deficit-gated HTEMP\n\n- DTR trigger: **>{DTRC:.1f} C** (calibration-only breakpoint)\n- Kt cutoff scale selected by 2000-2016 leave-one-year-out CV: **Kt0={kt0:.3f}**\n- CV pooled high-DTR RMSE at selected Kt0: **{best['loyo_rmse']:.4f} C**\n- `Rdef=max(0,Kt0-Kt)/0.1`\n- beta_pre = **{bp:.4f} C per C-DTR-excess per 0.1-Kt-deficit**\n- beta_post = **{bq:.4f} C per C-DTR-excess per 0.1-Kt-deficit**\n\nFor Kt>=Kt0 the radiation gate is exactly zero, so high-clearness high-DTR days receive no shoulder cooling.\n\n## Independent validation 2017-2024\n| Scope | Official RMSE | M10 RMSE | Improvement | Official Bias | M10 Bias | Official R2 | M10 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {ba['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {ba['mbe']:.4f} | {na['mbe']:.4f} | {ba['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {bo['rmse']:.4f} | {bn['rmse']:.4f} | {imp:.2f}% | {bo['mbe']:.4f} | {bn['mbe']:.4f} | {bo['r2']:.4f} | {bn['r2']:.4f} |\n\nThis is the preferred structure if it keeps the M9 low/mid-Kt gains, removes the high-Kt degradation, and improves or maintains the 12.84% M9 high-DTR gain.\n''';README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
