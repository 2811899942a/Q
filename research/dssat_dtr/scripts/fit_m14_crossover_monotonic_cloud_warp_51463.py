#!/usr/bin/env python3
"""M14: robust calibration-crossover monotonic DTR x CLOUDS HTEMP shape warp.

M13 was physically valid but started the pre-peak shape change at solar noon,
although calibration residuals indicate the cold-to-warm transition occurs earlier.
M14 derives a single crossover time H0 from 2000-2016 high-DTR observations only.
Because the sparse three-hourly checkpoints contain strong outliers, the crossover
is defined from supported hourly-bin MEDIAN residuals, with interpolation between
the mean actual solar times of the two bracketing bins. Validation years never
participate in H0 or coefficient selection.

For H0 < h < modeled Tmax:
    q = (T_PL - T_PL(H0)) / (TMAX - T_PL(H0))
    q_new = q ** p_pre
For modeled Tmax < h < sunset:
    q = (T_PL - T_sunset) / (TMAX - T_sunset)
    q_new = q ** p_post
where
    p = 1 + k * (DTR-DTRc) * CLOUDS, k >= 0.

The transform is monotonic and endpoint-preserving by construction.
DTRc=14.8 C is frozen. H0 and k values use calibration data only.
"""
from __future__ import annotations
import csv, math, statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'processed_51463'
PFILE=DATA/'htemp_pointwise_2000_2024.csv'; SFILE=DATA/'main51463_dtr_srad_daily.csv'
README=DATA/'README_M14_CROSSOVER_MONOTONIC.md'; CROSS=DATA/'m14_calibration_crossover.csv'; PARAM=DATA/'m14_parameters.csv'; VAL=DATA/'m14_validation.csv'; DTR_OUT=DATA/'m14_by_dtr.csv'; HOUR_OUT=DATA/'m14_by_hour.csv'; CLOUD_OUT=DATA/'m14_by_cloud_strata.csv'; YEAR_OUT=DATA/'m14_by_year.csv'; SHAPE=DATA/'m14_shape_checks.csv'
DTRC=14.8;LAT=43.7833;A=2.;B=2.2;C=1.;PI=3.14159;RAD=PI/180.;S0N=1368.;AMTRCS=.77

def mean(x):return statistics.mean(x) if x else float('nan')
def dssat_solar(date,srad):
 doy=date.timetuple().tm_yday;dec=-23.45*math.cos(2*PI*(doy+10.)/365.);soc=math.tan(RAD*dec)*math.tan(RAD*LAT);soc=min(max(soc,-1.),1.);dl=min(max(12.+24.*math.asin(soc)/PI,0.),24.);su=12.-dl/2.;sd=12.+dl/2.;ss=math.sin(RAD*dec)*math.sin(RAD*LAT);cc=math.cos(RAD*dec)*math.cos(RAD*LAT);z=ss/cc if abs(cc)>1e-12 else 0.;z=min(max(z,-1.),1.);ds=3600.*(dl*ss+24./PI*cc*math.sqrt(max(0.,1.-z*z)));sc=AMTRCS*S0N*ds*1e-6;cl=min(max(1.-srad/sc,0.),1.) if sc>0 else 0.;return dl,su,sd,cl
def pl(h,tx,tn,dl,su,sd):
 mn=su+C;mx=mn+dl/2.+A;t=.5*PI*(sd-mn)/(mx-mn);ts=tn+(tx-tn)*math.sin(t);ti=(tn-ts*math.exp(-B))/(1.-math.exp(-B));hd=24.+C-dl
 if mn<=h<=sd:return tn+(tx-tn)*math.sin(.5*PI*(h-mn)/(mx-mn))
 tt=24.+h-sd if h<mn else h-sd;return ti+(ts-ti)*math.exp(-B*tt/hd)
def derive_h0(cal):
 bins=defaultdict(list)
 for r in cal:
  if float(r['formal_dtr_c'])<=DTRC:continue
  h=int(math.floor(float(r['solar_hour'])))
  if 6<=h<=13:bins[h].append((float(r['solar_hour']),float(r['error_c'])))
 rows=[]
 for h in sorted(bins):
  vals=bins[h]
  if len(vals)>=15:
   rows.append({'hour_bin':h,'n':len(vals),'mean_actual_solar_hour':mean([x[0] for x in vals]),'mean_bias':mean([x[1] for x in vals]),'median_bias':statistics.median([x[1] for x in vals])})
 candidates=[]
 for a,b in zip(rows,rows[1:]):
  if a['median_bias']<=0. and b['median_bias']>0.:
   x0=a['mean_actual_solar_hour'];x1=b['mean_actual_solar_hour'];y0=a['median_bias'];y1=b['median_bias'];h0=x0+(0.-y0)*(x1-x0)/(y1-y0);candidates.append((h0,a,b))
 if not candidates:raise RuntimeError('No supported calibration median-residual negative-to-positive crossover found')
 h0,a,b=candidates[-1]
 return h0,rows,a,b
def branch(r,h0):
 h=float(r['solar_hour']);dl=r['dayl'];su=r['snup'];sd=r['sndn'];mx=su+C+dl/2.+A;tx=float(r['tmax_ghcn_c']);tn=float(r['tmin_ghcn_c']);p0=float(r['pred_c'])
 if h0<h<mx:
  lo=pl(h0,tx,tn,dl,su,sd);hi=tx;den=hi-lo
  if den<=1e-9:return 'none',0.,lo,hi
  return 'pre',min(max((p0-lo)/den,0.),1.),lo,hi
 if mx<h<sd:
  lo=pl(sd,tx,tn,dl,su,sd);hi=tx;den=hi-lo
  if den<=1e-9:return 'none',0.,lo,hi
  return 'post',min(max((p0-lo)/den,0.),1.),lo,hi
 return 'none',0.,0.,0.
def transform(r,h0,kp,kq):
 p0=float(r['pred_c']);d=float(r['formal_dtr_c'])
 if d<=DTRC:return p0
 br,q,lo,hi=branch(r,h0)
 if br=='none':return p0
 k=kp if br=='pre' else kq;expo=1.+k*(d-DTRC)*r['clouds'];return lo+(hi-lo)*(q**expo)
def fit(rows,h0,which):
 prep=[]
 for r in rows:
  if float(r['formal_dtr_c'])<=DTRC:continue
  br,q,lo,hi=branch(r,h0)
  if br==which:prep.append((q,lo,hi,(float(r['formal_dtr_c'])-DTRC)*r['clouds'],float(r['obs_c'])))
 best=None
 for i in range(4001):
  k=i*.005
  s=0.
  for q,lo,hi,e,o in prep:
   pr=lo+(hi-lo)*(q**(1.+k*e));s+=(pr-o)**2
  if prep and (best is None or s<best[0]):best=(s,k,len(prep),math.sqrt(s/len(prep)))
 return best
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
 srad={}
 with SFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):srad[r['date']]=float(r['srad'])
 rows=[]
 with PFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in srad:continue
   date=datetime.strptime(r['solar_date'],'%Y-%m-%d').date();dl,su,sd,cl=dssat_solar(date,srad[r['solar_date']]);r['year']=date.year;r['dayl']=dl;r['snup']=su;r['sndn']=sd;r['clouds']=cl;rows.append(r)
 cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017]
 h0,crossrows,ca,cb=derive_h0(cal);write(CROSS,crossrows,['hour_bin','n','mean_actual_solar_hour','mean_bias','median_bias'])
 bp=fit(cal,h0,'pre');bq=fit(cal,h0,'post');kp=bp[1];kq=bq[1];hitp=abs(kp-20.)<1e-12;hitq=abs(kq-20.)<1e-12
 write(PARAM,[{'dtr_threshold_c':DTRC,'crossover_solar_hour':h0,'cross_left_bin':ca['hour_bin'],'cross_left_median_bias':ca['median_bias'],'cross_right_bin':cb['hour_bin'],'cross_right_median_bias':cb['median_bias'],'k_pre':kp,'k_post':kq,'n_pre':bp[2],'n_post':bq[2],'pre_hit_upper_bound':hitp,'post_hit_upper_bound':hitq}],['dtr_threshold_c','crossover_solar_hour','cross_left_bin','cross_left_median_bias','cross_right_bin','cross_right_median_bias','k_pre','k_post','n_pre','n_post','pre_hit_upper_bound','post_hit_upper_bound'])
 models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M14_CROSSOVER_MONOTONIC',lambda r:transform(r,h0,kp,kq))];groups=[('May-Sep',val),('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
 rec=[]
 for name,pf in models:
  for g,rs in groups:m=metric(rs,pf);m.update({'model':name,'group':g});rec.append(m)
 write(VAL,[{k:r[k] for k in ['model','group','n','rmse','mae','mbe','r2']} for r in rec],['model','group','n','rmse','mae','mbe','r2'])
 dr=[];hr=[];cr=[];yr=[]
 for name,pf in models:
  for b in ['<10','10-<15','15-<18','18-<20','>=20']:
   rs=[r for r in val if dbin(float(r['formal_dtr_c']))==b];m=metric(rs,pf);m.update({'model':name,'dtr_bin':b});dr.append(m)
  for h in [5,8,9,11,12,14,15,17,18,20,23]:
   rs=[r for r in val if int(float(r['solar_hour']))==h];m=metric(rs,pf);m.update({'model':name,'solar_hour':h});hr.append(m)
  for y in sorted(set(r['year'] for r in val)):
   rs=[r for r in val if r['year']==y and float(r['formal_dtr_c'])>=15]
   if rs:m=metric(rs,pf);m.update({'model':name,'year':y,'n_days':len(set(r['solar_date'] for r in rs))});yr.append(m)
 caldays={r['solar_date']:r['clouds'] for r in cal if float(r['formal_dtr_c'])>=15};vv=sorted(caldays.values());q1=vv[len(vv)//3];q2=vv[2*len(vv)//3]
 for label,lo,hi in [('LowCloud',-1,q1),('MidCloud',q1,q2),('HighCloud',q2,2)]:
  rs=[r for r in val if float(r['formal_dtr_c'])>=15 and lo<=r['clouds']<hi]
  for name,pf in models:m=metric(rs,pf);m.update({'model':name,'cloud_group':label,'n_days':len(set(r['solar_date'] for r in rs))});cr.append(m)
 write(DTR_OUT,[{k:r[k] for k in ['model','dtr_bin','n','rmse','mae','mbe','r2']} for r in dr],['model','dtr_bin','n','rmse','mae','mbe','r2']);write(HOUR_OUT,[{k:r[k] for k in ['model','solar_hour','n','rmse','mae','mbe','r2']} for r in hr],['model','solar_hour','n','rmse','mae','mbe','r2']);write(CLOUD_OUT,[{k:r[k] for k in ['model','cloud_group','n_days','n','rmse','mae','mbe','r2']} for r in cr],['model','cloud_group','n_days','n','rmse','mae','mbe','r2']);write(YEAR_OUT,[{k:r[k] for k in ['model','year','n_days','n','rmse','mae','mbe','r2']} for r in yr],['model','year','n_days','n','rmse','mae','mbe','r2'])
 meta={}
 for r in rows:meta.setdefault(r['solar_date'],r)
 checks=[]
 for ds,r in meta.items():
  if float(r['formal_dtr_c'])<=DTRC:continue
  tx=float(r['tmax_ghcn_c']);tn=float(r['tmin_ghcn_c']);dl=r['dayl'];su=r['snup'];sd=r['sndn'];mx=su+C+dl/2.+A;vals=[]
  for i in range(481):
   h=i*.05;p0=pl(h,tx,tn,dl,su,sd);rr=dict(r);rr['solar_hour']=str(h);rr['pred_c']=str(p0);vals.append((h,transform(rr,h0,kp,kq)))
  rise=[z for z in vals if su+C<=z[0]<=mx];fall=[z for z in vals if mx<=z[0]<=sd];rd=[rise[i+1][1]-rise[i][1] for i in range(len(rise)-1)];fd=[fall[i+1][1]-fall[i][1] for i in range(len(fall)-1)];checks.append({'solar_date':ds,'year':r['year'],'rise_monotonic':'YES' if min(rd)>=-1e-8 else 'NO','fall_monotonic':'YES' if max(fd)<=1e-8 else 'NO','below_tmin_c':max(0.,tn-min(x[1] for x in vals)),'above_tmax_c':max(0.,max(x[1] for x in vals)-tx)})
 write(SHAPE,checks,['solar_date','year','rise_monotonic','fall_monotonic','below_tmin_c','above_tmax_c']);vc=[r for r in checks if r['year']>=2017];bad=sum(r['rise_monotonic']=='NO' or r['fall_monotonic']=='NO' or r['below_tmin_c']>1e-6 or r['above_tmax_c']>1e-6 for r in vc)
 mm={(r['model'],r['group']):r for r in rec};o=mm[('M0_OFFICIAL','DTR>=15')];n=mm[('M14_CROSSOVER_MONOTONIC','DTR>=15')];oa=mm[('M0_OFFICIAL','May-Sep')];na=mm[('M14_CROSSOVER_MONOTONIC','May-Sep')];imp=100*(o['rmse']-n['rmse'])/o['rmse'];impa=100*(oa['rmse']-na['rmse'])/oa['rmse'];decision='SOURCE_CANDIDATE' if bad==0 and imp>=8 and not hitp and not hitq else 'REVIEW_REQUIRED'
 text=f'''# M14 robust calibration-crossover monotonic CLOUDS HTEMP\n\n- Formal DTR trigger: **>{DTRC:.1f} C**\n- Calibration-only median-residual crossover H0: **{h0:.3f} solar hour**\n- Robust crossing bracket: hour bins {ca['hour_bin']} (median Bias {ca['median_bias']:.3f} C) -> {cb['hour_bin']} (median Bias {cb['median_bias']:.3f} C)\n- k_pre = **{kp:.4f}**, k_post = **{kq:.4f}**\n- upper-bound hits: pre={hitp}, post={hitq}\n- validation full-curve physical violations: **{bad}/{len(vc)}**\n\n## Independent validation 2017-2024\n| Scope | Official RMSE | M14 RMSE | Improvement | Official Bias | M14 Bias | Official R2 | M14 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {oa['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {oa['mbe']:.4f} | {na['mbe']:.4f} | {oa['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {o['rmse']:.4f} | {n['rmse']:.4f} | {imp:.2f}% | {o['mbe']:.4f} | {n['mbe']:.4f} | {o['r2']:.4f} | {n['r2']:.4f} |\n\nReference: M13 physically valid but only 4.28% high-DTR improvement; M10 statistical reference 13.71%.\n\nAutomated decision: **{decision}**.\n''';README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
