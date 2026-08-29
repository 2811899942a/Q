#!/usr/bin/env python3
"""One-time expanded gamma search for the physically monotonic Urumqi post-peak warp."""
import csv
from pathlib import Path
import test_dtr_phase_compression_51463 as base
import test_dtr_cooling_pulse_51463 as cp
import test_monotonic_postpeak_warp_51463 as mw
DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463';GRID=DATA/'monotonic_warp_refined_grid.csv';VAL=DATA/'monotonic_warp_refined_validation.csv';README=DATA/'README_MONOTONIC_WARP_REFINED.md'
def write(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
def main():
    rows=cp.load_rows();cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];high=[r for r in cal if r['dtr']>=14.5]
    grid=[];best=None
    for i in range(201):
        g=i*.01;fn=lambda r,G=g:mw.warp(r,G);ma=base.metric(cal,fn);mh=base.metric(high,fn);obj=.5*ma['rmse']+.5*mh['rmse'];rec={'gamma':g,'cal_all_rmse':ma['rmse'],'cal_high_rmse':mh['rmse'],'objective':obj};grid.append(rec)
        if best is None or obj<best['objective']:best=rec
    g=best['gamma'];boundary=g in {0.0,2.0}
    models=[('M0',cp.original),('M1_PL_XJ',cp.pl_xj),('M2_WARP',lambda r:mw.warp(r,g))];out=[]
    for scope,s in [('May-Sep',val),('DTR>=15',[r for r in val if r['dtr']>=15]),('15-18',[r for r in val if 15<=r['dtr']<18]),('18-20',[r for r in val if 18<=r['dtr']<20]),('>=20',[r for r in val if r['dtr']>=20])]:
        for name,fn in models:
            m=base.metric(s,fn);out.append({'scope':scope,'model':name,'gamma':g if name=='M2_WARP' else '',**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})
    write(GRID,[{k:round(v,6) if isinstance(v,float) else v for k,v in r.items()} for r in grid]);write(VAL,out)
    mp={(r['scope'],r['model']):r for r in out};o=mp[('DTR>=15','M0')];b=mp[('DTR>=15','M1_PL_XJ')];m=mp[('DTR>=15','M2_WARP')];imp=100*(o['rmse']-m['rmse'])/o['rmse'];imp1=100*(b['rmse']-m['rmse'])/b['rmse']
    txt=f'''# Refined Urumqi monotonic post-peak warp

- Gamma search: **0.00-2.00 per C**, step 0.01.
- Best gamma: **{g:.2f} per C**.
- Optimum at search boundary: **{'YES' if boundary else 'NO'}**.
- Independent DTR>=15 RMSE: official **{o['rmse']:.4f}**, PL-XJ **{b['rmse']:.4f}**, warp **{m['rmse']:.4f} C**.
- Improvement vs official: **{imp:.2f}%**; additional improvement beyond PL-XJ: **{imp1:.2f}%**.
- DTR>=15 Bias: **{m['mbe']:.4f} C**; R2: **{m['r2']:.4f}**.

The expanded search is accepted only if gamma is interior. The equation remains monotonic and anchor-preserving for any nonnegative gamma by construction.
''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
