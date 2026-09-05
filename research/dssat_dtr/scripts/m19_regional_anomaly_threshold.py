#!/usr/bin/env python3
"""M19: regional thermal-anomaly threshold with bounded HTEMP shape correction.

M18 showed that a regional amplitude K_RT is poorly identifiable: the fit wants
maximum correction. M19 moves the transferable regional parameter to the trigger:

    K_RT = local DTR anomaly threshold, in seasonal standard-deviation units.

The response shape is fixed and bounded. Other regions re-estimate only K_RT
from their own local DTR climatology after the structural constants are frozen.
This is an exploratory mechanism screen; final publication validation still
requires fresh regional data and a stricter external calibration protocol.
"""
from __future__ import annotations
import csv, importlib.util, json, math
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve()
spec=importlib.util.spec_from_file_location("m17base",HERE.with_name("m17_regional_radiative_monotonic_warp.py"))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OUT=m.ROOT/'data'/'m19_regional_anomaly_threshold'
KT0=0.70
P_TARGET=20.0
GAIN_SCALES=[0.10,0.25,0.50,1.00]
THETA_GRID=[round(-2.0+0.1*i,1) for i in range(51)] # -2.0 ... 3.0 SD


def mean(x): return m.mean(x)
def write(name,rows):
    if not rows:return
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def seg(r):
    if '_m19seg' not in r:r['_m19seg']=m.segment(r)
    return r['_m19seg']

def exposure(r,prof,theta):
    mu,sd=prof[int(r['doy'])-1]
    z=(r['formal_dtr']-mu)/sd
    return max(z-theta,0.0)*max(KT0-r['kt'],0.0)/0.1

def pred(r,prof,theta,gscale):
    br,qt,lo,hi=seg(r)
    if br=='none':return r['p0']
    e=exposure(r,prof,theta)
    if e<=0:return r['p0']
    s=1.0-math.exp(-e/gscale)
    s=min(max(s,0.0),1.0)
    qtarget=qt**P_TARGET
    qnew=(1.0-s)*qt+s*qtarget
    return lo+(hi-lo)*qnew

def metrics(rows,fn):
    ee=[fn(r)-r['obs'] for r in rows]
    return {'n':len(ee),'rmse':math.sqrt(mean([x*x for x in ee])),'mae':mean([abs(x) for x in ee]),'bias':mean(ee)}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows,daily=m.enrich()
    for r in rows:seg(r)
    cal=[r for r in rows if r['year']<=2016]
    val=[r for r in rows if r['year']>=2017]
    years=sorted(set(r['year'] for r in cal))
    prof=m.profile(daily,set(years))
    highcal=[r for r in cal if r['formal_dtr']>=15]
    offcal=metrics(cal,lambda r:r['p0']);offhigh=metrics(highcal,lambda r:r['p0'])

    # Exploratory calibration-period structural/threshold screen.
    screen=[]
    for gs in GAIN_SCALES:
        for th in THETA_GRID:
            fn=lambda r,t=th,g=gs:pred(r,prof,t,g)
            a=metrics(cal,fn);h=metrics(highcal,fn)
            screen.append({'K_RT':th,'gain_scale':gs,'cal_all_rmse':a['rmse'],'cal_high_rmse':h['rmse'],'cal_all_bias':a['bias'],'cal_high_bias':h['bias']})
    feas=[x for x in screen if x['cal_all_rmse']<=offcal['rmse']+1e-12]
    pool=feas if feas else screen
    best=min(pool,key=lambda x:(x['cal_high_rmse'],x['cal_all_rmse'],abs(x['K_RT']),x['gain_scale']))
    theta=best['K_RT'];gscale=best['gain_scale']
    official=lambda r:r['p0']
    model=lambda r:pred(r,prof,theta,gscale)

    res=[];byyear=[]
    for name,fn in {'OFFICIAL':official,'M19':model}.items():
        for group,rr in [('MaySep',val),('DTR_GE15',[r for r in val if r['formal_dtr']>=15])]:res.append({'model':name,'group':group,**metrics(rr,fn)})
        for y in sorted(set(r['year'] for r in val)):
            rr=[r for r in val if r['year']==y and r['formal_dtr']>=15]
            if rr:byyear.append({'model':name,'year':y,**metrics(rr,fn)})

    checks=[];bydate={r['solar_date']:r for r in rows}
    for ds,r in bydate.items():
        if r['year']<2017 or r['formal_dtr']<15:continue
        mx=r['su']+m.C+r['dl']/2+m.A;vals=[]
        for h in np.arange(0,24.0001,.05):
            fake=dict(r);fake['h']=float(h);fake['p0']=m.pl(h,r['tx'],r['tn'],r['dl'],r['su'],r['sd']);fake.pop('_m19seg',None)
            vals.append((h,model(fake)))
        rise=[v for v in vals if r['su']+m.C<=v[0]<=mx];fall=[v for v in vals if mx<=v[0]<=r['sd']]
        rd=np.diff([v[1] for v in rise]);fd=np.diff([v[1] for v in fall])
        checks.append({'date':ds,'below':max(0,r['tn']-min(v[1] for v in vals)),'above':max(0,max(v[1] for v in vals)-r['tx']),'rise_bad':int(np.min(rd)<-1e-7),'fall_bad':int(np.max(fd)>1e-7)})

    # Save the exact regional 2000-2016 DTR profile needed by the source patch.
    profile_rows=[{'doy':i+1,'dtr_mean_c':prof[i][0],'dtr_sd_c':prof[i][1]} for i in range(366)]
    write('calibration_screen.csv',screen);write('validation_metrics.csv',res);write('validation_by_year.csv',byyear);write('physical_checks.csv',checks);write('regional_dtr_profile_2000_2016.csv',profile_rows)

    mm={(r['model'],r['group']):r for r in res};oa=mm[('OFFICIAL','MaySep')];oh=mm[('OFFICIAL','DTR_GE15')];na=mm[('M19','MaySep')];nh=mm[('M19','DTR_GE15')]
    bad=sum(c['below']>1e-6 or c['above']>1e-6 or c['rise_bad'] or c['fall_bad'] for c in checks)
    pairs={}
    for r in byyear:pairs.setdefault(r['year'],{})[r['model']]=r['rmse']
    wins=sum(1 for x in pairs.values() if 'OFFICIAL' in x and 'M19' in x and x['M19']<x['OFFICIAL']);tot=sum(1 for x in pairs.values() if 'OFFICIAL' in x and 'M19' in x)
    gate=na['rmse']<2.7962 and nh['rmse']<4.6344 and bad==0
    interior=THETA_GRID[0]<theta<THETA_GRID[-1]
    # Numerical closure with a deliberately inactive threshold.
    closure=max(abs(pred(r,prof,99.0,gscale)-r['p0']) for r in val) if val else 0.0
    pars={'model':'M19_regional_anomaly_threshold','parameter_name':'K_RT','parameter_definition':'seasonally standardized DTR anomaly threshold (SD)','K_RT':theta,'K_RT_screen_bounds':[THETA_GRID[0],THETA_GRID[-1]],'Kt0':KT0,'P_TARGET':P_TARGET,'gain_scale':gscale,'response':'S=1-exp(-E/gain_scale); q_new=(1-S)q+S*q**P_TARGET','E':'max(z_DTR-K_RT,0)*max(Kt0-Kt,0)/0.1','calibration_best':best,'closure_max_abs_c_at_K_RT_99':closure}
    (OUT/'parameters.json').write_text(json.dumps(pars,indent=2))
    text=f'''# M19 regional thermal-anomaly threshold screen

M19 relocates the transferable regional parameter from response amplitude to the anomaly trigger.

- **K_RT = {theta:.2f} SD**: local seasonally standardized DTR anomaly threshold.
- fixed radiative threshold Kt0 = {KT0:.2f}; fixed P_TARGET = {P_TARGET:.1f}.
- selected bounded gain scale = {gscale:.2f} from the exploratory 2000-2016 mechanism screen.
- official calibration all/high-DTR RMSE = {offcal['rmse']:.4f} / {offhigh['rmse']:.4f} C.
- selected calibration all/high-DTR RMSE = {best['cal_all_rmse']:.4f} / {best['cal_high_rmse']:.4f} C.

Legacy 2017+ continuity benchmark:

|Metric|Official|M19|Improvement|
|---|---:|---:|---:|
|May-Sep RMSE|{oa['rmse']:.6f}|{na['rmse']:.6f}|{100*(oa['rmse']-na['rmse'])/oa['rmse']:.2f}%|
|DTR>=15 RMSE|{oh['rmse']:.6f}|{nh['rmse']:.6f}|{100*(oh['rmse']-nh['rmse'])/oh['rmse']:.2f}%|

- high-DTR full-curve physical violations = {bad}/{len(checks)}
- high-DTR annual wins vs official = {wins}/{tot}
- gate vs locked physical M15 = **{'PASS' if gate else 'FAIL'}**
- K_RT inside exploratory search bounds = **{'PASS' if interior else 'BOUNDARY'}**
- inactive-threshold closure max |M19-official| = {closure:.3e} C

Scientific boundary: this is a mechanism/parameter-definition screen. The legacy validation has already influenced the broader model-development sequence and is not a fresh publication test. Final claims require fresh Xinjiang/Urumqi weather plus crop phenology/yield validation.
'''
    (OUT/'README.md').write_text(text);print(text)

if __name__=='__main__':main()
