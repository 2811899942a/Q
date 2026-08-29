#!/usr/bin/env python3
"""Diagnose DTR-dependent residual structure after station-specific PL calibration at Diwopu.

Uses the independently calibrated Diwopu parameters A=1.849, B=0.740, C=0.242
(from 2000-2016 May-Sep all-hour calibration) and evaluates untouched 2017-2024.
The key question is whether RMSE still exhibits a DTR breakpoint after ordinary
parameter-transfer error has been removed.
"""
import csv, math, statistics
from collections import defaultdict
from pathlib import Path
import numpy as np
import calibrate_dense_514635_pl as calmod

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_514635'
P=np.array([1.849,0.740,0.242]); OFF=np.array([2.0,2.2,1.0])
OUT=DATA/'diwopu_calibrated_dtr_bins.csv'; DAILY=DATA/'diwopu_calibrated_daily_rmse.csv'; BP=DATA/'diwopu_calibrated_breakpoint.csv'; README=DATA/'README_DIWOPU_CALIBRATED_DTR.md'

def mean(x):return statistics.mean(x) if x else float('nan')
def rmse(x):return math.sqrt(mean([v*v for v in x])) if x else float('nan')
def dbin(d):
    if d<10:return '<10'
    if d<12:return '10-<12'
    if d<13:return '12-<13'
    if d<14:return '13-<14'
    if d<14.5:return '14-<14.5'
    if d<16:return '14.5-<16'
    if d<18:return '16-<18'
    if d<20:return '18-<20'
    return '>=20'
def solve3(A,b):
    m=[list(A[i])+[b[i]] for i in range(3)]
    for c in range(3):
        p=max(range(c,3),key=lambda r:abs(m[r][c]));m[c],m[p]=m[p],m[c]
        z=m[c][c]
        if abs(z)<1e-12:return None
        for j in range(c,4):m[c][j]/=z
        for r in range(3):
            if r==c:continue
            f=m[r][c]
            for j in range(c,4):m[r][j]-=f*m[c][j]
    return [m[i][3] for i in range(3)]
def breakpoint(rows):
    vals=[(r['dtr'],r['rmse']) for r in rows]
    best=None
    for i in range(101):
        c=9+i*.1
        if sum(x<=c for x,y in vals)<100 or sum(x>c for x,y in vals)<30:continue
        X=[(1,x,max(0,x-c)) for x,y in vals]
        A=[[sum(xx[i]*xx[j] for xx in X) for j in range(3)] for i in range(3)]
        b=[sum(xx[i]*y for xx,(x,y) in zip(X,vals)) for i in range(3)]
        be=solve3(A,b)
        if be is None:continue
        sse=sum((y-sum(be[j]*xx[j] for j in range(3)))**2 for xx,(x,y) in zip(X,vals))
        if best is None or sse<best['sse']:best={'breakpoint':c,'sse':sse,'b0':be[0],'slope_below':be[1],'slope_above':be[1]+be[2]}
    return best
def main():
    arr=np.array(calmod.load_points(),float); val=arr[arr[:,0]>=2017]
    pred_off=calmod.predict(OFF,val);pred_cal=calmod.predict(P,val)
    eoff=pred_off-val[:,3];ecal=pred_cal-val[:,3]
    bins=[]
    for b in ['<10','10-<12','12-<13','13-<14','14-<14.5','14.5-<16','16-<18','18-<20','>=20']:
        mask=np.array([dbin(x)==b for x in val[:,1]])
        if not np.any(mask):continue
        for name,e,pred in [('Official',eoff,pred_off),('Diwopu-PL',ecal,pred_cal)]:
            ee=e[mask];oo=val[mask,3];pp=pred[mask]
            rr=float(np.corrcoef(oo,pp)[0,1]**2) if len(oo)>2 else float('nan')
            bins.append({'dtr_bin':b,'model':name,'n_points':int(mask.sum()),'n_days':len(set(val[mask,0].astype(int).tolist())),'mean_dtr':round(float(np.mean(val[mask,1])),3),'rmse':round(float(np.sqrt(np.mean(ee*ee))),4),'mae':round(float(np.mean(np.abs(ee))),4),'bias':round(float(np.mean(ee)),4),'r2':round(rr,4)})
    with OUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(bins[0].keys()));w.writeheader();w.writerows(bins)

    # daily RMSE on validation data under calibrated model
    byday=defaultdict(list)
    for row,e in zip(val,ecal):
        # load_points lacks actual date, but each dense day has same dtr and ~20-24 rows; group sequentially by year+dtr is unsafe.
        # Reconstruct day blocks from repeated tmax/tmin/daylen/snup/sndn tuple, which uniquely identifies almost all days.
        key=(int(row[0]),round(row[4],3),round(row[5],3),round(row[6],6),round(row[7],6),round(row[8],6))
        byday[key].append((row,e))
    daily=[]
    for key,z in byday.items():
        dtr=float(z[0][0][1]);errs=[float(x[1]) for x in z]
        daily.append({'year':key[0],'dtr':dtr,'n_points':len(errs),'rmse':rmse(errs),'bias':mean(errs)})
    with DAILY.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(daily[0].keys()));w.writeheader();w.writerows(daily)
    bp=breakpoint(daily)
    with BP.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(bp.keys()));w.writeheader();w.writerow(bp)

    mp={(r['dtr_bin'],r['model']):r for r in bins}
    lines=['# Diwopu DTR residual after station-specific PL calibration','', '- Parameters fixed from 2000-2016 all-May-Sep calibration: **A=1.849, B=0.740, C=0.242**.', '- Diagnostics below use untouched **2017-2024** data.',f"- Best segmented breakpoint in calibrated daily RMSE: **{bp['breakpoint']:.1f} C**.",f"- RMSE slope below breakpoint: **{bp['slope_below']:.4f} C/C**; above: **{bp['slope_above']:.4f} C/C**.",'','## Independent validation by DTR','', '| DTR | Official RMSE | Calibrated RMSE | Calibrated Bias | Calibrated R2 |','|---|---:|---:|---:|---:|']
    for b in ['<10','10-<12','12-<13','13-<14','14-<14.5','14.5-<16','16-<18','18-<20','>=20']:
        if (b,'Official') in mp:
            o=mp[(b,'Official')];c=mp[(b,'Diwopu-PL')];lines.append(f"| {b} | {o['rmse']:.3f} | {c['rmse']:.3f} | {c['bias']:.3f} | {c['r2']:.3f} |")
    lines += ['','If calibrated RMSE remains low and flat below the breakpoint but rises sharply above it, the dense second station independently supports a DTR-dependent structural limitation beyond fixed A/B/C parameter transfer.']
    README.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))
if __name__=='__main__':main()
