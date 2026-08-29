#!/usr/bin/env python3
"""Diagnose whether dense Diwopu observations require a DTR-dependent daytime peak width.

Starting from the independently calibrated single Diwopu PL baseline
A=1.849, B=0.740, C=0.242, replace only the daytime sine shape by:

    T = Tmin + (Tmax-Tmin) * sin(theta)^p

p=1 is the original Parton-Logan shape. p>1 narrows the high-temperature shoulder
while preserving Tmin/Tmax anchors. Sunset temperature is evaluated with the same p
and passed to the original night exponential branch, preserving continuity.

For each calibration-period DTR bin, fit p only. Then apply that bin-specific p to
untouched 2017-2024 data in the same bin. This is a mechanism diagnostic, not yet the
final continuous source parameterization.
"""
import csv, math
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar
import calibrate_dense_514635_pl as core

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_514635'
OUT=DATA/'diwopu_peak_width_by_dtr.csv'; README=DATA/'README_DIWOPU_PEAK_WIDTH.md'
A,B,C=1.849,0.740,0.242
BINS=[('<10',-1e9,10),('10-<12',10,12),('12-<13',12,13),('13-<14',13,14),('14-<14.5',14,14.5),('14.5-<16',14.5,16),('16-<18',16,18),('18-<20',18,20),('>=20',20,1e9)]

def predict(arr,p):
    hs=arr[:,2];tmax=arr[:,4];tmin=arr[:,5];dayl=arr[:,6];snup=arr[:,7];sndn=arr[:,8]
    tmin_time=snup+C;tmax_time=tmin_time+dayl/2+A
    theta_s=.5*np.pi*(sndn-tmin_time)/(tmax_time-tmin_time);ss=np.clip(np.sin(theta_s),1e-8,None);ts=tmin+(tmax-tmin)*(ss**p)
    eb=np.exp(-B);tmini=(tmin-ts*eb)/(1-eb);hdecay=24+C-dayl
    out=np.empty(len(arr));day=(hs>=snup+C)&(hs<=sndn)
    theta=.5*np.pi*(hs[day]-tmin_time[day])/(tmax_time[day]-tmin_time[day]);s=np.clip(np.sin(theta),0,None);out[day]=tmin[day]+(tmax[day]-tmin[day])*(s**p)
    night=~day;tt=np.where(hs[night]<snup[night]+C,24+hs[night]-sndn[night],hs[night]-sndn[night]);out[night]=tmini[night]+(ts[night]-tmini[night])*np.exp(-B*tt/hdecay[night]);return out

def met(arr,p):
    pr=predict(arr,p);e=pr-arr[:,3];r=float(np.corrcoef(arr[:,3],pr)[0,1]**2) if len(arr)>2 else float('nan');return float(np.sqrt(np.mean(e*e))),float(np.mean(np.abs(e))),float(np.mean(e)),r

def main():
    arr=np.array(core.load_points(),float);cal=arr[arr[:,0]<=2016];val=arr[arr[:,0]>=2017]
    rows=[]
    for name,lo,hi in BINS:
        ca=cal[(cal[:,1]>=lo)&(cal[:,1]<hi)];va=val[(val[:,1]>=lo)&(val[:,1]<hi)]
        if len(ca)<100:continue
        res=minimize_scalar(lambda p:met(ca,p)[0],bounds=(.25,5.0),method='bounded',options={'xatol':1e-5});p=float(res.x)
        mcal1=met(ca,1);mcal=met(ca,p);mval1=met(va,1) if len(va) else (float('nan'),)*4;mval=met(va,p) if len(va) else (float('nan'),)*4
        rows.append({'dtr_bin':name,'n_cal':len(ca),'n_val':len(va),'mean_dtr_cal':round(float(np.mean(ca[:,1])),3),'p_opt_cal':round(p,5),'p_at_lower_bound':'YES' if p<.27 else 'NO','p_at_upper_bound':'YES' if p>4.98 else 'NO','cal_rmse_p1':round(mcal1[0],4),'cal_rmse_popt':round(mcal[0],4),'val_rmse_p1':round(mval1[0],4),'val_rmse_popt':round(mval[0],4),'val_bias_popt':round(mval[2],4),'val_r2_popt':round(mval[3],4)})
    with OUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    txt='# Dense Diwopu daytime peak-width exponent diagnostic\n\nBaseline A/B/C are fixed at 1.849/0.740/0.242. Only `p` in `sin(theta)^p` is fitted separately within each 2000-2016 DTR bin.\n\n| DTR | Mean DTR cal | p optimum | Cal RMSE p=1 -> p | Val RMSE p=1 -> p | Val Bias(p) |\n|---|---:|---:|---:|---:|---:|\n'
    for r in rows:txt+=f"| {r['dtr_bin']} | {r['mean_dtr_cal']:.2f} | {r['p_opt_cal']:.3f} | {r['cal_rmse_p1']:.3f} -> {r['cal_rmse_popt']:.3f} | {r['val_rmse_p1']:.3f} -> {r['val_rmse_popt']:.3f} | {r['val_bias_popt']:.3f} |\n"
    txt+='''\nInterpretation: a reproducible rise of p above 1 with DTR would directly support a DTR-dependent narrowing of the daytime thermal peak. Lack of a systematic p-DTR relationship would reject this mechanism before any source modification.\n''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
