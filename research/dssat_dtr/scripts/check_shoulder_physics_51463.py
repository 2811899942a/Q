#!/usr/bin/env python3
"""Physical QA for the additive Urumqi post-peak shoulder candidate.

Checks continuous 5-minute post-peak curves on unique May-Sep high-DTR days for:
- any temperature increase after the modeled peak before sunset;
- Tmin clipping;
- interior local minima followed by rebound toward sunset.
This QA is required before source-level DSSAT implementation.
"""
import csv,math
from pathlib import Path
import test_dtr_phase_compression_51463 as base
import test_dtr_cooling_pulse_51463 as cp
import test_postpeak_shoulder_51463 as sh
DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463';OUT=DATA/'shoulder_physical_qa.csv';README=DATA/'README_SHOULDER_PHYSICS.md'

def main():
    rows=cp.load_rows(); days={}
    for r in rows:
        if r['dtr']>=14.5:days.setdefault(r['date'],r)
    rec=[]
    for date,r in sorted(days.items()):
        A,B,C=base.PL_XJ_BAL;tmin_time=r['snup']+C;tpeak=tmin_time+r['dayl']/2+A;sunset=r['sndn']
        ts=[];raw_below=0
        n=0
        if sunset<=tpeak:continue
        h=tpeak
        while h<=sunset+1e-9:
            rr=dict(r);rr['hs']=h
            tpl=cp.pl_xj(rr);e=max(0,r['dtr']-14.5);q=(h-tpeak)/(sunset-tpeak) if h>tpeak else 0.0
            raw=q*((1-q)**2.0);qs=1/3;mx=qs*((1-qs)**2);corr=4.70*e*(raw/mx if mx>0 else 0);unclipped=tpl-corr
            if unclipped<r['tmin']-1e-9:raw_below+=1
            t=max(r['tmin'],unclipped);ts.append(t);n+=1;h+=1/12
        inc=sum(ts[i+1]>ts[i]+0.02 for i in range(len(ts)-1));max_inc=max([ts[i+1]-ts[i] for i in range(len(ts)-1)] or [0])
        imin=min(range(len(ts)),key=lambda i:ts[i]);rebound=max(ts[imin:])-ts[imin] if imin<len(ts)-1 else 0
        rec.append({'date':date,'dtr_c':r['dtr'],'n_steps':n,'increasing_steps':inc,'any_postpeak_increase':'YES' if inc else 'NO','max_5min_increase_c':round(max_inc,4),'raw_below_tmin_steps':raw_below,'tmin_clipping':'YES' if raw_below else 'NO','post_min_rebound_c':round(rebound,4),'rebound_gt_0.5c':'YES' if rebound>0.5 else 'NO'})
    with OUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rec[0].keys()));w.writeheader();w.writerows(rec)
    n=len(rec);inc=sum(r['any_postpeak_increase']=='YES' for r in rec);clip=sum(r['tmin_clipping']=='YES' for r in rec);reb=sum(r['rebound_gt_0.5c']=='YES' for r in rec)
    txt=f'''# Physical QA — additive post-peak shoulder

High-DTR May-Sep days checked: **{n}**. Curves sampled every 5 minutes from PL-XJ peak to sunset.

- Days with any post-peak temperature increase before sunset: **{inc}/{n} ({100*inc/n:.1f}%)**.
- Days requiring Tmin clipping: **{clip}/{n} ({100*clip/n:.1f}%)**.
- Days with >0.5 C rebound after an interior post-peak minimum: **{reb}/{n} ({100*reb/n:.1f}%)**.

A source-level HTEMP candidate should normally preserve monotonic cooling from the daily peak toward sunset under this simplified clear DTR-driven mechanism. If rebound/clipping is common, the additive shoulder is rejected as a final equation even if its checkpoint RMSE improves; its value is then diagnostic evidence locating the structural error in the early post-peak shoulder.
''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
