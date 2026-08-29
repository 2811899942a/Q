#!/usr/bin/env python3
"""One-time expanded search for the Urumqi DTR-triggered cooling-pulse amplitude.

Search lambda from 0 to 4 (step 0.01). DTRc remains fixed at 14.5 C and the
functional shape is unchanged. If the optimum is still at the boundary, this
one-parameter amplitude model is rejected as too restrictive.
"""
import csv
from pathlib import Path
import test_dtr_phase_compression_51463 as base
import test_dtr_cooling_pulse_51463 as cp

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463'
GRID=DATA/'dtr_cooling_pulse_refined_grid.csv'
VAL=DATA/'dtr_cooling_pulse_refined_validation.csv'
README=DATA/'README_DTR_COOLING_PULSE_REFINED.md'


def write(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)


def main():
    rows=cp.load_rows();cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017]
    high=[r for r in cal if r['dtr']>=cp.DTR_C]
    grid=[];best=None
    for i in range(401):
        lam=i*0.01
        fn=lambda r,L=lam:cp.cooling_pulse(r,L)
        ma=base.metric(cal,fn);mh=base.metric(high,fn)
        obj=.5*ma['rmse']+.5*mh['rmse']
        rec={'lambda':lam,'cal_all_rmse':ma['rmse'],'cal_high_rmse':mh['rmse'],'objective':obj}
        grid.append(rec)
        if best is None or obj<best['objective']:best=rec
    lam=best['lambda'];boundary=lam in {0.0,4.0}
    models=[('M0',cp.original),('M1_PL_XJ',cp.pl_xj),('M2_PHASE',cp.phase_compression),('M3_COOLING',lambda r:cp.cooling_pulse(r,lam))]
    result=[]
    for scope,s in [('May-Sep',val),('DTR>=15',[r for r in val if r['dtr']>=15]),('DTR15-18',[r for r in val if 15<=r['dtr']<18]),('DTR18-20',[r for r in val if 18<=r['dtr']<20]),('DTR>=20',[r for r in val if r['dtr']>=20])]:
        for name,fn in models:
            m=base.metric(s,fn);result.append({'scope':scope,'model':name,'lambda':lam if name=='M3_COOLING' else 0,**{k:round(v,4) if isinstance(v,float) else v for k,v in m.items()}})
    write(GRID,[{k:round(v,6) if isinstance(v,float) else v for k,v in r.items()} for r in grid]);write(VAL,result)
    mp={(r['scope'],r['model']):r for r in result};m0=mp[('DTR>=15','M0')];m3=mp[('DTR>=15','M3_COOLING')]
    imp=100*(m0['rmse']-m3['rmse'])/m0['rmse']
    txt=f'''# Refined Urumqi cooling-pulse amplitude

- Fixed DTRc: **14.5 C**
- Lambda search: **0.00-4.00**, step 0.01
- Best lambda: **{lam:.2f}**
- Optimum at boundary: **{'YES' if boundary else 'NO'}**
- Independent DTR>=15 RMSE: official **{m0['rmse']:.4f} C** -> cooling pulse **{m3['rmse']:.4f} C**
- Improvement: **{imp:.2f}%**
- DTR>=15 Bias: official **{m0['mbe']:.4f} C** -> cooling pulse **{m3['mbe']:.4f} C**

If the optimum is interior, lambda can be retained as the first local structural coefficient. If it is again at the upper boundary, stop amplitude expansion and introduce a second shape degree of freedom.
'''
    README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
