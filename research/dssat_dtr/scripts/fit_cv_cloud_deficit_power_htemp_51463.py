#!/usr/bin/env python3
"""Fit a nonlinear radiation-deficit HTEMP correction for Urumqi 51463.

DTRc=14.8 C is fixed from calibration-only breakpoint analysis.
Kt=SRAD/Ra is internally computable. Define continuous radiative deficit
  Dk = max(0,1-Kt)
and a normalized gate
  G = (Dk/0.4)^p.
The reference 0.4 only scales beta; it is not a threshold.

p is chosen by leave-one-year-out CV within 2000-2016 from 0.5..4.0 step 0.25.
For each p and fold, separate nonnegative beta_pre/beta_post are fitted analytically.
2017-2024 is untouched final validation.
"""
import csv,math,statistics
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'/'processed_51463'
PFILE=DATA/'htemp_pointwise_2000_2024.csv';SFILE=DATA/'main51463_dtr_srad_daily.csv'
README=DATA/'README_CV_CLOUDDEF_POWER_HTEMP.md';CVOUT=DATA/'cv_clouddef_power_grid.csv';PARAM=DATA/'cv_clouddef_power_parameters.csv';VAL=DATA/'cv_clouddef_power_validation.csv';DTR=DATA/'cv_clouddef_power_by_dtr.csv';HOUR=DATA/'cv_clouddef_power_by_hour.csv';STRATA=DATA/'cv_clouddef_power_by_kt_strata.csv'
DTRC=14.8;LAT=43.7833;A=2.0;C=1.0

def mean(x):return statistics.mean(x) if x else float('nan')
def ra(j):
 phi=math.radians(LAT);dr=1+0.033*math.cos(2*math.pi*j/365);de=0.409*math.sin(2*math.pi*j/365-1.39);arg=max(-1,min(1,-math.tan(phi)*math.tan(de)));ws=math.acos(arg);return (24*60/math.pi)*0.0820*dr*(ws*math.sin(phi)*math.sin(de)+math.cos(phi)*math.cos(de)*math.sin(ws))
def branch(r):
 hs=float(r['solar_hour']);sn=float(r['snup_solar_h']);sd=float(r['sndn_solar_h']);dl=float(r['dayl_h']);tp=sn+C+dl/2+A
 if 12<hs<tp and tp>12:
  v=(hs-12)/(tp-12);return 'pre',4*v*(1-v)
 if tp<hs<sd and sd>tp:
  u=(hs-tp)/(sd-tp);return 'post',4*u*(1-u)
 return 'none',0.0
def gate(r,p):return (max(0.0,1.0-r['kt'])/0.4)**p
def fit_beta(rows,p,which):
 s=t=0.0;n=0
 for r in rows:
  b,bv=branch(r)
  if b!=which or float(r['formal_dtr_c'])<=DTRC:continue
  x=(float(r['formal_dtr_c'])-DTRC)*gate(r,p)*bv
  if x<=0:continue
  e=float(r['pred_c'])-float(r['obs_c']);s+=x*x;t+=x*e;n+=1
 return max(0.0,t/s) if s>0 else 0.0,n
def pred(r,p,bp,bq):
 if float(r['formal_dtr_c'])<=DTRC:return float(r['pred_c'])
 w,b=branch(r)
 if w=='none':return float(r['pred_c'])
 x=(float(r['formal_dtr_c'])-DTRC)*gate(r,p)*b
 return float(r['pred_c'])-(bp if w=='pre' else bq)*x
def metric(rows,pf):
 if not rows:return {'n':0,'rmse':float('nan'),'mae':float('nan'),'mbe':float('nan'),'r2':float('nan')}
 o=[float(r['obs_c']) for r in rows];q=[pf(r) for r in rows];e=[b-a for a,b in zip(o,q)];rm=math.sqrt(mean([z*z for z in e]));ma=mean([abs(z) for z in e]);mb=mean(e);mo,mp=mean(o),mean(q);so=sum((x-mo)**2 for x in o);sp=sum((x-mp)**2 for x in q);rr=sum((a-mo)*(b-mp) for a,b in zip(o,q))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan');return {'n':len(rows),'rmse':rm,'mae':ma,'mbe':mb,'r2':rr*rr}
def dbin(d):
 if d<10:return '<10'
 if d<15:return '10-<15'
 if d<18:return '15-<18'
 if d<20:return '18-<20'
 return '>=20'
def main():
 kd={}
 with SFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   d=datetime.strptime(r['date'],'%Y-%m-%d').date();kd[r['date']]=float(r['srad'])/ra(d.timetuple().tm_yday)
 rows=[]
 with PFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in kd:continue
   r['year']=int(r['solar_date'][:4]);r['kt']=kd[r['solar_date']];rows.append(r)
 cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];years=sorted(set(r['year'] for r in cal));high=lambda r:float(r['formal_dtr_c'])>=15
 grid=[]
 for i in range(15):
  p=0.5+i*0.25;sse=n=0
  for y in years:
   tr=[r for r in cal if r['year']!=y];te=[r for r in cal if r['year']==y and high(r)];bp,_=fit_beta(tr,p,'pre');bq,_=fit_beta(tr,p,'post')
   for r in te:e=pred(r,p,bp,bq)-float(r['obs_c']);sse+=e*e;n+=1
  grid.append({'p':p,'loyo_n':n,'loyo_rmse':math.sqrt(sse/n)})
 best=min(grid,key=lambda x:x['loyo_rmse']);p=float(best['p']);bp,np=fit_beta(cal,p,'pre');bq,nq=fit_beta(cal,p,'post')
 with CVOUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(grid[0].keys()));w.writeheader();w.writerows(grid)
 with PARAM.open('w',newline='',encoding='utf-8-sig') as f:
  ff=['dtr_threshold_c','power_p','beta_pre','beta_post','n_cal_pre','n_cal_post','loyo_rmse'];w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerow({'dtr_threshold_c':DTRC,'power_p':p,'beta_pre':bp,'beta_post':bq,'n_cal_pre':np,'n_cal_post':nq,'loyo_rmse':best['loyo_rmse']})
 models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M11_CLOUDDEF_POWER',lambda r:pred(r,p,bp,bq))];groups=[('May-Sep',val),('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),('DTR>=15',[r for r in val if high(r)]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
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
 caldays={r['solar_date']:r['kt'] for r in cal if high(r)};ks=sorted(caldays.values());q1=ks[len(ks)//3];q2=ks[2*len(ks)//3];sr=[]
 for label,lo,hi in [('LowKt',-9,q1),('MidKt',q1,q2),('HighKt',q2,9)]:
  rs=[r for r in val if high(r) and lo<=r['kt']<hi]
  for name,pf in models:m=metric(rs,pf);m.update({'model':name,'kt_group':label,'n_days':len(set(r['solar_date'] for r in rs))});sr.append(m)
 ff4=['model','kt_group','n_days','n','rmse','mae','mbe','r2']
 with STRATA.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=ff4);w.writeheader();w.writerows([{k:r[k] for k in ff4} for r in sr])
 mm={(r['model'],r['group']):r for r in rec};bo=mm[('M0_OFFICIAL','DTR>=15')];bn=mm[('M11_CLOUDDEF_POWER','DTR>=15')];ba=mm[('M0_OFFICIAL','May-Sep')];na=mm[('M11_CLOUDDEF_POWER','May-Sep')];imp=100*(bo['rmse']-bn['rmse'])/bo['rmse'];impa=100*(ba['rmse']-na['rmse'])/ba['rmse']
 text=f'''# Urumqi CV nonlinear radiative-deficit HTEMP\n\n- DTR trigger: **>{DTRC:.1f} C**\n- Gate: `G=(max(0,1-Kt)/0.4)^p`\n- Power selected by 2000-2016 leave-one-year-out CV: **p={p:.2f}**\n- CV pooled high-DTR RMSE: **{best['loyo_rmse']:.4f} C**\n- beta_pre = **{bp:.4f}**; beta_post = **{bq:.4f}**\n\nNo Kt cutoff is introduced. As Kt approaches 1, the correction decays continuously toward zero.\n\n## Independent validation 2017-2024\n| Scope | Official RMSE | M11 RMSE | Improvement | Official Bias | M11 Bias | Official R2 | M11 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {ba['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {ba['mbe']:.4f} | {na['mbe']:.4f} | {ba['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {bo['rmse']:.4f} | {bn['rmse']:.4f} | {imp:.2f}% | {bo['mbe']:.4f} | {bn['mbe']:.4f} | {bo['r2']:.4f} | {bn['r2']:.4f} |\n\nCompare against M10 (13.71% high-DTR improvement) and inspect Kt strata before retention.\n''';README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
