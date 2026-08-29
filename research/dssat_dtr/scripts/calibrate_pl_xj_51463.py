#!/usr/bin/env python3
"""DSSAT Parton-Logan parameter sensitivity and independent-year Urumqi calibration.

Input: pointwise baseline table already aligned to local apparent solar time.
Calibration years: 2000-2016.
Validation years: 2017-2024.
Primary season: May-Sep.

Three parameter products are reported:
1) PL-XJ-ALL: minimise May-Sep calibration RMSE over all matched observations.
2) PL-XJ-HIGH: minimise May-Sep calibration RMSE for formal DTR >=15 C.
3) PL-XJ-BAL: minimise mean of standardised overall and high-DTR RMSE ratios,
   giving the extreme-DTR process explicit weight without fitting only extremes.

No crop observations are used here. This stage only diagnoses and regionalises HTEMP.
"""
from __future__ import annotations
import csv, math, statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'processed_51463'
INFILE = DATA / 'htemp_pointwise_2000_2024.csv'
SENS_OUT = DATA / 'pl_xj_oat_sensitivity.csv'
GRID_OUT = DATA / 'pl_xj_grid_top_candidates.csv'
METRICS_OUT = DATA / 'pl_xj_validation_metrics.csv'
HOUR_OUT = DATA / 'pl_xj_validation_by_solar_hour.csv'
DTR_OUT = DATA / 'pl_xj_validation_by_dtr.csv'
README_OUT = DATA / 'README_PL_XJ_CALIBRATION.md'

PI=3.14159
OFFICIAL=(2.0,2.2,1.0)
CAL_Y0,CAL_Y1=2000,2016
VAL_Y0,VAL_Y1=2017,2024


def htemp(hs,tmax,tmin,dayl,snup,sndn,A,B,C):
    hs%=24.0
    tmin_time=snup+C
    tmax_time=tmin_time+dayl/2.0+A
    den=tmax_time-tmin_time
    if den<=0 or B<=0:
        return float('nan')
    t=0.5*PI*(sndn-tmin_time)/den
    tsndn=tmin+(tmax-tmin)*math.sin(t)
    eb=math.exp(-B)
    if abs(1.0-eb)<1e-12:
        return float('nan')
    tmini=(tmin-tsndn*eb)/(1.0-eb)
    hdecay=24.0+C-dayl
    if hdecay<=0:
        return float('nan')
    if hs>=snup+C and hs<=sndn:
        t=0.5*PI*(hs-tmin_time)/den
        return tmin+(tmax-tmin)*math.sin(t)
    if hs<snup+C:
        t=24.0+hs-sndn
    else:
        t=hs-sndn
    return tmini+(tsndn-tmini)*math.exp(-B*t/hdecay)


def rmse(rows,p):
    A,B,C=p; ss=0.0; n=0
    for r in rows:
        y=htemp(r['hs'],r['tmax'],r['tmin'],r['dayl'],r['snup'],r['sndn'],A,B,C)
        if math.isfinite(y):
            e=y-r['obs']; ss+=e*e; n+=1
    return math.sqrt(ss/n) if n else float('nan')


def metrics(rows,p):
    A,B,C=p; obs=[]; pred=[]
    for r in rows:
        y=htemp(r['hs'],r['tmax'],r['tmin'],r['dayl'],r['snup'],r['sndn'],A,B,C)
        if math.isfinite(y): obs.append(r['obs']); pred.append(y)
    n=len(obs)
    if not n: return {'n':0,'rmse':'','mae':'','mbe':'','r2':''}
    es=[p-o for p,o in zip(pred,obs)]
    rm=math.sqrt(sum(e*e for e in es)/n)
    ma=sum(abs(e) for e in es)/n; mb=sum(es)/n
    mo=sum(obs)/n; mp=sum(pred)/n
    sx=sum((x-mo)**2 for x in obs); sy=sum((x-mp)**2 for x in pred)
    cov=sum((x-mo)*(y-mp) for x,y in zip(obs,pred))
    rr=cov/math.sqrt(sx*sy) if sx>0 and sy>0 else float('nan')
    return {'n':n,'rmse':round(rm,4),'mae':round(ma,4),'mbe':round(mb,4),'r2':round(rr*rr,4) if math.isfinite(rr) else ''}


def write(path,rows,fields=None):
    rows=list(rows); fields=fields or (list(rows[0]) if rows else [])
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)


def frange(start,stop,step):
    n=int(round((stop-start)/step))
    return [round(start+i*step,10) for i in range(n+1)]


def main():
    rows=[]
    with INFILE.open('r',encoding='utf-8-sig',newline='') as f:
        for x in csv.DictReader(f):
            dt=datetime.strptime(x['datetime_solar'],'%Y-%m-%d %H:%M:%S')
            rows.append({'year':dt.year,'month':dt.month,'date':x['solar_date'],
                         'hs':float(x['solar_hour']),'hourbin':int(x['solar_hour_bin']),
                         'obs':float(x['obs_c']),'tmax':float(x['tmax_ghcn_c']),
                         'tmin':float(x['tmin_ghcn_c']),'dtr':float(x['formal_dtr_c']),
                         'dayl':float(x['dayl_h']),'snup':float(x['snup_solar_h']),
                         'sndn':float(x['sndn_solar_h'])})
    cal=[r for r in rows if CAL_Y0<=r['year']<=CAL_Y1 and 5<=r['month']<=9]
    val=[r for r in rows if VAL_Y0<=r['year']<=VAL_Y1 and 5<=r['month']<=9]
    cal_hi=[r for r in cal if r['dtr']>=15.0]; val_hi=[r for r in val if r['dtr']>=15.0]

    base_cal=rmse(cal,OFFICIAL); base_hi=rmse(cal_hi,OFFICIAL)

    # OAT sensitivity around official defaults; broad but physically interpretable ranges.
    sens=[]
    ranges={
        'A':frange(0.0,4.0,0.25),
        'B':frange(0.5,5.0,0.25),
        'C':frange(0.0,2.5,0.25),
    }
    for name,vals in ranges.items():
        for v in vals:
            A,B,C=OFFICIAL
            if name=='A': A=v
            elif name=='B': B=v
            else: C=v
            p=(A,B,C)
            sens.append({'parameter':name,'value':v,'A':A,'B':B,'C':C,
                         'cal_rmse_all':round(rmse(cal,p),4),
                         'cal_rmse_dtr_ge15':round(rmse(cal_hi,p),4)})
    write(SENS_OUT,sens)

    # Joint coarse grid. ~17*19*11 = 3553 combinations.
    grid=[]
    for A in frange(0.0,4.0,0.25):
      for B in frange(0.5,5.0,0.25):
       for C in frange(0.0,2.5,0.25):
        p=(A,B,C)
        ra=rmse(cal,p); rh=rmse(cal_hi,p)
        bal=0.5*(ra/base_cal)+0.5*(rh/base_hi)
        grid.append((ra,rh,bal,A,B,C))

    best_all=min(grid,key=lambda z:z[0])
    best_hi=min(grid,key=lambda z:z[1])
    best_bal=min(grid,key=lambda z:z[2])
    products={
      'DSSAT-OFFICIAL':OFFICIAL,
      'PL-XJ-ALL':(best_all[3],best_all[4],best_all[5]),
      'PL-XJ-HIGH':(best_hi[3],best_hi[4],best_hi[5]),
      'PL-XJ-BAL':(best_bal[3],best_bal[4],best_bal[5]),
    }

    top=[]
    for objective,idx in [('ALL',0),('HIGH',1),('BAL',2)]:
        for rank,z in enumerate(sorted(grid,key=lambda q:q[idx])[:30],1):
            top.append({'objective':objective,'rank':rank,'A':z[3],'B':z[4],'C':z[5],
                        'cal_rmse_all':round(z[0],4),'cal_rmse_dtr_ge15':round(z[1],4),
                        'balanced_ratio_objective':round(z[2],6)})
    write(GRID_OUT,top)

    # Evaluation table: calibration and independent validation.
    scopes=[('CAL May-Sep',cal),('CAL May-Sep DTR>=15',cal_hi),
            ('VAL May-Sep',val),('VAL May-Sep DTR>=15',val_hi)]
    out=[]
    for name,p in products.items():
        for scope,rr in scopes:
            m=metrics(rr,p)
            out.append({'model':name,'A':p[0],'B':p[1],'C':p[2],'scope':scope,**m})
    write(METRICS_OUT,out)

    # Detailed validation diagnostics for official and recommended balanced product.
    rec=products['PL-XJ-BAL']
    detail=[]
    for name,p in [('DSSAT-OFFICIAL',OFFICIAL),('PL-XJ-BAL',rec)]:
        for b,lo,hi in [('<10',-1e9,10),('10-<15',10,15),('15-<20',15,20),('>=20',20,1e9)]:
            rr=[r for r in val if lo<=r['dtr']<hi]
            m=metrics(rr,p); detail.append({'model':name,'group':b,**m})
    write(DTR_OUT,detail)

    hout=[]
    for name,p in [('DSSAT-OFFICIAL',OFFICIAL),('PL-XJ-BAL',rec)]:
        for h in range(24):
            rr=[r for r in val if r['hourbin']==h]
            m=metrics(rr,p); hout.append({'model':name,'solar_hour':h,**m})
    write(HOUR_OUT,hout)

    # Parameter OAT ranking using the range of RMSE produced over its sweep.
    ranking=[]
    for param in ['A','B','C']:
        ss=[r for r in sens if r['parameter']==param]
        allv=[float(r['cal_rmse_all']) for r in ss]; hiv=[float(r['cal_rmse_dtr_ge15']) for r in ss]
        besta=min(ss,key=lambda r:float(r['cal_rmse_all']))
        besth=min(ss,key=lambda r:float(r['cal_rmse_dtr_ge15']))
        ranking.append((param,max(allv)-min(allv),max(hiv)-min(hiv),besta,besth))
    ranking.sort(key=lambda z:z[2],reverse=True)

    def find(model,scope):
        return next(r for r in out if r['model']==model and r['scope']==scope)
    bo=find('DSSAT-OFFICIAL','VAL May-Sep'); bh=find('DSSAT-OFFICIAL','VAL May-Sep DTR>=15')
    ro=find('PL-XJ-BAL','VAL May-Sep'); rh=find('PL-XJ-BAL','VAL May-Sep DTR>=15')
    imp_all=100*(float(bo['rmse'])-float(ro['rmse']))/float(bo['rmse'])
    imp_hi=100*(float(bh['rmse'])-float(rh['rmse']))/float(bh['rmse'])

    sens_text='\n'.join(
      f"- {p}: OAT RMSE span all={sa:.3f} C, high-DTR={sh:.3f} C; best one-at-a-time value all={ba['value']}, high={bi['value']}"
      for p,sa,sh,ba,bi in ranking)

    readme=f"""# PL-XJ regional calibration — Urumqi 51463

## Split
- Calibration: **{CAL_Y0}-{CAL_Y1}**, May-Sep, {len(cal):,} observation points; DTR>=15 C: {len(cal_hi):,} points.
- Independent validation: **{VAL_Y0}-{VAL_Y1}**, May-Sep, {len(val):,} points; DTR>=15 C: {len(val_hi):,} points.
- Official DSSAT parameters: A={OFFICIAL[0]}, B={OFFICIAL[1]}, C={OFFICIAL[2]}.

## One-at-a-time sensitivity
{sens_text}

## Joint-grid optima
- PL-XJ-ALL: A={products['PL-XJ-ALL'][0]}, B={products['PL-XJ-ALL'][1]}, C={products['PL-XJ-ALL'][2]}
- PL-XJ-HIGH: A={products['PL-XJ-HIGH'][0]}, B={products['PL-XJ-HIGH'][1]}, C={products['PL-XJ-HIGH'][2]}
- **PL-XJ-BAL (recommended diagnostic regionalisation): A={rec[0]}, B={rec[1]}, C={rec[2]}**

## Independent validation — recommended PL-XJ-BAL
| Scope | Official RMSE | PL-XJ-BAL RMSE | RMSE improvement |
|---|---:|---:|---:|
| May-Sep | {bo['rmse']} C | {ro['rmse']} C | {imp_all:.2f}% |
| May-Sep DTR>=15 C | {bh['rmse']} C | {rh['rmse']} C | {imp_hi:.2f}% |

Official May-Sep MAE/MBE/R2: {bo['mae']} / {bo['mbe']} / {bo['r2']}.
PL-XJ-BAL May-Sep MAE/MBE/R2: {ro['mae']} / {ro['mbe']} / {ro['r2']}.

Official high-DTR MAE/MBE/R2: {bh['mae']} / {bh['mbe']} / {bh['r2']}.
PL-XJ-BAL high-DTR MAE/MBE/R2: {rh['mae']} / {rh['mbe']} / {rh['r2']}.

## Decision logic
- If independent validation improves substantially with only A/B/C regionalisation, a significant component of Urumqi error is **parameter-transfer / regionalisation error** in the original Parton-Logan implementation.
- If high-DTR residuals remain large after PL-XJ calibration, the remaining signal supports testing a **structural modification** (for example phase-corrected or cross-day temperature reconstruction) rather than endlessly tuning A/B/C.
- This calibration is not yet a crop-model validation and must not be described as improved maize yield simulation.
"""
    README_OUT.write_text(readme,encoding='utf-8')
    print(readme)

if __name__=='__main__': main()
