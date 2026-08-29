#!/usr/bin/env python3
"""Physical-consistency diagnosis for the frozen M12 statistical prototype.

M12 has strong independent validation skill, but its additive anchored shoulder
correction must not be promoted to DSSAT source code unless it preserves a
physically plausible diurnal curve. This script checks correction magnitudes
at observed validation checkpoints and reconstructs full 24-hour curves for
every matched May-Sep day with SRAD to test:

- minimum/maximum bounds against daily Tmin/Tmax;
- monotonic warming from modeled Tmin time to modeled Tmax;
- monotonic cooling from modeled Tmax to sunset;
- size of any local reversal introduced by the correction.

This is a diagnostic only. No parameter is refitted.
"""
from __future__ import annotations
import csv, math, statistics
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed_51463'
PFILE=DATA/'htemp_pointwise_2000_2024.csv'
SFILE=DATA/'main51463_dtr_srad_daily.csv'
README=DATA/'README_M12_PHYSICAL_SHAPE.md'
DAILY=DATA/'m12_physical_shape_daily.csv'
MAG=DATA/'m12_correction_magnitude.csv'

DTRC=14.8; BP=21.902523100316625; BQ=4.675932416092293
LAT=43.7833; A=2.0; B=2.2; C=1.0; PI=3.14159; RAD=PI/180.; S0N=1368.; AMTRCS=.77

def pct(vals,p):
    vals=sorted(vals)
    if not vals:return float('nan')
    x=(len(vals)-1)*p;i=int(math.floor(x));j=int(math.ceil(x))
    return vals[i] if i==j else vals[i]*(j-x)+vals[j]*(x-i)

def daylen(doy):
    dec=-23.45*math.cos(2*PI*(doy+10.)/365.)
    soc=math.tan(RAD*dec)*math.tan(RAD*LAT);soc=min(max(soc,-1.),1.)
    dl=12.+24.*math.asin(soc)/PI;dl=min(max(dl,0.),24.)
    return dl,dec,12.-dl/2.,12.+dl/2.
def clouds(date,srad):
    dl,dec,su,sd=daylen(date.timetuple().tm_yday)
    ss=math.sin(RAD*dec)*math.sin(RAD*LAT);cc=math.cos(RAD*dec)*math.cos(RAD*LAT)
    soc=ss/cc if abs(cc)>1e-12 else 0.;soc=min(max(soc,-1.),1.)
    dsinb=3600.*(dl*ss+24./PI*cc*math.sqrt(max(0.,1.-soc*soc)))
    sclear=AMTRCS*S0N*dsinb*1e-6
    return min(max(1.-srad/sclear,0.),1.) if sclear>0 else 0.
def pl(h,tmax,tmin,dl,su,sd):
    mn=su+C;mx=mn+dl/2.+A;t=.5*PI*(sd-mn)/(mx-mn);ts=tmin+(tmax-tmin)*math.sin(t)
    tmini=(tmin-ts*math.exp(-B))/(1.-math.exp(-B));hdec=24.+C-dl
    if mn<=h<=sd:
        t=.5*PI*(h-mn)/(mx-mn);return tmin+(tmax-tmin)*math.sin(t)
    tt=24.+h-sd if h<mn else h-sd;return tmini+(ts-tmini)*math.exp(-B*tt/hdec)
def correction(h,dtr,cl,dl,su,sd):
    if dtr<=DTRC:return 0.,'none'
    mx=su+C+dl/2.+A
    if 12.<h<mx and mx>12.:
        v=(h-12.)/(mx-12.);return BP*(dtr-DTRC)*cl*4*v*(1-v),'pre'
    if mx<h<sd and sd>mx:
        u=(h-mx)/(sd-mx);return BQ*(dtr-DTRC)*cl*4*u*(1-u),'post'
    return 0.,'none'
def main():
    daily_srad={}
    with SFILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):daily_srad[r['date']]=float(r['srad'])
    # representative daily extrema from pointwise table
    daymeta={}
    point_rows=[]
    with PFILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if int(r['month']) not in [5,6,7,8,9] or r['solar_date'] not in daily_srad:continue
            daymeta.setdefault(r['solar_date'],(float(r['tmax_ghcn_c']),float(r['tmin_ghcn_c']),float(r['formal_dtr_c'])))
            if int(r['solar_date'][:4])>=2017 and float(r['formal_dtr_c'])>=15:
                date=datetime.strptime(r['solar_date'],'%Y-%m-%d').date();dl,dec,su,sd=daylen(date.timetuple().tm_yday);cl=clouds(date,daily_srad[r['solar_date']]);d,br=correction(float(r['solar_hour']),float(r['formal_dtr_c']),cl,dl,su,sd)
                if d>0:point_rows.append({'solar_date':r['solar_date'],'branch':br,'solar_hour':r['solar_hour'],'dtr_c':r['formal_dtr_c'],'clouds':cl,'correction_c':d,'official_pred_c':r['pred_c'],'corrected_pred_c':float(r['pred_c'])-d,'tmin_c':r['tmin_ghcn_c'],'tmax_c':r['tmax_ghcn_c']})
    with MAG.open('w',newline='',encoding='utf-8-sig') as f:
        fields=list(point_rows[0].keys());w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(point_rows)
    out=[]
    for ds,(tx,tn,dtr) in sorted(daymeta.items()):
        date=datetime.strptime(ds,'%Y-%m-%d').date();dl,dec,su,sd=daylen(date.timetuple().tm_yday);cl=clouds(date,daily_srad[ds]);mx=su+C+dl/2.+A
        if dtr<=DTRC:continue
        # 0.05-h grid is enough to detect local reversals in deterministic smooth curves.
        grid=[i*.05 for i in range(481)]
        vals=[]
        for h in grid:
            p=pl(h,tx,tn,dl,su,sd);dc,_=correction(h,dtr,cl,dl,su,sd);vals.append((h,p-dc,dc))
        rise=[z for z in vals if su+C<=z[0]<=mx]
        fall=[z for z in vals if mx<=z[0]<=sd]
        rise_steps=[rise[i+1][1]-rise[i][1] for i in range(len(rise)-1)]
        fall_steps=[fall[i+1][1]-fall[i][1] for i in range(len(fall)-1)]
        out.append({'solar_date':ds,'year':date.year,'dtr_c':dtr,'clouds':cl,'tmin_c':tn,'tmax_c':tx,
                    'max_correction_c':max(z[2] for z in vals),'curve_min_c':min(z[1] for z in vals),'curve_max_c':max(z[1] for z in vals),
                    'below_tmin_c':max(0.,tn-min(z[1] for z in vals)),'above_tmax_c':max(0.,max(z[1] for z in vals)-tx),
                    'rise_reversal_c':max(0.,-min(rise_steps)) if rise_steps else 0.,'fall_reversal_c':max(0.,max(fall_steps)) if fall_steps else 0.,
                    'rise_monotonic':'YES' if not rise_steps or min(rise_steps)>=-1e-8 else 'NO','fall_monotonic':'YES' if not fall_steps or max(fall_steps)<=1e-8 else 'NO'})
    with DAILY.open('w',newline='',encoding='utf-8-sig') as f:
        fields=list(out[0].keys());w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
    val=[r for r in out if r['year']>=2017];cal=[r for r in out if r['year']<=2016]
    mags=[r['correction_c'] for r in point_rows]
    pre=[r['correction_c'] for r in point_rows if r['branch']=='pre'];post=[r['correction_c'] for r in point_rows if r['branch']=='post']
    def summ(rs):
        return {'n':len(rs),'rise_bad':sum(r['rise_monotonic']=='NO' for r in rs),'fall_bad':sum(r['fall_monotonic']=='NO' for r in rs),'below':sum(r['below_tmin_c']>1e-6 for r in rs),'max_rev_rise':max((r['rise_reversal_c'] for r in rs),default=0.),'max_rev_fall':max((r['fall_reversal_c'] for r in rs),default=0.),'max_below':max((r['below_tmin_c'] for r in rs),default=0.)}
    sc=summ(cal);sv=summ(val)
    verdict='PHYSICALLY_ACCEPTABLE' if sv['rise_bad']==0 and sv['fall_bad']==0 and sv['below']==0 else 'PHYSICAL_SHAPE_VIOLATIONS_PRESENT'
    text=f'''# M12 physical-shape diagnostic\n\nNo parameter was refitted. The frozen M12 coefficients were applied to complete 24-hour curves on a 0.05-h grid.\n\n## Validation checkpoint correction magnitudes (2017-2024, DTR>=15 C)\n- active observed checkpoints: **{len(mags)}**\n- all-branch correction P50/P90/P95/P99/max: **{pct(mags,.5):.2f} / {pct(mags,.9):.2f} / {pct(mags,.95):.2f} / {pct(mags,.99):.2f} / {max(mags,default=0):.2f} C**\n- pre-peak correction P95/max: **{pct(pre,.95):.2f} / {max(pre,default=0):.2f} C**\n- post-peak correction P95/max: **{pct(post,.95):.2f} / {max(post,default=0):.2f} C**\n\n## Full-curve physical checks\n| Period | High-DTR days | Rise non-monotonic | Fall non-monotonic | Curve below daily Tmin | Max rise reversal per 0.05h | Max fall reversal per 0.05h | Max Tmin undershoot |\n|---|---:|---:|---:|---:|---:|---:|---:|\n| Calibration 2000-2016 | {sc['n']} | {sc['rise_bad']} | {sc['fall_bad']} | {sc['below']} | {sc['max_rev_rise']:.3f} | {sc['max_rev_fall']:.3f} | {sc['max_below']:.3f} C |\n| Validation 2017-2024 | {sv['n']} | {sv['rise_bad']} | {sv['fall_bad']} | {sv['below']} | {sv['max_rev_rise']:.3f} | {sv['max_rev_fall']:.3f} | {sv['max_below']:.3f} C |\n\nAutomated verdict: **{verdict}**.\n\nIf violations are present, M12 remains valid as mechanism/statistical evidence but the source implementation must use a monotonic shape transformation rather than direct additive shoulder subtraction.\n'''
    README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
