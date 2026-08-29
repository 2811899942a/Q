#!/usr/bin/env python3
"""Check temporal stability of the Urumqi post-peak shoulder parameters.

The structural form and DTRc=14.5 C are fixed. Recalibrate lambda and k separately
on 2000-2008 and 2009-2016, plus the full 2000-2016 calibration period. This is a
parameter-stability diagnostic before any Fortran source modification.
"""
import csv
from pathlib import Path
import test_dtr_phase_compression_51463 as base
import test_dtr_cooling_pulse_51463 as cp
import test_postpeak_shoulder_51463 as sh

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463'
OUT=DATA/'shoulder_parameter_stability.csv'; README=DATA/'README_SHOULDER_PARAMETER_STABILITY.md'

def search(rows):
    high=[r for r in rows if r['dtr']>=14.5];best=None
    kvals=[1.0+i*.5 for i in range(11)] # 1..6
    for k in kvals:
        for i in range(61):
            lam=i*.1
            fn=lambda r,L=lam,K=k:sh.shoulder(r,L,K)
            ma=base.metric(rows,fn);mh=base.metric(high,fn);obj=.5*ma['rmse']+.5*mh['rmse']
            rec={'lambda':lam,'k':k,'peak_q':1/(k+1),'objective':obj,'all_rmse':ma['rmse'],'high_rmse':mh['rmse']}
            if best is None or obj<best['objective']:best=rec
    return best

def main():
    rows=cp.load_rows(); periods=[('Full_2000_2016',[r for r in rows if r['year']<=2016]),('Early_2000_2008',[r for r in rows if r['year']<=2008]),('Late_2009_2016',[r for r in rows if 2009<=r['year']<=2016])]
    out=[]
    for name,s in periods:
        b=search(s);out.append({'period':name,'n_points':len(s),'n_high_points':sum(r['dtr']>=14.5 for r in s),**{k:round(v,5) if isinstance(v,float) else v for k,v in b.items()}})
    with OUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
    full=out[0];e=out[1];l=out[2]
    txt=f'''# Urumqi shoulder parameter stability

Same formula and DTRc=14.5 C were recalibrated independently in two non-overlapping subperiods.

| Period | N | High-DTR N | lambda | k | peak q | high-DTR calibration RMSE |
|---|---:|---:|---:|---:|---:|---:|
'''
    for r in out:txt+=f"| {r['period']} | {r['n_points']} | {r['n_high_points']} | {r['lambda']:.2f} | {r['k']:.2f} | {r['peak_q']:.3f} | {r['high_rmse']:.4f} |\n"
    txt+=f'''\nEarly-vs-late parameter differences: lambda **{abs(float(e['lambda'])-float(l['lambda'])):.2f}**, k **{abs(float(e['k'])-float(l['k'])):.2f}**.

A source-level parameterization is considered reasonably stable only if both subperiods retain the same qualitative early-post-peak shoulder shape and do not drive lambda/k to opposite search boundaries.
''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
