#!/usr/bin/env python3
"""Separate dense Diwopu daytime shape diagnostics into pre-peak and post-peak phases.

Baseline is the single calibrated Diwopu PL A=1.849,B=0.740,C=0.242. For mechanism
discovery only, fit exponent p in z=sin(theta)^p using *daytime points only*:
- full daytime Tmin-time to sunset;
- pre-peak Tmin-time to modeled Tmax time;
- post-peak modeled Tmax time to sunset.
Nighttime is excluded so the inferred daytime shape is not confounded by the sunset
value propagated through the night exponential.
"""
import csv
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar
import calibrate_dense_514635_pl as core

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_514635';OUT=DATA/'diwopu_day_phase_exponents.csv';README=DATA/'README_DIWOPU_DAY_PHASES.md'
A,B,C=1.849,.740,.242
BINS=[('<10',-1e9,10),('10-<12',10,12),('12-<13',12,13),('13-<14',13,14),('14-<14.5',14,14.5),('14.5-<16',14.5,16),('16-<18',16,18),('18-<20',18,20),('>=20',20,1e9)]

def phase_mask(arr,phase):
    hs=arr[:,2];dayl=arr[:,6];snup=arr[:,7];sndn=arr[:,8];tmin_time=snup+C;tpeak=tmin_time+dayl/2+A
    if phase=='day':return (hs>=tmin_time)&(hs<=sndn)
    if phase=='pre':return (hs>=tmin_time)&(hs<=tpeak)
    return (hs>tpeak)&(hs<=sndn)
def pred_day(arr,p):
    hs=arr[:,2];tmax=arr[:,4];tmin=arr[:,5];dayl=arr[:,6];snup=arr[:,7];tmin_time=snup+C;tpeak=tmin_time+dayl/2+A;theta=.5*np.pi*(hs-tmin_time)/(tpeak-tmin_time);s=np.clip(np.sin(theta),1e-8,None);return tmin+(tmax-tmin)*(s**p)
def metric(arr,p):
    pr=pred_day(arr,p);e=pr-arr[:,3];r=float(np.corrcoef(arr[:,3],pr)[0,1]**2) if len(arr)>2 else float('nan');return float(np.sqrt(np.mean(e*e))),float(np.mean(np.abs(e))),float(np.mean(e)),r
def main():
    arr=np.array(core.load_points(),float);cal=arr[arr[:,0]<=2016];val=arr[arr[:,0]>=2017];rows=[]
    for phase in ['day','pre','post']:
        for name,lo,hi in BINS:
            ca=cal[(cal[:,1]>=lo)&(cal[:,1]<hi)];va=val[(val[:,1]>=lo)&(val[:,1]<hi)];ca=ca[phase_mask(ca,phase)];va=va[phase_mask(va,phase)]
            if len(ca)<50:continue
            res=minimize_scalar(lambda p:metric(ca,p)[0],bounds=(.25,5),method='bounded');p=float(res.x);m1=metric(ca,1);mp=metric(ca,p);v1=metric(va,1) if len(va) else (float('nan'),)*4;vp=metric(va,p) if len(va) else (float('nan'),)*4
            rows.append({'phase':phase,'dtr_bin':name,'n_cal':len(ca),'n_val':len(va),'mean_dtr_cal':round(float(np.mean(ca[:,1])),3),'p_opt_cal':round(p,4),'cal_rmse_p1':round(m1[0],4),'cal_rmse_p':round(mp[0],4),'val_rmse_p1':round(v1[0],4),'val_rmse_p':round(vp[0],4),'val_bias_p':round(vp[2],4),'val_r2_p':round(vp[3],4)})
    with OUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    txt='# Dense Diwopu phase-separated daytime exponent diagnostic\n\nOnly daytime observations are fitted; night is excluded. `p>1` means a narrower/lower sine shoulder away from Tmax; `p<1` means broader/higher shoulder.\n\n| Phase | DTR | p | Val RMSE p=1 -> p | Val Bias(p) |\n|---|---|---:|---:|---:|\n'
    for r in rows:
        if r['dtr_bin'] in {'12-<13','13-<14','14-<14.5','14.5-<16','16-<18'}:txt+=f"| {r['phase']} | {r['dtr_bin']} | {r['p_opt_cal']:.3f} | {r['val_rmse_p1']:.3f} -> {r['val_rmse_p']:.3f} | {r['val_bias_p']:.3f} |\n"
    txt+='''\nA mechanism is retained only if the phase-specific p trend is coherent across adjacent DTR bins and improves independent validation, not merely calibration.\n''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
