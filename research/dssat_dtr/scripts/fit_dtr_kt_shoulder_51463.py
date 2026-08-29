#!/usr/bin/env python3
"""Fit a DTR-triggered, internally-computable Kt-modulated HTEMP shoulder correction.

DTRc=14.8 C is fixed from 2000-2016 calibration-only residual breakpoint analysis.
Kt = SRAD/Ra, where Ra is FAO-56 extraterrestrial radiation from latitude + DOY.
Prototype SRAD is the daily station-coordinate NASA POWER series already merged for
mechanism screening; a DSSAT implementation would use the existing WTH SRAD field.

For DTR>DTRc, define two hot-shoulder bases:
- pre-peak: solar noon -> modeled Tmax, Bpre=4v(1-v)
- post-peak: modeled Tmax -> sunset, Bpost=4u(1-u)

Correction amplitudes depend continuously on clearness:
 Apre  = excess * (bpre0 + bpre1*(Kt-Kt_cal_mean))
 Apost = excess * (bpost0 + bpost1*(Kt-Kt_cal_mean))
 Tnew = TPL - A*B on the active branch.

Four linear coefficients are fitted analytically using only 2000-2016 May-Sep points.
2017-2024 is untouched independent validation. DTR<=14.8 remains official DSSAT.
"""
import csv,math,statistics
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'/'processed_51463';PFILE=DATA/'htemp_pointwise_2000_2024.csv';SFILE=DATA/'main51463_dtr_srad_daily.csv'
README=DATA/'README_DTR_KT_SHOULDER.md';PARAM=DATA/'dtr_kt_shoulder_parameters.csv';VAL=DATA/'dtr_kt_shoulder_validation.csv';DTR=DATA/'dtr_kt_shoulder_by_dtr.csv';HOUR=DATA/'dtr_kt_shoulder_by_hour.csv';STRATA=DATA/'dtr_kt_shoulder_by_kt_strata.csv'
DTRC=14.8;LAT=43.7833;A=2.0;C=1.0

def mean(x):return statistics.mean(x) if x else float('nan')
def ra(doy):
 phi=math.radians(LAT);dr=1+0.033*math.cos(2*math.pi*doy/365);de=0.409*math.sin(2*math.pi*doy/365-1.39);arg=max(-1,min(1,-math.tan(phi)*math.tan(de)));ws=math.acos(arg);return (24*60/math.pi)*0.0820*dr*(ws*math.sin(phi)*math.sin(de)+math.cos(phi)*math.cos(de)*math.sin(ws))
def solve2(rows,which,ktmean):
 a11=a22=a12=t1=t2=0.0;n=0
 for r in rows:
  bpre,bpost=branch_bases(r);b=bpre if which=='pre' else bpost
  if b==0:continue
  ex=max(0,float(r['formal_dtr_c'])-DTRC);kc=r['kt']-ktmean;z1=ex*b;z2=ex*b*kc;e=float(r['pred_c'])-float(r['obs_c']);a11+=z1*z1;a22+=z2*z2;a12+=z1*z2;t1+=z1*e;t2+=z2*e;n+=1
 den=a11*a22-a12*a12
 if abs(den)<1e-12:return 0.0,0.0,n
 b0=(t1*a22-t2*a12)/den;b1=(t2*a11-t1*a12)/den
 return b0,b1,n
def branch_bases(r):
 d=float(r['formal_dtr_c']);hs=float(r['solar_hour'])
 if d<=DTRC:return 0.0,0.0
 sn=float(r['snup_solar_h']);sd=float(r['sndn_solar_h']);dl=float(r['dayl_h']);tp=sn+C+dl/2+A
 if 12.0<hs<tp and tp>12:
  v=(hs-12)/(tp-12);return 4*v*(1-v),0.0
 if tp<hs<sd and sd>tp:
  u=(hs-tp)/(sd-tp);return 0.0,4*u*(1-u)
 return 0.0,0.0
def pred(r,coef,ktmean):
 bpre,bpost=branch_bases(r)
 if bpre==0 and bpost==0:return float(r['pred_c'])
 ex=max(0,float(r['formal_dtr_c'])-DTRC);kc=r['kt']-ktmean
 if bpre:
  amp=ex*(coef[0]+coef[1]*kc);return float(r['pred_c'])-amp*bpre
 amp=ex*(coef[2]+coef[3]*kc);return float(r['pred_c'])-amp*bpost
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
 srad={}
 with SFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   d=datetime.strptime(r['date'],'%Y-%m-%d').date();s=float(r['srad']);srad[r['date']]=s/ra(d.timetuple().tm_yday)
 rows=[]
 with PFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in srad:continue
   r['year']=int(r['solar_date'][:4]);r['kt']=srad[r['solar_date']];rows.append(r)
 cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];ktmean=mean([r['kt'] for r in cal]);p0,p1,np=solve2(cal,'pre',ktmean);q0,q1,nq=solve2(cal,'post',ktmean);coef=(p0,p1,q0,q1)
 with PARAM.open('w',newline='',encoding='utf-8-sig') as f:
  ff=['dtr_threshold_c','kt_cal_mean','bpre0','bpre_kt','bpost0','bpost_kt','n_pre_cal','n_post_cal'];w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerow({'dtr_threshold_c':DTRC,'kt_cal_mean':ktmean,'bpre0':p0,'bpre_kt':p1,'bpost0':q0,'bpost_kt':q1,'n_pre_cal':np,'n_post_cal':nq})
 models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M9_DTR_KT_SHOULDER',lambda r:pred(r,coef,ktmean))];groups=[('May-Sep',val),('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
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
 # Kt tertiles from calibration high-DTR days (unique dates), apply to validation.
 caldays={r['solar_date']:r['kt'] for r in cal if float(r['formal_dtr_c'])>=15};vals=sorted(caldays.values());q1=vals[len(vals)//3];q2=vals[(2*len(vals))//3];sr=[]
 for label,lo,hi in [('LowKt',-9,q1),('MidKt',q1,q2),('HighKt',q2,9)]:
  rs=[r for r in val if float(r['formal_dtr_c'])>=15 and lo<=r['kt']<hi]
  for name,pf in models:
   m=metric(rs,pf);m.update({'model':name,'kt_group':label,'n_days':len(set(r['solar_date'] for r in rs))});sr.append(m)
 ff4=['model','kt_group','n_days','n','rmse','mae','mbe','r2']
 with STRATA.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=ff4);w.writeheader();w.writerows([{k:r[k] for k in ff4} for r in sr])
 mm={(r['model'],r['group']):r for r in rec};bo=mm[('M0_OFFICIAL','DTR>=15')];bn=mm[('M9_DTR_KT_SHOULDER','DTR>=15')];ba=mm[('M0_OFFICIAL','May-Sep')];na=mm[('M9_DTR_KT_SHOULDER','May-Sep')];imp=100*(bo['rmse']-bn['rmse'])/bo['rmse'];impa=100*(ba['rmse']-na['rmse'])/ba['rmse']
 text=f'''# Urumqi DTR-triggered Kt-modulated hot-shoulder HTEMP\n\n- Formal DTR trigger: **>{DTRC:.1f} C**, calibration-only\n- Kt = SRAD/Ra; calibration mean Kt = **{ktmean:.4f}**\n- Pre-peak amplitude: `excess*({p0:.4f} + {p1:.4f}*(Kt-Ktmean))`\n- Post-peak amplitude: `excess*({q0:.4f} + {q1:.4f}*(Kt-Ktmean))`\n- Calibration active points: pre={np}, post={nq}\n\n## Independent validation 2017-2024\n| Scope | Official RMSE | M9 RMSE | Improvement | Official Bias | M9 Bias | Official R2 | M9 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {ba['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {ba['mbe']:.4f} | {na['mbe']:.4f} | {ba['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {bo['rmse']:.4f} | {bn['rmse']:.4f} | {imp:.2f}% | {bo['mbe']:.4f} | {bn['mbe']:.4f} | {bo['r2']:.4f} | {bn['r2']:.4f} |\n\nBenchmark to beat: exploratory DTR-only two-sided shoulder = 9.07% high-DTR RMSE improvement. A strong result should exceed this while keeping DTR<=14.8 exactly unchanged.\n''';README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
