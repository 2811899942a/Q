#!/usr/bin/env python3
"""Fit a calibration-only DTR-triggered shoulder-contraction + skew HTEMP model.

Formal threshold DTRc=14.8 C is taken only from 2000-2016 calibration diagnostics.
2017-2024 remains independent validation.

For DTR>DTRc during daylight between Tmin-time t0 and sunset ts:
  y=(t-t0)/(ts-t0), p=(tpeak-t0)/(ts-t0)

Two anchor-preserving basis functions are used:
  B_width = 4*y*(1-y)*(y-p)^2       >=0 on both peak shoulders
  B_skew  = 4*y*(1-y)*(y-p)         <0 before peak, >0 after peak

Both are exactly zero at t0, modeled Tmax time (y=p), and sunset.
Correction:
  T_new = T_PL - excess*(beta_width*B_width + beta_skew*B_skew)

beta_width>0 contracts both hot shoulders. beta_skew>0 warms the pre-peak side and
cools the post-peak side, representing DTR-dependent asymmetry. Parameters are fitted
analytically using only 2000-2016 May-Sep observations.
"""
from __future__ import annotations
import csv,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'/'processed_51463';INFILE=DATA/'htemp_pointwise_2000_2024.csv'
README=DATA/'README_SHOULDER_SKEW_HTEMP.md';PARAM=DATA/'shoulder_skew_parameters.csv';VAL=DATA/'shoulder_skew_validation.csv';DTR=DATA/'shoulder_skew_validation_by_dtr.csv';HOUR=DATA/'shoulder_skew_validation_by_hour.csv'
DTRC=14.8;A=2.0;C=1.0

def mean(x):return statistics.mean(x) if x else float('nan')
def basis(r):
 d=float(r['formal_dtr_c']);hs=float(r['solar_hour'])
 if d<=DTRC:return 0.0,0.0
 sn=float(r['snup_solar_h']);sd=float(r['sndn_solar_h']);dl=float(r['dayl_h']);t0=sn+C;tp=t0+dl/2+A
 if not(t0<hs<sd) or sd<=t0:return 0.0,0.0
 y=(hs-t0)/(sd-t0);p=(tp-t0)/(sd-t0);ex=d-DTRC
 bw=ex*4*y*(1-y)*(y-p)**2;bs=ex*4*y*(1-y)*(y-p)
 return bw,bs

def fit(cal):
 # error_new=e-beta_w*bw-beta_s*bs
 a11=a22=a12=t1=t2=0.0
 for r in cal:
  x1,x2=basis(r);e=float(r['pred_c'])-float(r['obs_c']);a11+=x1*x1;a22+=x2*x2;a12+=x1*x2;t1+=x1*e;t2+=x2*e
 den=a11*a22-a12*a12
 if abs(den)<1e-12:return 0.0,0.0
 b1=(t1*a22-t2*a12)/den;b2=(t2*a11-t1*a12)/den
 # width should represent contraction; if negative, compare boundary beta_width=0.
 if b1<0:
  b1=0.0;b2=t2/a22 if a22>0 else 0.0
 return b1,b2

def pred(r,bw,bs):
 x1,x2=basis(r);return float(r['pred_c'])-bw*x1-bs*x2

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
 rows=[]
 with INFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if int(r['month']) in [5,6,7,8,9]:r['year']=int(r['solar_date'][:4]);rows.append(r)
 cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];bw,bs=fit(cal)
 with PARAM.open('w',newline='',encoding='utf-8-sig') as f:
  ff=['dtr_threshold_c','beta_width','beta_skew'];w=csv.DictWriter(f,fieldnames=ff);w.writeheader();w.writerow({'dtr_threshold_c':DTRC,'beta_width':bw,'beta_skew':bs})
 models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M8_SHOULDER_SKEW',lambda r:pred(r,bw,bs))];groups=[('May-Sep',val),('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
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
  for h in [5,8,9,11,12,14,15,17,18,20,23]:
   rs=[r for r in val if int(float(r['solar_hour']))==h];m=metric(rs,pf);m.update({'model':name,'solar_hour':h});hr.append(m)
 ff3=['model','solar_hour','n','rmse','mae','mbe','r2']
 with HOUR.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=ff3);w.writeheader();w.writerows([{k:r[k] for k in ff3} for r in hr])
 mm={(r['model'],r['group']):r for r in rec};bo=mm[('M0_OFFICIAL','DTR>=15')];bn=mm[('M8_SHOULDER_SKEW','DTR>=15')];ba=mm[('M0_OFFICIAL','May-Sep')];na=mm[('M8_SHOULDER_SKEW','May-Sep')];imp=100*(bo['rmse']-bn['rmse'])/bo['rmse'];impa=100*(ba['rmse']-na['rmse'])/ba['rmse']
 text=f'''# Urumqi DTR-triggered shoulder-contraction and skew HTEMP\n\n- Calibration-only trigger: **DTR > {DTRC:.1f} C**\n- Shoulder-width coefficient: **beta_width={bw:.4f}**\n- Asymmetry/skew coefficient: **beta_skew={bs:.4f}**\n\nThe two deformation bases are zero at Tmin-time, modeled Tmax, and sunset, so the daily anchors remain unchanged.\n\n## Independent validation 2017-2024\n\n| Scope | Official RMSE | M8 RMSE | Improvement | Official Bias | M8 Bias | Official R2 | M8 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {ba['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {ba['mbe']:.4f} | {na['mbe']:.4f} | {ba['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {bo['rmse']:.4f} | {bn['rmse']:.4f} | {imp:.2f}% | {bo['mbe']:.4f} | {bn['mbe']:.4f} | {bo['r2']:.4f} | {bn['r2']:.4f} |\n\nThis model is retained only if it clearly improves validation performance and keeps parameter magnitudes interpretable.\n''';README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
