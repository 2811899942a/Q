#!/usr/bin/env python3
"""Final robustness validation for M10 CV radiative-deficit HTEMP.

No parameters are fitted here. The script reads the already selected M10 parameters
(DTRc, Kt0, beta_pre, beta_post), reconstructs 2017-2024 May-Sep predictions, and
reports:
1) year-by-year high-DTR performance;
2) paired day-block bootstrap CI for high-DTR RMSE improvement.

Bootstrap resamples whole solar dates, preserving within-day dependence among the
~8 observed checkpoints. Random seed is fixed for reproducibility.
"""
import csv,math,random,statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'/'processed_51463'
PFILE=DATA/'htemp_pointwise_2000_2024.csv';SFILE=DATA/'main51463_dtr_srad_daily.csv';PAR=DATA/'cv_raddef_parameters.csv'
YEAROUT=DATA/'m10_validation_by_year.csv';BOOTOUT=DATA/'m10_dayblock_bootstrap_summary.csv';README=DATA/'README_M10_ROBUSTNESS.md'
LAT=43.7833;A=2.0;C=1.0

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
def pred(r,dtrc,kt0,bp,bq):
 p0=float(r['pred_c']);d=float(r['formal_dtr_c'])
 if d<=dtrc:return p0
 which,b=branch(r)
 if which=='none':return p0
 rd=max(0,kt0-r['kt'])/0.1;x=(d-dtrc)*rd*b
 return p0-(bp if which=='pre' else bq)*x
def metrics(rows,key):
 if not rows:return (0,float('nan'),float('nan'),float('nan'))
 e=[r[key]-r['obs'] for r in rows];return len(rows),math.sqrt(mean([x*x for x in e])),mean([abs(x) for x in e]),mean(e)
def pct_imp(a,b):return 100*(a-b)/a if a and math.isfinite(a) else float('nan')
def quantile(v,p):
 s=sorted(v);x=(len(s)-1)*p;i=int(math.floor(x));j=int(math.ceil(x));return s[i] if i==j else s[i]*(j-x)+s[j]*(x-i)
def main():
 with PAR.open('r',newline='',encoding='utf-8-sig') as f:r=next(csv.DictReader(f));dtrc=float(r['dtr_threshold_c']);kt0=float(r['kt0_cv']);bp=float(r['beta_pre']);bq=float(r['beta_post'])
 kd={}
 with SFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   d=datetime.strptime(r['date'],'%Y-%m-%d').date();kd[r['date']]=float(r['srad'])/ra(d.timetuple().tm_yday)
 rows=[]
 with PFILE.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in kd:continue
   y=int(r['solar_date'][:4])
   if y<2017:continue
   r['kt']=kd[r['solar_date']];p0=float(r['pred_c']);pn=pred(r,dtrc,kt0,bp,bq);rows.append({'date':r['solar_date'],'year':y,'dtr':float(r['formal_dtr_c']),'obs':float(r['obs_c']),'official':p0,'m10':pn})
 out=[]
 for y in range(2017,2025):
  for scope,rs in [('May-Sep',[r for r in rows if r['year']==y]),('DTR>=15',[r for r in rows if r['year']==y and r['dtr']>=15])]:
   n0,r0,a0,b0=metrics(rs,'official');n1,r1,a1,b1=metrics(rs,'m10');out.append({'year':y,'scope':scope,'n_points':n0,'n_days':len(set(r['date'] for r in rs)),'official_rmse':r0,'m10_rmse':r1,'rmse_improvement_pct':pct_imp(r0,r1),'official_mae':a0,'m10_mae':a1,'official_bias':b0,'m10_bias':b1})
 with YEAROUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
 # paired day-block bootstrap on validation high-DTR days
 hi=[r for r in rows if r['dtr']>=15];by=defaultdict(lambda:[0.0,0.0,0])
 for r in hi:
  e0=r['official']-r['obs'];e1=r['m10']-r['obs'];z=by[r['date']];z[0]+=e0*e0;z[1]+=e1*e1;z[2]+=1
 days=list(by.values());rng=random.Random(20260829);imps=[];deltas=[]
 B=10000
 for _ in range(B):
  s0=s1=n=0
  for _j in range(len(days)):
   z=days[rng.randrange(len(days))];s0+=z[0];s1+=z[1];n+=z[2]
  r0=math.sqrt(s0/n);r1=math.sqrt(s1/n);imps.append(100*(r0-r1)/r0);deltas.append(r0-r1)
 n0,r0,a0,b0=metrics(hi,'official');_,r1,a1,b1=metrics(hi,'m10')
 boot={'n_days':len(days),'n_points':len(hi),'n_bootstrap':B,'official_rmse':r0,'m10_rmse':r1,'observed_improvement_pct':pct_imp(r0,r1),'bootstrap_median_improvement_pct':quantile(imps,.5),'ci2_5_improvement_pct':quantile(imps,.025),'ci97_5_improvement_pct':quantile(imps,.975),'ci2_5_rmse_reduction_c':quantile(deltas,.025),'ci97_5_rmse_reduction_c':quantile(deltas,.975),'prob_improvement_gt0':sum(x>0 for x in imps)/B}
 with BOOTOUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(boot.keys()));w.writeheader();w.writerow(boot)
 hy=[r for r in out if r['scope']=='DTR>=15' and r['n_days']>0];improved=[r for r in hy if r['rmse_improvement_pct']>0]
 text=f'''# M10 final robustness validation\n\nNo parameters were refitted. M10 parameters were frozen before this analysis.\n\n## 2017-2024 high-DTR year consistency\n\n| Year | High-DTR days | Official RMSE | M10 RMSE | Improvement |\n|---|---:|---:|---:|---:|\n'''
 for r in hy:text+=f"| {r['year']} | {r['n_days']} | {r['official_rmse']:.3f} | {r['m10_rmse']:.3f} | {r['rmse_improvement_pct']:.2f}% |\n"
 text+=f'''\nM10 improves high-DTR RMSE in **{len(improved)}/{len(hy)} validation years with high-DTR observations**.\n\n## Paired day-block bootstrap (DTR>=15 C)\n\n- Validation days: **{len(days)}**; points: **{len(hi)}**\n- Observed RMSE: **{r0:.4f} -> {r1:.4f} C**\n- Observed improvement: **{pct_imp(r0,r1):.2f}%**\n- Bootstrap median improvement: **{boot['bootstrap_median_improvement_pct']:.2f}%**\n- 95% CI improvement: **[{boot['ci2_5_improvement_pct']:.2f}%, {boot['ci97_5_improvement_pct']:.2f}%]**\n- 95% CI absolute RMSE reduction: **[{boot['ci2_5_rmse_reduction_c']:.3f}, {boot['ci97_5_rmse_reduction_c']:.3f}] C**\n- Bootstrap probability RMSE improvement >0: **{100*boot['prob_improvement_gt0']:.2f}%**\n\nStopping criterion: if annual consistency is broad and the paired day-block bootstrap CI remains above zero, M10 is accepted as the current statistical prototype and formula search should stop until crop/DSSAT propagation testing.\n''';README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
