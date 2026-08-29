#!/usr/bin/env python3
"""Invert observed post-peak temperatures into the equivalent PL-XJ cooling phase.

For each May-Sep observation after the PL-XJ peak and before sunset, use the monotonic
PL-XJ post-peak daytime branch to ask: at what normalized post-peak phase q_eff would
PL-XJ attain the observed temperature? Then compare q_eff with actual q.

This is mechanism discovery, not model fitting. It reveals the empirical phase advance
required by Urumqi observations and where a new source formula must act.
"""
import csv,math,statistics
from pathlib import Path
import test_dtr_phase_compression_51463 as base
import test_dtr_cooling_pulse_51463 as cp
DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463';POINT=DATA/'postpeak_phase_inversion_points.csv';SUMMARY=DATA/'postpeak_phase_inversion_summary.csv';README=DATA/'README_POSTPEAK_PHASE_INVERSION.md'

def median(x):return statistics.median(x) if x else float('nan')
def mean(x):return statistics.mean(x) if x else float('nan')
def dbin(d):
    if d<15:return '14.5-<15'
    if d<18:return '15-<18'
    if d<20:return '18-<20'
    return '>=20'
def qbin(q):
    if q<.2:return '0-<0.2'
    if q<.4:return '0.2-<0.4'
    if q<.6:return '0.4-<0.6'
    if q<.8:return '0.6-<0.8'
    return '0.8-1.0'
def main():
    rows=cp.load_rows();pts=[]
    A,B,C=base.PL_XJ_BAL
    for r in rows:
        if r['dtr']<14.5:continue
        tmin_time=r['snup']+C;tpeak=tmin_time+r['dayl']/2+A
        if not(tpeak<r['hs']<r['sndn']):continue
        q=(r['hs']-tpeak)/(r['sndn']-tpeak);tpl=cp.pl_xj(r);tsunset=base.htemp(r['sndn'],r['tmax'],r['tmin'],r['dayl'],r['snup'],r['sndn'],A,B,C,0)
        obs=r['obs'];status='MAPPABLE';qeff='';advance=''
        if obs>r['tmax']+0.05:status='OBS_ABOVE_TMAX'
        elif obs<tsunset-0.05:status='OBS_BELOW_PLXJ_SUNSET'
        else:
            z=(obs-r['tmin'])/(r['tmax']-r['tmin']) if r['tmax']>r['tmin'] else 0
            z=max(-1,min(1,z));theta=math.pi-math.asin(z)
            h_eff=tmin_time+(2*(tpeak-tmin_time)/math.pi)*theta
            qeff=(h_eff-tpeak)/(r['sndn']-tpeak);advance=qeff-q
        pts.append({'date':r['date'],'year':r['year'],'dtr_c':r['dtr'],'dtr_bin':dbin(r['dtr']),'solar_hour':r['hs'],'q_actual':round(q,5),'q_bin':qbin(q),'obs_c':obs,'plxj_c':round(tpl,4),'plxj_sunset_c':round(tsunset,4),'status':status,'q_eff_obs':('' if qeff=='' else round(qeff,5)),'phase_advance':('' if advance=='' else round(advance,5)),'split':'Calibration' if r['year']<=2016 else 'Validation'})
    with POINT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(pts[0].keys()));w.writeheader();w.writerows(pts)
    out=[]
    for split in ['All','Calibration','Validation']:
        basepts=pts if split=='All' else [r for r in pts if r['split']==split]
        for d in ['14.5-<15','15-<18','18-<20','>=20']:
            for qb in ['0-<0.2','0.2-<0.4','0.4-<0.6','0.6-<0.8','0.8-1.0']:
                s=[r for r in basepts if r['dtr_bin']==d and r['q_bin']==qb]
                if not s:continue
                m=[r for r in s if r['status']=='MAPPABLE'];adv=[float(r['phase_advance']) for r in m]
                out.append({'split':split,'dtr_bin':d,'q_bin':qb,'n_points':len(s),'n_mappable':len(m),'pct_below_plxj_sunset':round(100*sum(r['status']=='OBS_BELOW_PLXJ_SUNSET' for r in s)/len(s),2),'pct_above_tmax':round(100*sum(r['status']=='OBS_ABOVE_TMAX' for r in s)/len(s),2),'median_phase_advance':('' if not adv else round(median(adv),4)),'mean_phase_advance':('' if not adv else round(mean(adv),4)),'median_q_actual':round(median([float(r['q_actual']) for r in s]),4),'median_q_eff':('' if not m else round(median([float(r['q_eff_obs']) for r in m]),4))})
    with SUMMARY.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
    # headline for main 15-18 DTR bin in early and middle postpeak phases
    rows15=[r for r in out if r['split']=='All' and r['dtr_bin']=='15-<18']
    lines=['# Observed post-peak phase inversion — Urumqi 51463','',f'- High-DTR post-peak observation points: **{len(pts)}**.','- `phase_advance = q_eff(observed temperature) - q_actual`; positive values mean the observed atmosphere has cooled farther along the PL-XJ post-peak trajectory than the model at the same clock time.','', '## Main DTR 15-<18 C bin','', '| Actual post-peak q bin | N | Below PL-XJ sunset temp | Median q actual | Median q effective | Median phase advance |','|---|---:|---:|---:|---:|---:|']
    for r in rows15:lines.append(f"| {r['q_bin']} | {r['n_points']} | {r['pct_below_plxj_sunset']:.1f}% | {r['median_q_actual']:.3f} | {r['median_q_eff'] if r['median_q_eff']!='' else 'NA'} | {r['median_phase_advance'] if r['median_phase_advance']!='' else 'NA'} |")
    lines += ['','The inversion directly constrains the shape of the next formula. A strong positive advance at small q that diminishes by mid/late q supports an early post-peak shoulder-compression mechanism; a nearly constant advance would support a simpler global time shift.']
    README.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))
if __name__=='__main__':main()
