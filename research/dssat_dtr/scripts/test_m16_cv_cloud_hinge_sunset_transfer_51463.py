#!/usr/bin/env python3
"""M16: cross-validated dense-station CLOUDS-hinge sunset-anchor transfer.

This is the final planned refinement of M15. The primary-station validation data
are never used to select the cloud gate or its amplitude.

Dense Diwopu sunset observations (2000-2016) select c0 by leave-one-year-out CV:
    X = max(0,DTR-14.8) * max(0,CLOUDS-c0)
    sunset_error ~= alpha * X, alpha>=0
For every CV fold alpha is fitted on the other calibration years. The c0 with the
smallest pooled held-out sunset RMSE is selected, then alpha is refitted once on
all dense calibration years. Dense 2017-2024 and primary 51463 2017-2024 remain
untouched validation.

The source-form curve uses the same physically monotonic M15 construction:
- Tmax unchanged;
- corrected sunset anchor TS1=max(TMIN, TS0-alpha*X);
- official normalized post-peak cooling progress is rescaled to TS1;
- official B=2.2 exponential night form is retained with its asymptote recomputed
  to connect TS1 to TMIN;
- DTR<=14.8 is exactly official HTEMP.
"""
from __future__ import annotations
import csv,math,statistics
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];MAIN=ROOT/'data'/'processed_51463';DENSE=ROOT/'data'/'processed_514635'
SUN=DENSE/'dense_sunset_anchor_daily.csv';PFILE=MAIN/'htemp_pointwise_2000_2024.csv';SFILE=MAIN/'main51463_dtr_srad_daily.csv'
README=MAIN/'README_M16_CV_CLOUD_HINGE_SUNSET.md';GRID=MAIN/'m16_dense_cv_cloud_grid.csv';PARAM=MAIN/'m16_parameters.csv';VAL=MAIN/'m16_validation.csv';DTR_OUT=MAIN/'m16_by_dtr.csv';HOUR_OUT=MAIN/'m16_by_hour.csv';CLOUD_OUT=MAIN/'m16_by_cloud_strata.csv';YEAR_OUT=MAIN/'m16_by_year.csv';SHAPE=MAIN/'m16_shape_checks.csv';DENSEVAL=MAIN/'m16_dense_sunset_validation.csv'
DTRC=14.8;LAT=43.7833;A=2.;B=2.2;C=1.;PI=3.14159;RAD=PI/180.;S0N=1368.;AMTRCS=.77

def mean(x):return statistics.mean(x) if x else float('nan')
def rmse(x):return math.sqrt(mean([z*z for z in x])) if x else float('nan')
def fit_alpha(rows,c0):
 sx2=sxy=0.
 for r in rows:
  x=max(0.,r['dtr_c']-DTRC)*max(0.,r['clouds']-c0);sx2+=x*x;sxy+=x*r['sunset_error_c']
 return max(0.,sxy/sx2) if sx2>0 else 0.
def cv_dense(cal):
 years=sorted(set(r['year'] for r in cal));grid=[]
 for i in range(81):
  c0=i*.01;sse=0.;n=0
  for y in years:
   tr=[r for r in cal if r['year']!=y];te=[r for r in cal if r['year']==y];alpha=fit_alpha(tr,c0)
   for r in te:
    x=max(0.,r['dtr_c']-DTRC)*max(0.,r['clouds']-c0);e=(r['sunset_error_c']-alpha*x);sse+=e*e;n+=1
  grid.append({'cloud_hinge_c0':c0,'loyo_n':n,'loyo_rmse':math.sqrt(sse/n)})
 return min(grid,key=lambda r:r['loyo_rmse']),grid
def solar(date,srad):
 doy=date.timetuple().tm_yday;dec=-23.45*math.cos(2*PI*(doy+10.)/365.);soc=math.tan(RAD*dec)*math.tan(RAD*LAT);soc=min(max(soc,-1.),1.);dl=min(max(12.+24.*math.asin(soc)/PI,0.),24.);su=12.-dl/2.;sd=12.+dl/2.;ss=math.sin(RAD*dec)*math.sin(RAD*LAT);cc=math.cos(RAD*dec)*math.cos(RAD*LAT);z=ss/cc if abs(cc)>1e-12 else 0.;z=min(max(z,-1.),1.);ds=3600.*(dl*ss+24./PI*cc*math.sqrt(max(0.,1.-z*z)));sc=AMTRCS*S0N*ds*1e-6;cl=min(max(1.-srad/sc,0.),1.) if sc>0 else 0.;return dl,su,sd,cl
def parts(tx,tn,dl,su,sd):
 mn=su+C;mx=mn+dl/2.+A;theta=.5*PI*(sd-mn)/(mx-mn);ts=tn+(tx-tn)*math.sin(theta);eb=math.exp(-B);ti=(tn-ts*eb)/(1.-eb);hd=24.+C-dl;return mn,mx,ts,ti,hd
def pl(h,tx,tn,dl,su,sd):
 mn,mx,ts,ti,hd=parts(tx,tn,dl,su,sd)
 if mn<=h<=sd:return tn+(tx-tn)*math.sin(.5*PI*(h-mn)/(mx-mn))
 tt=24.+h-sd if h<mn else h-sd;return ti+(ts-ti)*math.exp(-B*tt/hd)
def model(h,tx,tn,dl,su,sd,cl,c0,alpha):
 p0=pl(h,tx,tn,dl,su,sd);dtr=tx-tn
 if dtr<=DTRC:return p0,0.,False
 mn,mx,ts0,ti0,hd=parts(tx,tn,dl,su,sd);x=(dtr-DTRC)*max(0.,cl-c0);delta=alpha*x;ts1=max(tn,ts0-delta);cap=ts0-delta<tn
 if mx<h<=sd:
  den=tx-ts0;r=min(max((tx-p0)/den,0.),1.) if den>1e-12 else 0.;return tx-(tx-ts1)*r,ts0-ts1,cap
 if h>sd or h<mn:
  eb=math.exp(-B);ti1=(tn-ts1*eb)/(1.-eb);tt=24.+h-sd if h<mn else h-sd;return ti1+(ts1-ti1)*math.exp(-B*tt/hd),ts0-ts1,cap
 return p0,ts0-ts1,cap
def metric(rows,pf):
 if not rows:return {'n':0,'rmse':float('nan'),'mae':float('nan'),'mbe':float('nan'),'r2':float('nan')}
 o=[float(r['obs_c']) for r in rows];p=[pf(r) for r in rows];e=[b-a for a,b in zip(o,p)];rrm=math.sqrt(mean([x*x for x in e]));ma=mean([abs(x) for x in e]);mb=mean(e);mo=mean(o);mp=mean(p);so=sum((x-mo)**2 for x in o);sp=sum((x-mp)**2 for x in p);r=sum((a-mo)*(b-mp) for a,b in zip(o,p))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan');return {'n':len(rows),'rmse':rrm,'mae':ma,'mbe':mb,'r2':r*r}
def dbin(d):
 if d<10:return '<10'
 if d<15:return '10-<15'
 if d<18:return '15-<18'
 if d<20:return '18-<20'
 return '>=20'
def write(path,rows,fields):
 with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
 dense=[]
 with SUN.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   q={k:float(v) if k not in {'date'} else v for k,v in r.items()};q['year']=int(float(q['year']));dense.append(q)
 dcal=[r for r in dense if r['year']<=2016 and r['dtr_c']>DTRC];dval=[r for r in dense if r['year']>=2017 and r['dtr_c']>DTRC]
 best,grid=cv_dense(dcal);c0=float(best['cloud_hinge_c0']);alpha=fit_alpha(dcal,c0)
 write(GRID,grid,['cloud_hinge_c0','loyo_n','loyo_rmse'])
 def dscore(rs):
  raw=[r['sunset_error_c'] for r in rs];cor=[]
  for r in rs:
   x=max(0.,r['dtr_c']-DTRC)*max(0.,r['clouds']-c0);cor.append(r['sunset_error_c']-alpha*x)
  return {'n':len(rs),'raw_bias':mean(raw),'raw_rmse':rmse(raw),'corrected_bias':mean(cor),'corrected_rmse':rmse(cor)}
 ds=[]
 for lab,rs in [('DenseCalibration',dcal),('DenseValidation',dval)]:a=dscore(rs);a['split']=lab;ds.append(a)
 write(DENSEVAL,ds,['split','n','raw_bias','raw_rmse','corrected_bias','corrected_rmse'])
 srad={}
 with SFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):srad[r['date']]=float(r['srad'])
 rows=[]
 with PFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in srad:continue
   date=datetime.strptime(r['solar_date'],'%Y-%m-%d').date();dl,su,sd,cl=solar(date,srad[r['solar_date']]);r['year']=date.year;r['dayl']=dl;r['snup']=su;r['sndn']=sd;r['clouds']=cl;rows.append(r)
 val=[r for r in rows if r['year']>=2017]
 def pm(r):return model(float(r['solar_hour']),float(r['tmax_ghcn_c']),float(r['tmin_ghcn_c']),r['dayl'],r['snup'],r['sndn'],r['clouds'],c0,alpha)[0]
 models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M16_CV_CLOUD_HINGE_TS',pm)];groups=[('May-Sep',val),('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
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
 for lab,lo,hi in [('LowCloud',-1,q1),('MidCloud',q1,q2),('HighCloud',q2,2)]:
  rs=[r for r in val if float(r['formal_dtr_c'])>=15 and lo<=r['clouds']<hi]
  for name,pf in models:m=metric(rs,pf);m.update({'model':name,'cloud_group':lab,'n_days':len(set(r['solar_date'] for r in rs))});cr.append(m)
 write(DTR_OUT,[{k:r[k] for k in ['model','dtr_bin','n','rmse','mae','mbe','r2']} for r in dr],['model','dtr_bin','n','rmse','mae','mbe','r2']);write(HOUR_OUT,[{k:r[k] for k in ['model','solar_hour','n','rmse','mae','mbe','r2']} for r in hr],['model','solar_hour','n','rmse','mae','mbe','r2']);write(YEAR_OUT,[{k:r[k] for k in ['model','year','n_days','n','rmse','mae','mbe','r2']} for r in yr],['model','year','n_days','n','rmse','mae','mbe','r2']);write(CLOUD_OUT,[{k:r[k] for k in ['model','cloud_group','n_days','n','rmse','mae','mbe','r2']} for r in cr],['model','cloud_group','n_days','n','rmse','mae','mbe','r2'])
 meta={}
 for r in rows:meta.setdefault(r['solar_date'],r)
 checks=[]
 for ds0,r in meta.items():
  if float(r['formal_dtr_c'])<=DTRC:continue
  tx=float(r['tmax_ghcn_c']);tn=float(r['tmin_ghcn_c']);vals=[];cap=False;delta=0.
  for i in range(481):
   h=i*.05;pn,de,cp=model(h,tx,tn,r['dayl'],r['snup'],r['sndn'],r['clouds'],c0,alpha);vals.append((h,pn));delta=max(delta,de);cap=cap or cp
  mn=r['snup']+C;mx=mn+r['dayl']/2.+A;rise=[z for z in vals if mn<=z[0]<=mx];aft=[z for z in vals if mx<=z[0]<=24];pre=[z for z in vals if 0<=z[0]<=mn];rd=[rise[i+1][1]-rise[i][1] for i in range(len(rise)-1)];ad=[aft[i+1][1]-aft[i][1] for i in range(len(aft)-1)];pd=[pre[i+1][1]-pre[i][1] for i in range(len(pre)-1)];checks.append({'solar_date':ds0,'year':r['year'],'sunset_reduction_c':delta,'ts_capped_at_tmin':'YES' if cap else 'NO','rise_monotonic':'YES' if min(rd)>=-1e-8 else 'NO','postpeak_to_midnight_monotonic':'YES' if max(ad)<=1e-8 else 'NO','midnight_to_tmin_monotonic':'YES' if max(pd)<=1e-8 else 'NO','below_tmin_c':max(0.,tn-min(x[1] for x in vals)),'above_tmax_c':max(0.,max(x[1] for x in vals)-tx)})
 write(SHAPE,checks,['solar_date','year','sunset_reduction_c','ts_capped_at_tmin','rise_monotonic','postpeak_to_midnight_monotonic','midnight_to_tmin_monotonic','below_tmin_c','above_tmax_c']);vc=[r for r in checks if r['year']>=2017];bad=sum(r['rise_monotonic']=='NO' or r['postpeak_to_midnight_monotonic']=='NO' or r['midnight_to_tmin_monotonic']=='NO' or r['below_tmin_c']>1e-6 or r['above_tmax_c']>1e-6 for r in vc);caps=sum(r['ts_capped_at_tmin']=='YES' for r in vc)
 mm={(r['model'],r['group']):r for r in rec};o=mm[('M0_OFFICIAL','DTR>=15')];n=mm[('M16_CV_CLOUD_HINGE_TS','DTR>=15')];oa=mm[('M0_OFFICIAL','May-Sep')];na=mm[('M16_CV_CLOUD_HINGE_TS','May-Sep')];imp=100*(o['rmse']-n['rmse'])/o['rmse'];impa=100*(oa['rmse']-na['rmse'])/oa['rmse'];dg=100*(ds[1]['raw_rmse']-ds[1]['corrected_rmse'])/ds[1]['raw_rmse']
 boundary=(abs(c0-0.)<1e-12 or abs(c0-.8)<1e-12)
 write(PARAM,[{'dtr_threshold_c':DTRC,'cloud_hinge_c0':c0,'alpha_sunset':alpha,'dense_loyo_rmse':best['loyo_rmse'],'c0_hit_search_boundary':boundary,'primary_validation_shape_violations':bad,'primary_validation_ts_caps':caps}],['dtr_threshold_c','cloud_hinge_c0','alpha_sunset','dense_loyo_rmse','c0_hit_search_boundary','primary_validation_shape_violations','primary_validation_ts_caps'])
 decision='PREFERRED_SOURCE_CANDIDATE' if bad==0 and imp>8.65 and not boundary and n['mbe']>-1 else 'KEEP_M15_IF_BETTER'
 text=f'''# M16 cross-validated cloud-hinge sunset-anchor transfer\n\nNo primary-station validation information was used to choose M16 parameters.\n\n- Dense calibration-only LOYO selected `CLOUDS` hinge: **c0={c0:.3f}** (boundary={boundary})\n- Dense full-calibration alpha: **{alpha:.4f}**\n- Dense independent sunset validation RMSE gain: **{dg:.2f}%**\n- Primary validation physical violations: **{bad}/{len(vc)}**\n- Primary validation TS caps at Tmin: **{caps}/{len(vc)}**\n\n## Primary 51463 independent transfer validation 2017-2024\n| Scope | Official RMSE | M16 RMSE | Improvement | Official Bias | M16 Bias | Official R2 | M16 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {oa['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {oa['mbe']:.4f} | {na['mbe']:.4f} | {oa['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {o['rmse']:.4f} | {n['rmse']:.4f} | {imp:.2f}% | {o['mbe']:.4f} | {n['mbe']:.4f} | {o['r2']:.4f} | {n['r2']:.4f} |\n\nM15 reference = **8.65%** high-DTR improvement.\n\nAutomated decision: **{decision}**.\n''';README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
