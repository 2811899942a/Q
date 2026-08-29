#!/usr/bin/env python3
from __future__ import annotations
import csv, math, statistics
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'processed_51463'
PFILE=DATA/'htemp_pointwise_2000_2024.csv'; SFILE=DATA/'main51463_dtr_srad_daily.csv'; PARAM=DATA/'amtrd_gate_parameters.csv'
README=DATA/'README_AMTRD_PHYSICAL_BOUNDS.md'; OUT=DATA/'amtrd_physical_bounds_summary.csv'
LAT=43.7833; PI=3.14159; RAD=PI/180.; SC=1368.; A=2.; C=1.

def mean(x): return statistics.mean(x) if x else float('nan')
def solar_s0d(d):
    doy=d.timetuple().tm_yday; dec=-23.45*math.cos(2*PI*(doy+10)/365.); soc=math.tan(RAD*dec)*math.tan(RAD*LAT); soc=max(-1.,min(1.,soc)); dayl=max(0.,min(24.,12+24*math.asin(soc)/PI)); ss=math.sin(RAD*dec)*math.sin(RAD*LAT); cc=math.cos(RAD*dec)*math.cos(RAD*LAT); q=ss/cc if abs(cc)>1e-12 else 0.; q=max(-1.,min(1.,q)); ds=3600*(dayl*ss+24/PI*cc*math.sqrt(max(0.,1-q*q))); return SC*ds*1e-6

def branch(r):
    hs=float(r['solar_hour']); sn=float(r['snup_solar_h']); sd=float(r['sndn_solar_h']); dl=float(r['dayl_h']); tp=sn+C+dl/2+A
    if 12<hs<tp and tp>12:
        v=(hs-12)/(tp-12); return 'pre',4*v*(1-v)
    if tp<hs<sd and sd>tp:
        u=(hs-tp)/(sd-tp); return 'post',4*u*(1-u)
    return 'none',0.

def metric(rows,key):
    e=[r[key]-float(r['obs_c']) for r in rows]; o=[float(r['obs_c']) for r in rows]; p=[r[key] for r in rows]
    mo,mp=mean(o),mean(p); so=sum((x-mo)**2 for x in o); sp=sum((x-mp)**2 for x in p); rr=sum((a-mo)*(b-mp) for a,b in zip(o,p))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan')
    return len(rows),math.sqrt(mean([x*x for x in e])),mean([abs(x) for x in e]),mean(e),rr*rr

def main():
    with PARAM.open('r',encoding='utf-8-sig') as f: p=next(csv.DictReader(f))
    dtrc=float(p['dtr_threshold_c']); t0=float(p['amtrd0_cv']); bp=float(p['beta_pre']); bq=float(p['beta_post'])
    am={}
    with SFILE.open('r',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            d=datetime.strptime(r['date'],'%Y-%m-%d').date(); s0=solar_s0d(d); am[r['date']]=float(r['srad'])/s0 if s0>0 else 0.
    rows=[]; corrections=[]; below=above=0
    with PFILE.open('r',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in am: continue
            base=float(r['pred_c']); dtr=float(r['formal_dtr_c']); raw=base; which,bv=branch(r)
            if dtr>dtrc and which!='none':
                gate=max(0.,t0-am[r['solar_date']])/0.1; corr=(bp if which=='pre' else bq)*(dtr-dtrc)*gate*bv; raw=base-corr; corrections.append(corr)
            tmin=float(r['tmin_ghcn_c']); tmax=float(r['tmax_ghcn_c']); below += raw<tmin; above += raw>tmax
            rr=dict(r); rr['year']=int(r['solar_date'][:4]); rr['raw']=raw; rr['clamped']=max(tmin,min(tmax,raw)); rows.append(rr)
    val=[r for r in rows if r['year']>=2017]; high=[r for r in val if float(r['formal_dtr_c'])>=15]
    m0=[]
    for r in rows: r['m0']=float(r['pred_c'])
    records=[]
    for group,rs in [('ALL_MAYSEP',rows),('VAL_MAYSEP',val),('VAL_HIGH_DTR',high)]:
        for key,name in [('m0','M0'),('raw','M12_RAW'),('clamped','M12_CLAMPED')]:
            n,rm,ma,mb,r2=metric(rs,key); records.append({'group':group,'model':name,'n':n,'rmse':rm,'mae':ma,'mbe':mb,'r2':r2})
    with OUT.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0].keys()));w.writeheader();w.writerows(records)
    corr_sorted=sorted(corrections)
    def pct(q):
        if not corr_sorted:return 0.
        i=min(len(corr_sorted)-1,max(0,int(round(q*(len(corr_sorted)-1)))));return corr_sorted[i]
    mp={(r['group'],r['model']):r for r in records}; b=mp[('VAL_HIGH_DTR','M0')]; raw=mp[('VAL_HIGH_DTR','M12_RAW')]; cl=mp[('VAL_HIGH_DTR','M12_CLAMPED')]
    ir=100*(b['rmse']-raw['rmse'])/b['rmse']; ic=100*(b['rmse']-cl['rmse'])/b['rmse']
    text=f'''# AMTRD HTEMP physical-envelope validation\n\nFrozen M12 parameters: DTRc={dtrc:.1f} C, AMTRD0={t0:.3f}, beta_pre={bp:.4f}, beta_post={bq:.4f}.\n\n- Evaluated May-Sep points: **{len(rows)}**\n- Active correction points: **{len(corrections)}**\n- Raw predictions below formal Tmin: **{below}**\n- Raw predictions above formal Tmax: **{above}**\n- Correction magnitude P50/P90/P95/P99/max: **{pct(.5):.3f} / {pct(.9):.3f} / {pct(.95):.3f} / {pct(.99):.3f} / {max(corrections) if corrections else 0:.3f} C**\n\n## Independent 2017-2024 high-DTR validation\n| Model | RMSE | MAE | Bias | R2 | RMSE improvement |\n|---|---:|---:|---:|---:|---:|\n| M0 official | {b['rmse']:.4f} | {b['mae']:.4f} | {b['mbe']:.4f} | {b['r2']:.4f} | 0 |\n| M12 raw | {raw['rmse']:.4f} | {raw['mae']:.4f} | {raw['mbe']:.4f} | {raw['r2']:.4f} | {ir:.2f}% |\n| M12 clamped to [Tmin,Tmax] | {cl['rmse']:.4f} | {cl['mae']:.4f} | {cl['mbe']:.4f} | {cl['r2']:.4f} | {ic:.2f}% |\n\nSource implementation should use the clamped form if raw corrections violate the daily physical envelope without reducing independent-validation skill.\n''';README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__': main()
