#!/usr/bin/env python3
"""Test a minimal Urumqi-specific DSSAT HTEMP structural modification.

Hypothesis:
When May-Sep DTR exceeds the locally diagnosed breakpoint (14.5 C), the original
Parton-Logan daytime sine retains heat too long after the daily peak. We therefore
compress only the post-peak phase of the daytime sine:

  theta_new = pi/2 + F * (theta - pi/2)
  F = 1 + gamma * max(0, DTR - 14.5)

for solar time after the PL peak. Before the peak, the original equation is unchanged.
The modified sunset temperature is then used as the starting value of the original
nighttime exponential decay, preserving day-night continuity.

This script calibrates only gamma on 2000-2016 May-Sep and independently validates
2017-2024. It compares:
  M0 DSSAT official PL (A=2.0, B=2.2, C=1.0)
  M1 PL-XJ-BAL (A=0.5, B=0.5, C=1.75)
  M2 DTR-PC using official PL + one new gamma

No crop model is run here.
"""

from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed_51463"
INFILE = DATA / "htemp_pointwise_2000_2024.csv"
OUT_GRID = DATA / "dtr_phase_compression_grid.csv"
OUT_METRICS = DATA / "dtr_phase_compression_validation.csv"
OUT_DTR = DATA / "dtr_phase_compression_by_dtr.csv"
OUT_HOUR = DATA / "dtr_phase_compression_by_hour.csv"
README = DATA / "README_DTR_PHASE_COMPRESSION.md"

PI = 3.14159
DTR_C = 14.5
OFFICIAL = (2.0, 2.2, 1.0)
PL_XJ_BAL = (0.5, 0.5, 1.75)


def mean(xs): return statistics.mean(xs) if xs else float('nan')

def rmse(err): return math.sqrt(mean([e*e for e in err])) if err else float('nan')

def mae(err): return mean([abs(e) for e in err]) if err else float('nan')

def r2(obs,pred):
    if len(obs)<3: return float('nan')
    mo,mp=mean(obs),mean(pred)
    den=math.sqrt(sum((x-mo)**2 for x in obs)*sum((y-mp)**2 for y in pred))
    if den<=0: return float('nan')
    r=sum((x-mo)*(y-mp) for x,y in zip(obs,pred))/den
    return r*r


def htemp(hs,tmax,tmin,dayl,snup,sndn,A,B,C,gamma=0.0,dtr_c=DTR_C):
    """PL with optional post-peak phase compression and continuity-preserving night."""
    hs = hs % 24.0
    dtr = tmax-tmin
    tmin_time = snup + C
    tmax_time = tmin_time + dayl/2.0 + A
    # Original phase at sunset.
    theta_s = 0.5*PI*(sndn-tmin_time)/(tmax_time-tmin_time)
    factor = 1.0 + gamma*max(0.0,dtr-dtr_c)
    if sndn > tmax_time and gamma>0 and dtr>dtr_c:
        theta_s = 0.5*PI + factor*(theta_s-0.5*PI)
        # prevent physically nonsensical sine turnover below Tmin before sunset
        theta_s = min(theta_s, PI-0.02)
    tsndn = tmin + dtr*math.sin(theta_s)
    eb=math.exp(-B)
    tmini=(tmin-tsndn*eb)/(1.0-eb)
    hdecay=24.0+C-dayl

    if hs >= snup+C and hs <= sndn:
        theta=0.5*PI*(hs-tmin_time)/(tmax_time-tmin_time)
        if hs > tmax_time and gamma>0 and dtr>dtr_c:
            theta=0.5*PI + factor*(theta-0.5*PI)
            theta=min(theta,PI-0.02)
        return tmin+dtr*math.sin(theta)

    if hs < snup+C:
        t=24.0+hs-sndn
    else:
        t=hs-sndn
    arg=-B*t/hdecay
    return tmini+(tsndn-tmini)*math.exp(arg)


def metric(rows, model_fn):
    obs=[]; pred=[]
    for r in rows:
        p=model_fn(r); o=r['obs']
        obs.append(o); pred.append(p)
    err=[p-o for p,o in zip(pred,obs)]
    return {'n':len(rows),'rmse':rmse(err),'mae':mae(err),'mbe':mean(err),'r2':r2(obs,pred)}


def dtr_bin(x):
    if x<10:return '<10'
    if x<15:return '10-<15'
    if x<18:return '15-<18'
    if x<20:return '18-<20'
    return '>=20'


def main():
    rows=[]
    with INFILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            date=r['solar_date']; year=int(date[:4]); month=int(r['month'])
            if not 5<=month<=9: continue
            rows.append({
                'date':date,'year':year,'month':month,
                'hs':float(r['solar_hour']),'obs':float(r['obs_c']),
                'tmax':float(r['tmax_ghcn_c']),'tmin':float(r['tmin_ghcn_c']),
                'dtr':float(r['formal_dtr_c']),'dayl':float(r['dayl_h']),
                'snup':float(r['snup_solar_h']),'sndn':float(r['sndn_solar_h']),
                'hour_bin':int(float(r['solar_hour']))%24,
            })
    cal=[r for r in rows if r['year']<=2016]
    val=[r for r in rows if r['year']>=2017]

    def pred_params(params,gamma=0.0):
        A,B,C=params
        return lambda r: htemp(r['hs'],r['tmax'],r['tmin'],r['dayl'],r['snup'],r['sndn'],A,B,C,gamma)

    # Calibrate gamma using a balanced objective: all May-Sep + DTR>=14.5.
    grid=[]
    best=None
    for i in range(0,151):
        gamma=i*0.001
        fn=pred_params(OFFICIAL,gamma)
        allm=metric(cal,fn)
        high=[r for r in cal if r['dtr']>=DTR_C]
        highm=metric(high,fn)
        # normalized balanced objective relative to M0, prevents fitting only rare extremes
        obj=0.5*allm['rmse']+0.5*highm['rmse']
        rec={'gamma':gamma,'cal_all_rmse':allm['rmse'],'cal_high_rmse':highm['rmse'],'objective':obj}
        grid.append(rec)
        if best is None or obj<best['objective']:
            best=rec
    gamma=best['gamma']

    def model_defs():
        return [
            ('M0_DSSAT_OFFICIAL',pred_params(OFFICIAL,0.0)),
            ('M1_PL_XJ_BAL',pred_params(PL_XJ_BAL,0.0)),
            ('M2_DTR_PC',pred_params(OFFICIAL,gamma)),
        ]

    metric_rows=[]
    for split_name,subset in [('Calibration_2000_2016',cal),('Validation_2017_2024',val)]:
        for scope_name,scoperows in [
            ('May-Sep',subset),
            ('DTR>=14.5',[r for r in subset if r['dtr']>=DTR_C]),
            ('DTR>=15',[r for r in subset if r['dtr']>=15.0]),
        ]:
            for name,fn in model_defs():
                m=metric(scoperows,fn)
                metric_rows.append({'split':split_name,'scope':scope_name,'model':name,'gamma':gamma if name=='M2_DTR_PC' else 0.0,**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})

    # Validation by DTR bin.
    dtr_rows=[]
    for b in ['<10','10-<15','15-<18','18-<20','>=20']:
        subset=[r for r in val if dtr_bin(r['dtr'])==b]
        for name,fn in model_defs():
            m=metric(subset,fn)
            dtr_rows.append({'dtr_bin':b,'model':name,**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})

    # Validation by solar hour, focusing on whether afternoon bias is actually corrected.
    hour_rows=[]
    for h in range(24):
        subset=[r for r in val if r['hour_bin']==h]
        if not subset: continue
        for name,fn in model_defs():
            m=metric(subset,fn)
            hour_rows.append({'solar_hour':h,'model':name,**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})

    def write(path,rows):
        with path.open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    write(OUT_GRID,[{k:round(v,6) if isinstance(v,float) else v for k,v in r.items()} for r in grid])
    write(OUT_METRICS,metric_rows);write(OUT_DTR,dtr_rows);write(OUT_HOUR,hour_rows)

    mp={(r['split'],r['scope'],r['model']):r for r in metric_rows}
    m0=mp[('Validation_2017_2024','May-Sep','M0_DSSAT_OFFICIAL')]
    m1=mp[('Validation_2017_2024','May-Sep','M1_PL_XJ_BAL')]
    m2=mp[('Validation_2017_2024','May-Sep','M2_DTR_PC')]
    h0=mp[('Validation_2017_2024','DTR>=15','M0_DSSAT_OFFICIAL')]
    h1=mp[('Validation_2017_2024','DTR>=15','M1_PL_XJ_BAL')]
    h2=mp[('Validation_2017_2024','DTR>=15','M2_DTR_PC')]
    imp_all=100*(m0['rmse']-m2['rmse'])/m0['rmse']
    imp_high=100*(h0['rmse']-h2['rmse'])/h0['rmse']

    # Afternoon 14-18 validation aggregate.
    aft=[r for r in val if 14<=r['hour_bin']<=18]
    a0=metric(aft,pred_params(OFFICIAL,0.0)); a2=metric(aft,pred_params(OFFICIAL,gamma))

    text=f'''# DTR-triggered post-peak phase compression — first structural test

## Locally diagnosed trigger
- DTR breakpoint fixed before this fit: **{DTR_C:.1f} C**.
- Only one new structural parameter was calibrated: **gamma = {gamma:.3f} per C DTR excess**.
- Calibration: 2000-2016 May-Sep.
- Independent validation: 2017-2024 May-Sep.

## Formula
For `DTR > {DTR_C:.1f} C` and solar time after the original PL temperature peak:

`theta_new = pi/2 + [1 + gamma*(DTR-{DTR_C:.1f})] * (theta-pi/2)`

The pre-peak branch remains unchanged. The modified sunset temperature is passed into the existing nighttime exponential branch, so the curve remains continuous at sunset.

## Independent validation
| Model | May-Sep RMSE | DTR>=15 RMSE | DTR>=15 Bias | DTR>=15 R2 |
|---|---:|---:|---:|---:|
| M0 DSSAT official | {m0['rmse']:.4f} | {h0['rmse']:.4f} | {h0['mbe']:.4f} | {h0['r2']:.4f} |
| M1 PL-XJ-BAL | {m1['rmse']:.4f} | {h1['rmse']:.4f} | {h1['mbe']:.4f} | {h1['r2']:.4f} |
| M2 DTR-PC | {m2['rmse']:.4f} | {h2['rmse']:.4f} | {h2['mbe']:.4f} | {h2['r2']:.4f} |

M2 RMSE improvement vs official: **{imp_all:.2f}%** for all May-Sep and **{imp_high:.2f}%** for DTR>=15 C.

## Afternoon 14-18 solar time validation
- Official RMSE / Bias: **{a0['rmse']:.4f} / {a0['mbe']:.4f} C**.
- DTR-PC RMSE / Bias: **{a2['rmse']:.4f} / {a2['mbe']:.4f} C**.

## Decision rule
This M2 is worth advancing only if it materially reduces independent high-DTR and afternoon errors without degrading low-DTR days (which are mathematically unchanged because the trigger is inactive below 14.5 C). It remains a temperature-reconstruction experiment, not yet evidence of improved DSSAT crop yield or phenology.
'''
    README.write_text(text,encoding='utf-8')
    print(text)

if __name__=='__main__': main()
