#!/usr/bin/env python3
"""Fit a physically monotonic DTR x CLOUDS shape-warp HTEMP prototype (M13).

M12 established the local DTR x DSSAT-native CLOUDS mechanism but its direct
additive shoulder subtraction violated complete-curve physics. M13 keeps the
mechanism and replaces the additive correction with an endpoint-preserving
monotonic power warp.

Formal rules
------------
- DTRc = 14.8 C, fixed from calibration-only breakpoint analysis.
- DTR <= DTRc: exact official HTEMP.
- Pre-peak segment: solar noon -> modeled Tmax.
- Post-peak segment: modeled Tmax -> sunset.
- Segment endpoint temperatures are exact anchors.
- Let q be the official HTEMP temperature normalized to [0,1] between the two
  segment endpoint temperatures. Apply
      q_new = q ** p
      p = 1 + k * (DTR-DTRc) * CLOUDS, k >= 0.
- Since q is monotonic on each official segment and p>=1, the transformed curve
  remains monotonic and cannot overshoot its segment endpoint temperatures.
- k_pre and k_post are fitted only on 2000-2016 May-Sep observations.
- 2017-2024 remains untouched independent validation.
- CLOUDS follows DSSAT v4.8.5.0 SOLAR.for exactly.

The implementation precomputes the small set of active calibration points before
scanning k; this is mathematically identical to repeatedly scanning all points but
is much faster.
"""
from __future__ import annotations
import csv, math, statistics
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed_51463'
PFILE=DATA/'htemp_pointwise_2000_2024.csv'; SFILE=DATA/'main51463_dtr_srad_daily.csv'
README=DATA/'README_M13_MONOTONIC_CLOUD_WARP.md'; PARAM=DATA/'m13_monotonic_parameters.csv'; VAL=DATA/'m13_monotonic_validation.csv'; DTR_OUT=DATA/'m13_monotonic_by_dtr.csv'; HOUR_OUT=DATA/'m13_monotonic_by_hour.csv'; CLOUD_OUT=DATA/'m13_monotonic_by_cloud_strata.csv'; GRID=DATA/'m13_monotonic_fit_grid.csv'; SHAPE=DATA/'m13_monotonic_shape_checks.csv'
DTRC=14.8; LAT=43.7833; A=2.; B=2.2; C=1.; PI=3.14159; RAD=PI/180.; S0N=1368.; AMTRCS=.77

def mean(x): return statistics.mean(x) if x else float('nan')

def dssat_solar(date,srad):
    doy=date.timetuple().tm_yday
    dec=-23.45*math.cos(2*PI*(doy+10.)/365.)
    soc=math.tan(RAD*dec)*math.tan(RAD*LAT); soc=min(max(soc,-1.),1.)
    dl=min(max(12.+24.*math.asin(soc)/PI,0.),24.); su=12.-dl/2.; sd=12.+dl/2.
    ss=math.sin(RAD*dec)*math.sin(RAD*LAT); cc=math.cos(RAD*dec)*math.cos(RAD*LAT)
    z=ss/cc if abs(cc)>1e-12 else 0.; z=min(max(z,-1.),1.)
    dsinb=3600.*(dl*ss+24./PI*cc*math.sqrt(max(0.,1.-z*z)))
    sclear=AMTRCS*S0N*dsinb*1e-6
    cl=min(max(1.-srad/sclear,0.),1.) if sclear>0 else 0.
    return dl,su,sd,cl

def pl(h,tmax,tmin,dl,su,sd):
    mn=su+C; mx=mn+dl/2.+A
    t=.5*PI*(sd-mn)/(mx-mn)
    ts=tmin+(tmax-tmin)*math.sin(t)
    tmini=(tmin-ts*math.exp(-B))/(1.-math.exp(-B))
    hdec=24.+C-dl
    if mn<=h<=sd:
        t=.5*PI*(h-mn)/(mx-mn)
        return tmin+(tmax-tmin)*math.sin(t)
    tt=24.+h-sd if h<mn else h-sd
    return tmini+(ts-tmini)*math.exp(-B*tt/hdec)

def branch_info(r):
    h=float(r['solar_hour']); dl=r['dayl']; su=r['snup']; sd=r['sndn']
    mx=su+C+dl/2.+A; tmax=float(r['tmax_ghcn_c']); tmin=float(r['tmin_ghcn_c']); p0=float(r['pred_c'])
    if 12.<h<mx:
        lo=pl(12.,tmax,tmin,dl,su,sd); hi=tmax; den=hi-lo
        if den<=1e-9: return 'none',0.,lo,hi
        q=min(max((p0-lo)/den,0.),1.)
        return 'pre',q,lo,hi
    if mx<h<sd:
        lo=pl(sd,tmax,tmin,dl,su,sd); hi=tmax; den=hi-lo
        if den<=1e-9: return 'none',0.,lo,hi
        q=min(max((p0-lo)/den,0.),1.)
        return 'post',q,lo,hi
    return 'none',0.,0.,0.

def transformed(r,kpre,kpost):
    p0=float(r['pred_c']); dtr=float(r['formal_dtr_c'])
    if dtr<=DTRC: return p0
    br,q,lo,hi=branch_info(r)
    if br=='none': return p0
    k=kpre if br=='pre' else kpost
    exponent=1.+k*(dtr-DTRC)*r['clouds']
    return lo+(hi-lo)*(q**exponent)

def fit_branch(rows,branch):
    prepared=[]
    for r in rows:
        if float(r['formal_dtr_c'])<=DTRC: continue
        br,q,lo,hi=branch_info(r)
        if br!=branch: continue
        e=(float(r['formal_dtr_c'])-DTRC)*r['clouds']
        prepared.append((q,lo,hi,e,float(r['obs_c'])))
    best=None; grid=[]
    # Broad nonnegative range, 0..20. A boundary hit is explicitly rejected later.
    for i in range(2001):
        k=i*.01
        sse=0.
        for q,lo,hi,e,obs in prepared:
            pred=lo+(hi-lo)*(q**(1.+k*e))
            de=pred-obs; sse+=de*de
        n=len(prepared)
        if n:
            rm=math.sqrt(sse/n); grid.append((k,n,rm))
            if best is None or sse<best[0]: best=(sse,k,n,rm)
    return best,grid

def metric(rows,pf):
    if not rows:return {'n':0,'rmse':float('nan'),'mae':float('nan'),'mbe':float('nan'),'r2':float('nan')}
    o=[float(r['obs_c']) for r in rows]; p=[pf(r) for r in rows]; e=[b-a for a,b in zip(o,p)]
    rm=math.sqrt(mean([z*z for z in e])); ma=mean([abs(z) for z in e]); mb=mean(e)
    mo,mp=mean(o),mean(p); so=sum((x-mo)**2 for x in o); sp=sum((x-mp)**2 for x in p)
    rr=sum((a-mo)*(b-mp) for a,b in zip(o,p))/math.sqrt(so*sp) if so>0 and sp>0 else float('nan')
    return {'n':len(rows),'rmse':rm,'mae':ma,'mbe':mb,'r2':rr*rr}

def dbin(d):
    if d<10:return '<10'
    if d<15:return '10-<15'
    if d<18:return '15-<18'
    if d<20:return '18-<20'
    return '>=20'

def write(path,rows,fields):
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def main():
    srad={}
    with SFILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f): srad[r['date']]=float(r['srad'])
    rows=[]
    with PFILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in srad: continue
            date=datetime.strptime(r['solar_date'],'%Y-%m-%d').date()
            dl,su,sd,cl=dssat_solar(date,srad[r['solar_date']])
            r['year']=date.year; r['dayl']=dl; r['snup']=su; r['sndn']=sd; r['clouds']=cl
            rows.append(r)
    cal=[r for r in rows if r['year']<=2016]; val=[r for r in rows if r['year']>=2017]
    bp,gp=fit_branch(cal,'pre'); bq,gq=fit_branch(cal,'post')
    kpre=bp[1]; kpost=bq[1]
    grid=[{'branch':'pre','k':k,'n':n,'cal_rmse':rm} for k,n,rm in gp]+[{'branch':'post','k':k,'n':n,'cal_rmse':rm} for k,n,rm in gq]
    write(GRID,grid,['branch','k','n','cal_rmse'])
    at_bound_pre=abs(kpre-20.)<1e-12; at_bound_post=abs(kpost-20.)<1e-12
    write(PARAM,[{'dtr_threshold_c':DTRC,'k_pre':kpre,'k_post':kpost,'n_cal_pre':bp[2],'n_cal_post':bq[2],'cal_rmse_pre':bp[3],'cal_rmse_post':bq[3],'pre_hit_upper_bound':at_bound_pre,'post_hit_upper_bound':at_bound_post}],['dtr_threshold_c','k_pre','k_post','n_cal_pre','n_cal_post','cal_rmse_pre','cal_rmse_post','pre_hit_upper_bound','post_hit_upper_bound'])

    models=[('M0_OFFICIAL',lambda r:float(r['pred_c'])),('M13_MONOTONIC_CLOUD_WARP',lambda r:transformed(r,kpre,kpost))]
    groups=[('May-Sep',val),('DTR<14.8',[r for r in val if float(r['formal_dtr_c'])<DTRC]),('DTR>=15',[r for r in val if float(r['formal_dtr_c'])>=15]),('DTR>=18',[r for r in val if float(r['formal_dtr_c'])>=18])]
    rec=[]
    for name,pf in models:
        for gl,rs in groups:
            m=metric(rs,pf);m.update({'model':name,'group':gl});rec.append(m)
    write(VAL,[{k:r[k] for k in ['model','group','n','rmse','mae','mbe','r2']} for r in rec],['model','group','n','rmse','mae','mbe','r2'])

    dr=[]
    for name,pf in models:
        for b in ['<10','10-<15','15-<18','18-<20','>=20']:
            rs=[r for r in val if dbin(float(r['formal_dtr_c']))==b]
            m=metric(rs,pf);m.update({'model':name,'dtr_bin':b});dr.append(m)
    write(DTR_OUT,[{k:r[k] for k in ['model','dtr_bin','n','rmse','mae','mbe','r2']} for r in dr],['model','dtr_bin','n','rmse','mae','mbe','r2'])

    hr=[]
    for name,pf in models:
        for h in [5,8,9,11,12,14,15,17,18,20,23]:
            rs=[r for r in val if int(float(r['solar_hour']))==h]
            m=metric(rs,pf);m.update({'model':name,'solar_hour':h});hr.append(m)
    write(HOUR_OUT,[{k:r[k] for k in ['model','solar_hour','n','rmse','mae','mbe','r2']} for r in hr],['model','solar_hour','n','rmse','mae','mbe','r2'])

    caldays={r['solar_date']:r['clouds'] for r in cal if float(r['formal_dtr_c'])>=15}
    vv=sorted(caldays.values()); q1=vv[len(vv)//3]; q2=vv[2*len(vv)//3]; cr=[]
    for label,lo,hi in [('LowCloud',-1,q1),('MidCloud',q1,q2),('HighCloud',q2,2)]:
        rs=[r for r in val if float(r['formal_dtr_c'])>=15 and lo<=r['clouds']<hi]
        for name,pf in models:
            m=metric(rs,pf);m.update({'model':name,'cloud_group':label,'n_days':len(set(r['solar_date'] for r in rs))});cr.append(m)
    write(CLOUD_OUT,[{k:r[k] for k in ['model','cloud_group','n_days','n','rmse','mae','mbe','r2']} for r in cr],['model','cloud_group','n_days','n','rmse','mae','mbe','r2'])

    # Complete-curve invariants on a 0.05-h grid.
    daymeta={}
    for r in rows: daymeta.setdefault(r['solar_date'],r)
    checks=[]
    for ds,r in daymeta.items():
        if float(r['formal_dtr_c'])<=DTRC: continue
        tx=float(r['tmax_ghcn_c']); tn=float(r['tmin_ghcn_c']); dl=r['dayl']; su=r['snup']; sd=r['sndn']; mx=su+C+dl/2.+A
        vals=[]
        for i in range(481):
            h=i*.05; p0=pl(h,tx,tn,dl,su,sd)
            fake=dict(r); fake['solar_hour']=str(h); fake['pred_c']=str(p0)
            vals.append((h,transformed(fake,kpre,kpost)))
        rise=[z for z in vals if su+C<=z[0]<=mx]; fall=[z for z in vals if mx<=z[0]<=sd]
        rd=[rise[i+1][1]-rise[i][1] for i in range(len(rise)-1)]; fd=[fall[i+1][1]-fall[i][1] for i in range(len(fall)-1)]
        checks.append({'solar_date':ds,'year':r['year'],'rise_monotonic':'YES' if min(rd)>=-1e-8 else 'NO','fall_monotonic':'YES' if max(fd)<=1e-8 else 'NO','below_tmin_c':max(0.,tn-min(z[1] for z in vals)),'above_tmax_c':max(0.,max(z[1] for z in vals)-tx)})
    write(SHAPE,checks,['solar_date','year','rise_monotonic','fall_monotonic','below_tmin_c','above_tmax_c'])
    valchk=[r for r in checks if r['year']>=2017]
    bad=sum(r['rise_monotonic']=='NO' or r['fall_monotonic']=='NO' or r['below_tmin_c']>1e-6 or r['above_tmax_c']>1e-6 for r in valchk)

    mm={(r['model'],r['group']):r for r in rec}
    o=mm[('M0_OFFICIAL','DTR>=15')]; n=mm[('M13_MONOTONIC_CLOUD_WARP','DTR>=15')]
    oa=mm[('M0_OFFICIAL','May-Sep')]; na=mm[('M13_MONOTONIC_CLOUD_WARP','May-Sep')]
    imp=100*(o['rmse']-n['rmse'])/o['rmse']; impa=100*(oa['rmse']-na['rmse'])/oa['rmse']
    verdict='SOURCE_CANDIDATE' if bad==0 and imp>8.0 and not at_bound_pre and not at_bound_post else 'REVIEW_REQUIRED'
    text=f'''# M13 monotonic DSSAT-CLOUDS shape-warp HTEMP\n\nThe DTR x CLOUDS mechanism is retained, but the physically invalid additive M12 correction is replaced by an endpoint-preserving monotonic power warp.\n\n- DTR trigger: **>{DTRC:.1f} C**\n- `p_pre = 1 + k_pre*(DTR-DTRc)*CLOUDS`, **k_pre={kpre:.4f}**\n- `p_post = 1 + k_post*(DTR-DTRc)*CLOUDS`, **k_post={kpost:.4f}**\n- upper-bound hits: pre={at_bound_pre}, post={at_bound_post}\n- validation full-curve physical violations: **{bad}/{len(valchk)} high-DTR days**\n\n## Independent validation 2017-2024\n| Scope | Official RMSE | M13 RMSE | Improvement | Official Bias | M13 Bias | Official R2 | M13 R2 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| May-Sep | {oa['rmse']:.4f} | {na['rmse']:.4f} | {impa:.2f}% | {oa['mbe']:.4f} | {na['mbe']:.4f} | {oa['r2']:.4f} | {na['r2']:.4f} |\n| DTR>=15 C | {o['rmse']:.4f} | {n['rmse']:.4f} | {imp:.2f}% | {o['mbe']:.4f} | {n['mbe']:.4f} | {o['r2']:.4f} | {n['r2']:.4f} |\n\nReference statistical prototypes: M10=13.71% and M12=13.44% high-DTR RMSE improvement, but M12 is physically invalid as a direct source formula.\n\nAutomated decision: **{verdict}**.\n'''
    README.write_text(text,encoding='utf-8');print(text)

if __name__=='__main__': main()
