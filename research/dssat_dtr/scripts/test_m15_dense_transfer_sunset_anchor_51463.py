#!/usr/bin/env python3
"""M15: cross-station transfer of a DTR x CLOUDS sunset-anchor correction.

The correction magnitude is NOT fitted at the primary station. It is frozen from
Diwopu 51463599999 calibration (2000-2016) sunset observations, then transferred
to primary station 51463099999 independent validation (2017-2024).

Mechanism
---------
DTRc = 14.8 C (primary calibration-only threshold).
Dense-station calibration gave:
    delta_TS = alpha * max(0,DTR-DTRc) * CLOUDS
with alpha read from `dense_sunset_anchor_summary.csv`.

For high-DTR days:
1. Reduce the official Parton-Logan sunset anchor:
       TS1 = max(TMIN, TS0 - delta_TS)
2. From modeled Tmax to sunset, preserve the official normalized cooling progress
   but scale it to the new endpoint TS1. This is monotonic and exactly preserves Tmax.
3. At night, retain the official Parton-Logan exponential decay parameter B=2.2,
   recomputing the exponential asymptote so the curve connects TS1 to TMIN.
4. Pre-peak daytime HTEMP is unchanged.
5. DTR<=14.8 C is bit-for-formula identical to official HTEMP.

This test asks whether a mechanism fitted at the dense second Urumqi station can
transfer without refitting to the primary station. If successful it is stronger
than single-station curve tuning.
"""
from __future__ import annotations
import csv,math,statistics
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/'data'/'processed_51463';DENSE=ROOT/'data'/'processed_514635'
PFILE=MAIN/'htemp_pointwise_2000_2024.csv';SFILE=MAIN/'main51463_dtr_srad_daily.csv';ALPHA_FILE=DENSE/'dense_sunset_anchor_summary.csv'
README=MAIN/'README_M15_DENSE_TRANSFER_SUNSET.md';PARAM=MAIN/'m15_dense_transfer_parameters.csv';VAL=MAIN/'m15_dense_transfer_validation.csv';DTR_OUT=MAIN/'m15_dense_transfer_by_dtr.csv';HOUR_OUT=MAIN/'m15_dense_transfer_by_hour.csv';CLOUD_OUT=MAIN/'m15_dense_transfer_by_cloud_strata.csv';YEAR_OUT=MAIN/'m15_dense_transfer_by_year.csv';SHAPE=MAIN/'m15_dense_transfer_shape_checks.csv'
DTRC=14.8;LAT=43.7833;A=2.;B=2.2;C=1.;PI=3.14159;RAD=PI/180.;S0N=1368.;AMTRCS=.77

def mean(x):return statistics.mean(x) if x else float('nan')
def solar(date,srad):
 doy=date.timetuple().tm_yday;dec=-23.45*math.cos(2*PI*(doy+10.)/365.);soc=math.tan(RAD*dec)*math.tan(RAD*LAT);soc=min(max(soc,-1.),1.);dl=min(max(12.+24.*math.asin(soc)/PI,0.),24.);su=12.-dl/2.;sd=12.+dl/2.;ss=math.sin(RAD*dec)*math.sin(RAD*LAT);cc=math.cos(RAD*dec)*math.cos(RAD*LAT);z=ss/cc if abs(cc)>1e-12 else 0.;z=min(max(z,-1.),1.);ds=3600.*(dl*ss+24./PI*cc*math.sqrt(max(0.,1.-z*z)));sc=AMTRCS*S0N*ds*1e-6;cl=min(max(1.-srad/sc,0.),1.) if sc>0 else 0.;return dl,su,sd,cl
def parts(tx,tn,dl,su,sd):
 mn=su+C;mx=mn+dl/2.+A;theta=.5*PI*(sd-mn)/(mx-mn);ts=tn+(tx-tn)*math.sin(theta);eb=math.exp(-B);ti=(tn-ts*eb)/(1.-eb);hd=24.+C-dl;return mn,mx,ts,ti,hd
def pl(h,tx,tn,dl,su,sd):
 mn,mx,ts,ti,hd=parts(tx,tn,dl,su,sd)
 if mn<=h<=sd:return tn+(tx-tn)*math.sin(.5*PI*(h-mn)/(mx-mn))
 tt=24.+h-sd if h<mn else h-sd;return ti+(ts-ti)*math.exp(-B*tt/hd)
def m15(h,tx,tn,dl,su,sd,cl,alpha):
 p0=pl(h,tx,tn,dl,su,sd);dtr=tx-tn
 if dtr<=DTRC:return p0,0.,False
 mn,mx,ts0,ti0,hd=parts(tx,tn,dl,su,sd);delta=alpha*(dtr-DTRC)*cl;ts1=max(tn,ts0-delta);capped=(ts0-delta)<tn
 if mx<h<=sd:
  den=tx-ts0
  if den<=1e-12:return p0,ts0-ts1,capped
  r=min(max((tx-p0)/den,0.),1.)
  return tx-(tx-ts1)*r,ts0-ts1,capped
 if h>sd or h<mn:
  eb=math.exp(-B);ti1=(tn-ts1*eb)/(1.-eb);tt=24.+h-sd if h<mn else h-sd
  return ti1+(ts1-ti1)*math.exp(-B*tt/hd),ts0-ts1,capped
 return p0,ts0-ts1,capped
def metric(rows,pf):
 if not rows:return {'n':0,'rmse':float('nan'),'mae':float('nan'),'mbe':float('nan'),'r2':float('nan')}
 o=[float(r['obs_c']) for r in rows];p=[pf(r) for r in rows];e=[b-a for a,b in zip(o,p)];rm=math.sqrt(mean([x*x for x in e]));ma=mean([abs(x) for x in e]);mb=mean(e);mo=mean(o);mp=mean(p);so=sum((x-mo)**2 for x in o);sp=sum((x-mp)**2 for x in p);rr=sum((a-mo)*(b-mp) for a,b in zip(o,p))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan');return {'n':len(rows),'rmse':rm,'mae':ma,'mbe':mb,'r2':rr*rr}
def dbin(d):
 if d<10:return '<10'
 if d<15:return '10-<15'
 if d<18:return '15-<18'
 if d<20:return '18-<20'
 return '>=20'
def write(path,rows,fields):
 with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
 # Freeze alpha from the already completed dense-station calibration result.
 with ALPHA_FILE.open('r',newline='',encoding='utf-8-sig') as f:ar=list(csv.DictReader(f))
 calrow=next(r for r in ar if r['split']=='Calibration_2000_2016');alpha=float(calrow['alpha_from_calibration'])
 srad={}
 with SFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):srad[r['date']]=float(r['srad'])
 rows=[]
 with PFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in srad:continue
   date=datetime.strptime(r['solar_date'],'%Y-%m-%d').date();dl,su,sd,cl=solar(date,srad[r['solar_date']]);r['year']=date.year;r['dayl']=dl;r['snup']=su;r['sndn']=sd;r['clouds']=cl;rows.append(r)
 val=[r for r in rows if r['year']>=2017]
 def pm(r):return m15(float(r['solar_hour']),float(r['tmax_ghcn_c']),float(r['tmin_ghcn_c']),r['dayl'],r['snup'],r['sndn'],r['clouds'],alpha)[0]
 models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M15_DENSE_TRANSFER_TS',pm)]
 groups=[('May-Sep',val),('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
 rec=[]
 for name,pf in models:
  for g,rs in groups:m=metric(rs,pf);m.update({'model':name,'group':g});rec.append(m)
 write(VAL,[{k:r[k] for k in ['model','group','n','rmse','mae','mbe','r2']} for r in rec],['model','group','n','rmse','mae','mbe','r2'])
 dr=[];hr=[];yr=[];cr=[]
 for name,pf in models:
  for b in ['<10','10-<15','15-<18','18-<20','>=20']:
   rs=[r for r in val if dbin(float(r['formal_dtr_c']))==b];m=metric(rs,pf);m.update({'model':name,'dtr_bin':b});dr.append(m)
  for h in [2,5,8,9,11,12,14,15,17,18,20,23]:
   rs=[r for r in val if int(float(r['solar_hour']))==h];m=metric(rs,pf);m.update({'model':name,'solar_hour':h});hr.append(m)
  for y in sorted(set(r['year'] for r in val)):
   rs=[r for r in val if r['year']==y and float(r['formal_dtr_c'])>=15]
   if rs:m=metric(rs,pf);m.update({'model':name,'year':y,'n_days':len(set(r['solar_date'] for r in rs))});yr.append(m)
 cal=[r for r in rows if r['year']<=2016 and float(r['formal_dtr_c'])>=15];caldays={r['solar_date']:r['clouds'] for r in cal};vv=sorted(caldays.values());q1=vv[len(vv)//3];q2=vv[2*len(vv)//3]
 for label,lo,hi in [('LowCloud',-1,q1),('MidCloud',q1,q2),('HighCloud',q2,2)]:
  rs=[r for r in val if float(r['formal_dtr_c'])>=15 and lo<=r['clouds']<hi]
  for name,pf in models:m=metric(rs,pf);m.update({'model':name,'cloud_group':label,'n_days':len(set(r['solar_date'] for r in rs))});cr.append(m)
 write(DTR_OUT,[{k:r[k] for k in ['model','dtr_bin','n','rmse','mae','mbe','r2']} for r in dr],['model','dtr_bin','n','rmse','mae','mbe','r2']);write(HOUR_OUT,[{k:r[k] for k in ['model','solar_hour','n','rmse','mae','mbe','r2']} for r in hr],['model','solar_hour','n','rmse','mae','mbe','r2']);write(YEAR_OUT,[{k:r[k] for k in ['model','year','n_days','n','rmse','mae','mbe','r2']} for r in yr],['model','year','n_days','n','rmse','mae','mbe','r2']);write(CLOUD_OUT,[{k:r[k] for k in ['model','cloud_group','n_days','n','rmse','mae','mbe','r2']} for r in cr],['model','cloud_group','n_days','n','rmse','mae','mbe','r2'])
 # Complete same-day curve QA and cap frequency.
 meta={}
 for r in rows:meta.setdefault(r['solar_date'],r)
 checks=[]
 for ds,r in meta.items():
  if float(r['formal_dtr_c'])<=DTRC:continue
  tx=float(r['tmax_ghcn_c']);tn=float(r['tmin_ghcn_c']);vals=[];cap=False;delta=0.
  for i in range(481):
   h=i*.05;pn,de,cp=m15(h,tx,tn,r['dayl'],r['snup'],r['sndn'],r['clouds'],alpha);vals.append((h,pn));delta=max(delta,de);cap=cap or cp
  mn=r['snup']+C;mx=mn+r['dayl']/2.+A;rise=[z for z in vals if mn<=z[0]<=mx];fall=[z for z in vals if mx<=z[0]<=24]+[z for z in vals if 0<=z[0]<=mn]
  rd=[rise[i+1][1]-rise[i][1] for i in range(len(rise)-1)]
  # physical within continuous segments: post-peak to midnight and midnight to Tmin separately
  aft=[z for z in vals if mx<=z[0]<=24];pre=[z for z in vals if 0<=z[0]<=mn];ad=[aft[i+1][1]-aft[i][1] for i in range(len(aft)-1)];pd=[pre[i+1][1]-pre[i][1] for i in range(len(pre)-1)]
  checks.append({'solar_date':ds,'year':r['year'],'dtr_c':r['formal_dtr_c'],'clouds':r['clouds'],'sunset_reduction_c':delta,'ts_capped_at_tmin':'YES' if cap else 'NO','rise_monotonic':'YES' if min(rd)>=-1e-8 else 'NO','postpeak_to_midnight_monotonic':'YES' if max(ad)<=1e-8 else 'NO','midnight_to_tmin_monotonic':'YES' if max(pd)<=1e-8 else 'NO','below_tmin_c':max(0.,tn-min(z[1] for z in vals)),'above_tmax_c':max(0.,max(z[1] for z in vals)-tx)})
 write(SHAPE,checks,['solar_date','year','dtr_c','clouds','sunset_reduction_c','ts_capped_at_tmin','rise_monotonic','postpeak_to_midnight_monotonic','midnight_to_tmin_monotonic','below_tmin_c','above_tmax_c'])
 vc=[r for r in checks if r['year']>=2017];bad=sum(r['rise_monotonic']=='NO' or r['postpeak_to_midnight_monotonic']=='NO' or r['midnight_to_tmin_monotonic']=='NO' or r['below_tmin_c']>1e-6 or r['above_tmax_c']>1e-6 for r in vc);caps=sum(r['ts_capped_at_tmin']=='YES' for r in vc)
 mm={(r['model'],r['group']):r for r in rec};o=mm[('M0_OFFICIAL','DTR>=15')];n=mm[('M15_DENSE_TRANSFER_TS','DTR>=15')];oa=mm[('M0_OFFICIAL','May-Sep')];na=mm[('M15_DENSE_TRANSFER_TS','May-Sep')];imp=100*(o['rmse']-n['rmse'])/o['rmse'];impa=100*(oa['rmse']-na['rmse'])/oa['rmse']
 write(PARAM,[{'source_station':'51463599999','source_calibration':'2000-2016','target_station':'51463099999','target_validation':'2017-2024','dtr_threshold_c':DTRC,'alpha_sunset':alpha,'validation_shape_violations':bad,'validation_ts_caps':caps}],['source_station','source_calibration','target_station','target_validation','dtr_threshold_c','alpha_sunset','validation_shape_violations','validation_ts_caps'])
 decision='CROSS_STATION_SOURCE_CANDIDATE' if bad==0 and imp>=8 and n['mbe']>-1.0 else 'REVIEW_REQUIRED'
 text=f'''# M15 dense-station sunset-anchor transfer to primary Urumqi station\n\n**No M15 parameter was fitted on primary-station validation data.**\n\n- Source mechanism station: dense Diwopu `51463599999`, calibration 2000-2016.\n- Frozen sunset coefficient: **alpha={alpha:.4f}**.\n- Target station: `51463099999`, validation 2017-2024.\n- DTR trigger: **>{DTRC:.1f} C**.\n- Validation complete-curve physical violations: **{bad}/{len(vc)}**.\n- Validation days where corrected TS was capped at Tmin: **{caps}/{len(vc)}**.\n\n## Independent cross-station target validation\n| Scope | Official RMSE | M15 RMSE | Improvement | Official Bias | M15 Bias | Official R2 | M15 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {oa['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {oa['mbe']:.4f} | {na['mbe']:.4f} | {oa['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {o['rmse']:.4f} | {n['rmse']:.4f} | {imp:.2f}% | {o['mbe']:.4f} | {n['mbe']:.4f} | {o['r2']:.4f} | {n['r2']:.4f} |\n\nReference: M14 (single-station monotonic warp) = 7.43% high-DTR improvement; M10 statistical upper reference = 13.71%.\n\nAutomated decision: **{decision}**.\n''';README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
