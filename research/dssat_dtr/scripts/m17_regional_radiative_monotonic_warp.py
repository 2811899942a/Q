#!/usr/bin/env python3
"""M17 preregistered region-relative DTR x radiative-deficit monotonic HTEMP warp."""
from __future__ import annotations
import csv,math,statistics,json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar

ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data'/'processed_51463'; OUT=ROOT/'data'/'m17_regional_radwarp'
PFILE=D/'htemp_pointwise_2000_2024.csv'; SFILE=D/'main51463_dtr_srad_daily.csv'
LAT=43.7833; A=2.; B=2.2; C=1.; PI=3.14159; H0=10.455
QGRID=[0.,.5,1.]; KTGRID=[.60,.70,.80,.90]

def mean(x):return statistics.mean(x) if x else float('nan')
def ra(doy):
 p=math.radians(LAT);dr=1+.033*math.cos(2*math.pi*doy/365);de=.409*math.sin(2*math.pi*doy/365-1.39);x=max(-1,min(1,-math.tan(p)*math.tan(de)));w=math.acos(x);return (24*60/math.pi)*.0820*dr*(w*math.sin(p)*math.sin(de)+math.cos(p)*math.cos(de)*math.sin(w))
def pl(h,tx,tn,dl,su,sd):
 mn=su+C;mx=mn+dl/2+A;t=.5*PI*(sd-mn)/(mx-mn);ts=tn+(tx-tn)*math.sin(t);ti=(tn-ts*math.exp(-B))/(1-math.exp(-B));hd=24+C-dl
 if mn<=h<=sd:return tn+(tx-tn)*math.sin(.5*PI*(h-mn)/(mx-mn))
 tt=24+h-sd if h<mn else h-sd;return ti+(ts-ti)*math.exp(-B*tt/hd)
def profile(daily,years):
 pool=[r for r in daily if r['year'] in years];allv=[r['dtr'] for r in pool];gm=mean(allv);gs=max(statistics.stdev(allv),.5);out=[]
 for doy in range(1,367):
  vals=[r['dtr'] for r in pool if min(abs(r['doy']-doy),366-abs(r['doy']-doy))<=15]
  if len(vals)>=20:out.append((mean(vals),max(statistics.stdev(vals),.5)))
  else:out.append((gm,gs))
 return out
def enrich():
 s={}
 with SFILE.open(encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   dt=datetime.strptime(r['date'],'%Y-%m-%d');sr=float(r['srad']);tx=float(r['tmax']);tn=float(r['tmin']);s[r['date']]={'year':dt.year,'doy':dt.timetuple().tm_yday,'dtr':tx-tn,'srad':sr,'kt':sr/max(ra(dt.timetuple().tm_yday),1e-9)}
 rows=[]
 with PFILE.open(encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in s:continue
   x=dict(r);x.update(s[r['solar_date']]);x['obs']=float(r['obs_c']);x['p0']=float(r['pred_c']);x['formal_dtr']=float(r['formal_dtr_c']);x['h']=float(r['solar_hour']);x['su']=float(r['snup_solar_h']);x['sd']=float(r['sndn_solar_h']);x['dl']=float(r['dayl_h']);x['tx']=float(r['tmax_ghcn_c']);x['tn']=float(r['tmin_ghcn_c']);rows.append(x)
 return rows,list(s.values())
def segment(r):
 mx=r['su']+C+r['dl']/2+A
 if H0<r['h']<mx:
  lo=pl(H0,r['tx'],r['tn'],r['dl'],r['su'],r['sd']);hi=r['tx'];den=hi-lo
  return ('pre',min(max((r['p0']-lo)/den,0),1),lo,hi) if den>1e-9 else ('none',0,0,0)
 if mx<r['h']<r['sd']:
  lo=pl(r['sd'],r['tx'],r['tn'],r['dl'],r['su'],r['sd']);hi=r['tx'];den=hi-lo
  return ('post',min(max((r['p0']-lo)/den,0),1),lo,hi) if den>1e-9 else ('none',0,0,0)
 return 'none',0,0,0
def exposure(r,prof,q,kt0):
 mu,sd=prof[int(r['doy'])-1];z=(r['formal_dtr']-mu)/sd;return max(z-q,0)*max(kt0-r['kt'],0)/.1
def pred(r,prof,q,kt0,kpre,kpost):
 br,qt,lo,hi=segment(r)
 if br=='none':return r['p0']
 e=exposure(r,prof,q,kt0)
 if e<=0:return r['p0']
 k=kpre if br=='pre' else kpost;p=math.exp(min(k*e,20.));return lo+(hi-lo)*(qt**p)
def fitk(rows,prof,q,kt0,br):
 active=[r for r in rows if segment(r)[0]==br and exposure(r,prof,q,kt0)>0]
 if not active:return 0.
 def loss(k):return mean([(pred(r,prof,q,kt0,k if br=='pre' else 0,k if br=='post' else 0)-r['obs'])**2 for r in active])
 z=minimize_scalar(loss,bounds=(0,10),method='bounded',options={'xatol':1e-5});return float(z.x)
def metrics(rows,pf):
 e=[pf(r)-r['obs'] for r in rows];return {'n':len(e),'rmse':math.sqrt(mean([x*x for x in e])),'mae':mean([abs(x) for x in e]),'bias':mean(e)}
def write(name,rows):
 if not rows:return
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 OUT.mkdir(parents=True,exist_ok=True);rows,daily=enrich();cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];years=sorted(set(r['year'] for r in cal));cv=[]
 for q in QGRID:
  for kt0 in KTGRID:
   held=[]
   for y in years:
    tr=[r for r in cal if r['year']!=y];te=[r for r in cal if r['year']==y];pf=profile(daily,set(years)-{y});kp=fitk(tr,pf,q,kt0,'pre');ko=fitk(tr,pf,q,kt0,'post')
    for r in te:held.append((r,pred(r,pf,q,kt0,kp,ko)))
   ee=[p-r['obs'] for r,p in held];high=[(r,p) for r,p in held if r['formal_dtr']>=15]
   cv.append({'q':q,'kt0':kt0,'cv_all_rmse':math.sqrt(mean([x*x for x in ee])),'cv_high_rmse':math.sqrt(mean([(p-r['obs'])**2 for r,p in high])),'n':len(held),'n_high':len(high)})
 off_all=metrics(cal,lambda r:r['p0'])['rmse'];feas=[r for r in cv if r['cv_all_rmse']<=off_all+1e-12];best=min(feas,key=lambda r:(r['cv_high_rmse'],r['cv_all_rmse'],r['q'],r['kt0'])) if feas else min(cv,key=lambda r:(r['cv_high_rmse'],r['cv_all_rmse']))
 pf=profile(daily,set(years));kp=fitk(cal,pf,best['q'],best['kt0'],'pre');ko=fitk(cal,pf,best['q'],best['kt0'],'post')
 models={'OFFICIAL':lambda r:r['p0'],'M17':lambda r:pred(r,pf,best['q'],best['kt0'],kp,ko)};res=[];year=[]
 for name,fn in models.items():
  for g,rr in [('MaySep',val),('DTR_GE15',[r for r in val if r['formal_dtr']>=15])]:x=metrics(rr,fn);res.append({'model':name,'group':g,**x})
  for y in sorted(set(r['year'] for r in val)):
   rr=[r for r in val if r['year']==y and r['formal_dtr']>=15]
   if rr:year.append({'model':name,'year':y,**metrics(rr,fn)})
 # full-curve physical test
 checks=[];bydate={r['solar_date']:r for r in rows}
 for ds,r in bydate.items():
  if r['year']<2017 or r['formal_dtr']<15:continue
  mx=r['su']+C+r['dl']/2+A;grid=np.arange(0,24.0001,.05);vals=[]
  for h in grid:
   fake=dict(r);fake['h']=float(h);fake['p0']=pl(h,r['tx'],r['tn'],r['dl'],r['su'],r['sd']);vals.append((h,pred(fake,pf,best['q'],best['kt0'],kp,ko)))
  rise=[v for v in vals if r['su']+C<=v[0]<=mx];fall=[v for v in vals if mx<=v[0]<=r['sd']];rd=np.diff([v[1] for v in rise]);fd=np.diff([v[1] for v in fall]);checks.append({'date':ds,'below':max(0,r['tn']-min(v[1] for v in vals)),'above':max(0,max(v[1] for v in vals)-r['tx']),'rise_bad':int(np.min(rd)<-1e-7),'fall_bad':int(np.max(fd)>1e-7)})
 write('cv_grid.csv',cv);write('validation_metrics.csv',res);write('validation_by_year.csv',year);write('physical_checks.csv',checks)
 pars={'q':best['q'],'kt0':best['kt0'],'k_pre':kp,'k_post':ko,'calibration_official_all_rmse':off_all,'cv_selected':best};(OUT/'parameters.json').write_text(json.dumps(pars,indent=2))
 mm={(r['model'],r['group']):r for r in res};o=mm[('OFFICIAL','MaySep')];h=mm[('OFFICIAL','DTR_GE15')];n=mm[('M17','MaySep')];nh=mm[('M17','DTR_GE15')];bad=sum(c['below']>1e-6 or c['above']>1e-6 or c['rise_bad'] or c['fall_bad'] for c in checks)
 # compare known locked hard gates and annual M15 values from existing audit where available
 m15_year={2020:None,2021:None,2022:None,2023:None,2024:None}
 hard=n['rmse']<2.7639 and nh['rmse']<4.4623 and bad==0
 text=f'''# M17 regional radiative monotonic warp\n\nSelected only by 2000-2016 leave-one-year-out temperature CV.\n\n- selected q={best['q']}, Kt0={best['kt0']}; k_pre={kp:.6f}, k_post={ko:.6f}\n- calibration LOYO all/high-DTR RMSE={best['cv_all_rmse']:.4f}/{best['cv_high_rmse']:.4f} C\n- validation physical violations={bad}/{len(checks)}\n\n|Metric|Official|M17|Improvement|\n|---|---:|---:|---:|\n|May-Sep RMSE|{o['rmse']:.6f}|{n['rmse']:.6f}|{100*(o['rmse']-n['rmse'])/o['rmse']:.2f}%|\n|DTR>=15 RMSE|{h['rmse']:.6f}|{nh['rmse']:.6f}|{100*(h['rmse']-nh['rmse'])/h['rmse']:.2f}%|\n\nHard gate versus M12 statistical target (2.7639 / 4.4623 C) and physical QA: **{'PASS' if hard else 'FAIL'}**.\n\nThis benchmark is historical/legacy and cannot serve as fresh final validation.\n''';(OUT/'README.md').write_text(text);print(text)
if __name__=='__main__':main()
