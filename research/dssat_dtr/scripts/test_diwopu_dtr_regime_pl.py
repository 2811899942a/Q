#!/usr/bin/env python3
"""Test a local DTR-regime adaptive Parton-Logan parameterization at dense Diwopu.

Workflow:
1. Fit a single station-specific PL A/B/C on all May-Sep 2000-2016 data.
2. Using only calibration-period daily RMSE under that single PL, diagnose the DTR
   breakpoint by segmented regression.
3. Fix that calibration-only breakpoint.
4. Independently fit A/B/C below and above the breakpoint, using only calibration data.
5. Validate the resulting two-regime PL on untouched 2017-2024 observations.

This directly tests whether the high-DTR structural signal can be represented as
DTR-state-dependent PL coefficients without adding arbitrary temperature corrections.
"""
import csv, math, statistics
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.optimize import differential_evolution
import calibrate_dense_514635_pl as core

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_514635'
OUT=DATA/'diwopu_regime_pl_validation.csv'; PARAM=DATA/'diwopu_regime_pl_parameters.csv'; HOUR=DATA/'diwopu_regime_pl_highdtr_by_hour.csv'; README=DATA/'README_DIWOPU_REGIME_PL.md'
BOUNDS=[(0,4),(.5,5),(0,2.5)]

def metric(arr,p):return core.metric(arr,np.array(p,float))
def fit(arr,seed):
    res=differential_evolution(lambda p:metric(arr,p)[0],BOUNDS,seed=seed,maxiter=35,popsize=10,tol=1e-5,polish=True,workers=1)
    return res.x,res

def solve3(A,b):
    m=[list(A[i])+[b[i]] for i in range(3)]
    for c in range(3):
        p=max(range(c,3),key=lambda r:abs(m[r][c]));m[c],m[p]=m[p],m[c];z=m[c][c]
        if abs(z)<1e-12:return None
        for j in range(c,4):m[c][j]/=z
        for r in range(3):
            if r==c:continue
            f=m[r][c]
            for j in range(c,4):m[r][j]-=f*m[c][j]
    return [m[i][3] for i in range(3)]
def daily_rows(arr,p):
    pred=core.predict(np.array(p,float),arr);err=pred-arr[:,3];g=defaultdict(list)
    for row,e in zip(arr,err):
        key=(int(row[0]),round(row[4],3),round(row[5],3),round(row[6],6),round(row[7],6),round(row[8],6))
        g[key].append((row,e))
    out=[]
    for z in g.values():
        d=float(z[0][0][1]);es=[float(v[1]) for v in z];out.append((d,math.sqrt(statistics.mean([x*x for x in es]))))
    return out
def find_breakpoint(daily):
    best=None
    for i in range(91):
        c=9+i*.1
        if sum(x<=c for x,y in daily)<150 or sum(x>c for x,y in daily)<50:continue
        X=[(1,x,max(0,x-c)) for x,y in daily]
        A=[[sum(xx[i]*xx[j] for xx in X) for j in range(3)] for i in range(3)]
        b=[sum(xx[i]*y for xx,(x,y) in zip(X,daily)) for i in range(3)];be=solve3(A,b)
        if be is None:continue
        sse=sum((y-sum(be[j]*xx[j] for j in range(3)))**2 for xx,(x,y) in zip(X,daily))
        if best is None or sse<best['sse']:best={'threshold':c,'sse':sse,'slope_below':be[1],'slope_above':be[1]+be[2]}
    return best

def model_predict(arr,threshold,p_low,p_high):
    pred=np.empty(len(arr));low=arr[:,1]<threshold
    pred[low]=core.predict(np.array(p_low,float),arr[low]);pred[~low]=core.predict(np.array(p_high,float),arr[~low]);return pred
def metrics_from_pred(arr,pred):
    e=pred-arr[:,3];r=float(np.corrcoef(arr[:,3],pred)[0,1]**2) if len(arr)>2 else float('nan')
    return float(np.sqrt(np.mean(e*e))),float(np.mean(np.abs(e))),float(np.mean(e)),r

def main():
    arr=np.array(core.load_points(),float);cal=arr[arr[:,0]<=2016];val=arr[arr[:,0]>=2017]
    p_all,res_all=fit(cal,42)
    bp=find_breakpoint(daily_rows(cal,p_all));thr=bp['threshold']
    low_cal=cal[cal[:,1]<thr];high_cal=cal[cal[:,1]>=thr]
    p_low,res_low=fit(low_cal,43);p_high,res_high=fit(high_cal,44)
    params=[
        {'regime':'single_all','threshold_c':thr,'A':p_all[0],'B':p_all[1],'C':p_all[2],'peak_solar_h':12+p_all[0]+p_all[2],'n_cal':len(cal),'rmse_cal':metric(cal,p_all)[0]},
        {'regime':'low_DTR','threshold_c':thr,'A':p_low[0],'B':p_low[1],'C':p_low[2],'peak_solar_h':12+p_low[0]+p_low[2],'n_cal':len(low_cal),'rmse_cal':metric(low_cal,p_low)[0]},
        {'regime':'high_DTR','threshold_c':thr,'A':p_high[0],'B':p_high[1],'C':p_high[2],'peak_solar_h':12+p_high[0]+p_high[2],'n_cal':len(high_cal),'rmse_cal':metric(high_cal,p_high)[0]},
    ]
    with PARAM.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(params[0].keys()));w.writeheader();w.writerows(params)
    off=np.array([2.,2.2,1.]);pred_single=core.predict(p_all,val);pred_reg=model_predict(val,thr,p_low,p_high);pred_off=core.predict(off,val)
    rows=[]
    scopes=[('All_MaySep',np.ones(len(val),dtype=bool)),(f'DTR<{thr:.1f}',val[:,1]<thr),(f'DTR>={thr:.1f}',val[:,1]>=thr),('DTR14.5-18',(val[:,1]>=14.5)&(val[:,1]<18))]
    for scope,mask in scopes:
        s=val[mask]
        for name,pred in [('Official',pred_off[mask]),('Single_Diwopu_PL',pred_single[mask]),('DTR_Regime_PL',pred_reg[mask])]:
            m=metrics_from_pred(s,pred);rows.append({'scope':scope,'model':name,'n':len(s),'rmse':round(m[0],4),'mae':round(m[1],4),'bias':round(m[2],4),'r2':round(m[3],4)})
    with OUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    # High-DTR hourly diagnostics in the main 14.5-18 range.
    mask=(val[:,1]>=14.5)&(val[:,1]<18);s=val[mask];po=pred_off[mask];ps=pred_single[mask];pr=pred_reg[mask]
    hrs=[]
    for h in range(24):
        hm=np.floor(s[:,2]).astype(int)%24==h
        if not np.any(hm):continue
        for name,pred in [('Official',po[hm]),('Single_Diwopu_PL',ps[hm]),('DTR_Regime_PL',pr[hm])]:
            m=metrics_from_pred(s[hm],pred);hrs.append({'solar_hour':h,'model':name,'n':int(hm.sum()),'rmse':round(m[0],4),'mae':round(m[1],4),'bias':round(m[2],4),'r2':round(m[3],4)})
    with HOUR.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(hrs[0].keys()));w.writeheader();w.writerows(hrs)
    mp={(r['scope'],r['model']):r for r in rows};highkey=f'DTR>={thr:.1f}';a=mp[('All_MaySep','Single_Diwopu_PL')];ar=mp[('All_MaySep','DTR_Regime_PL')];h=mp[(highkey,'Single_Diwopu_PL')];hr=mp[(highkey,'DTR_Regime_PL')]
    imp_all=100*(a['rmse']-ar['rmse'])/a['rmse'];imp_high=100*(h['rmse']-hr['rmse'])/h['rmse']
    txt=f'''# Dense Diwopu DTR-regime adaptive Parton-Logan test

## Calibration-only regime discovery
- Single station PL parameters: A={p_all[0]:.3f}, B={p_all[1]:.3f}, C={p_all[2]:.3f}.
- Calibration-period RMSE breakpoint after single-PL fitting: **{thr:.1f} C**.
- Calibration daily-RMSE slope below/above breakpoint: **{bp['slope_below']:.4f} / {bp['slope_above']:.4f} C per C DTR**.

## Regime-specific parameters
| Regime | A | B | C | Implied peak solar hour | Calibration points |
|---|---:|---:|---:|---:|---:|
| Low DTR <{thr:.1f} | {p_low[0]:.3f} | {p_low[1]:.3f} | {p_low[2]:.3f} | {12+p_low[0]+p_low[2]:.3f} | {len(low_cal)} |
| High DTR >={thr:.1f} | {p_high[0]:.3f} | {p_high[1]:.3f} | {p_high[2]:.3f} | {12+p_high[0]+p_high[2]:.3f} | {len(high_cal)} |

## Independent 2017-2024 validation
- All May-Sep RMSE: single PL **{a['rmse']:.4f} C** -> DTR-regime PL **{ar['rmse']:.4f} C** ({imp_all:.2f}% additional improvement).
- High-DTR RMSE (>={thr:.1f} C): single PL **{h['rmse']:.4f} C** -> regime PL **{hr['rmse']:.4f} C** ({imp_high:.2f}% additional improvement).
- High-DTR bias: **{h['bias']:.4f} -> {hr['bias']:.4f} C**; R2: **{h['r2']:.4f} -> {hr['r2']:.4f}**.

Interpretation: if high- and low-DTR optimum coefficients differ materially and the fixed calibration-only regime switch improves independent validation, this supports a parsimonious **DTR-state-adaptive Parton-Logan** formulation. If validation gain is small, fixed A/B/C are not the only structural limitation and a continuous shape parameterization is still needed.
''';README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
