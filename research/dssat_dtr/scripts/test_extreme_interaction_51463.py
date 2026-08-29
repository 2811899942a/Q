#!/usr/bin/env python3
"""Test whether Tmax/Tmin extremes add explanatory value beyond DTR excess.

Outcome: daily afternoon HTEMP bias (May-Sep).
Calibration: 2000-2016. Independent validation: 2017-2024.
The diagnostic compares linear predictors fitted only on calibration data:
  DTR:          1 + DTRplus
  DTR+HOT:      1 + DTRplus + hot_excess
  DTR+COLD:     1 + DTRplus + cold_excess
  DTR+HOT+COLD: 1 + DTRplus + hot_excess + cold_excess
where DTRplus=max(0,DTR-14.5), hot_excess=max(0,Tmax-33.5),
and cold_excess=max(0,9.6-Tmin).

This is used only to decide whether the future DSSAT correction needs temperature-
extreme triggers; it is not itself the HTEMP correction formula.
"""
import csv, math, statistics
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/'data'/'processed_51463'
IN=DATA/'dtr_asymmetry_daily.csv'; OUT=DATA/'extreme_interaction_models.csv'; README=DATA/'README_EXTREME_INTERACTION.md'
DTRC=14.5; HOT=33.5; COLD=9.6


def solve(A,b):
    n=len(b);m=[list(A[i])+[b[i]] for i in range(n)]
    for c in range(n):
        p=max(range(c,n),key=lambda r:abs(m[r][c]));
        if abs(m[p][c])<1e-10:return None
        m[c],m[p]=m[p],m[c];d=m[c][c]
        for j in range(c,n+1):m[c][j]/=d
        for r in range(n):
            if r==c:continue
            f=m[r][c]
            for j in range(c,n+1):m[r][j]-=f*m[c][j]
    return [m[i][n] for i in range(n)]

def fit(rows,features):
    X=[];y=[]
    for r in rows:
        x=[1.0]+[r[k] for k in features];X.append(x);y.append(r['y'])
    p=len(X[0]);A=[[sum(x[i]*x[j] for x in X) for j in range(p)] for i in range(p)];b=[sum(x[i]*yy for x,yy in zip(X,y)) for i in range(p)]
    beta=solve(A,b);return beta

def evaluate(rows,features,beta):
    e=[]
    for r in rows:
        x=[1.0]+[r[k] for k in features];pred=sum(a*b for a,b in zip(x,beta));e.append(pred-r['y'])
    rmse=math.sqrt(statistics.mean([z*z for z in e]));mae=statistics.mean(abs(z) for z in e);bias=statistics.mean(e)
    return rmse,mae,bias

def main():
    rows=[]
    with IN.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['season']!='May-Sep' or r.get('afternoon_bias_c','')=='':continue
            year=int(r['solar_date'][:4]);dtr=float(r['dtr_c']);tmax=float(r['tmax_c']);tmin=float(r['tmin_c'])
            rows.append({'year':year,'y':float(r['afternoon_bias_c']),'dtrplus':max(0,dtr-DTRC),'hot':max(0,tmax-HOT),'cold':max(0,COLD-tmin),'high':dtr>=DTRC})
    cal=[r for r in rows if r['year']<=2016];val=[r for r in rows if r['year']>=2017];val_high=[r for r in val if r['high']]
    models=[('DTR',['dtrplus']),('DTR+HOT',['dtrplus','hot']),('DTR+COLD',['dtrplus','cold']),('DTR+HOT+COLD',['dtrplus','hot','cold'])]
    out=[]
    for name,feat in models:
        beta=fit(cal,feat);vr=evaluate(val,feat,beta);vh=evaluate(val_high,feat,beta)
        out.append({'model':name,'features':'+'.join(feat),'coefficients':';'.join(f'{x:.5f}' for x in beta),'val_all_rmse':round(vr[0],4),'val_all_mae':round(vr[1],4),'val_all_bias':round(vr[2],4),'val_high_dtr_rmse':round(vh[0],4),'val_high_dtr_mae':round(vh[1],4),'val_high_dtr_bias':round(vh[2],4)})
    with OUT.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
    base=out[0];best=min(out,key=lambda r:r['val_high_dtr_rmse']);gain=100*(base['val_high_dtr_rmse']-best['val_high_dtr_rmse'])/base['val_high_dtr_rmse']
    txt=f'''# Extreme-temperature interaction diagnostic

Thresholds are diagnostic values established before this fit: DTRc={DTRC} C, hot Tmax>{HOT} C (May-Sep P90), cold Tmin<{COLD} C (May-Sep P10).

| Model | Validation all RMSE | Validation high-DTR RMSE | High-DTR MAE | High-DTR Bias |
|---|---:|---:|---:|---:|
'''
    for r in out:txt+=f"| {r['model']} | {r['val_all_rmse']:.4f} | {r['val_high_dtr_rmse']:.4f} | {r['val_high_dtr_mae']:.4f} | {r['val_high_dtr_bias']:.4f} |\n"
    txt+=f'''\nBest independent high-DTR predictor: **{best['model']}**. Improvement over DTR-only residual predictor: **{gain:.2f}%**.

Decision: add hot/cold extreme triggers to the HTEMP structural correction only if they produce a material independent-validation gain beyond DTR excess alone. Otherwise keep the source modification parsimonious and DTR-driven.
'''
    README.write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
