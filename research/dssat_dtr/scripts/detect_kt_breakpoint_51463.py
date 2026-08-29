#!/usr/bin/env python3
"""Detect a calibration-only Kt breakpoint in high-DTR Urumqi HTEMP errors.

Input is the main-station daily residual + SRAD file. Kt = SRAD/Ra where Ra is
FAO-56 extraterrestrial radiation calculated from latitude and DOY.

Only May-Sep high-DTR days (DTR>=14.8 C) are used. The formal breakpoint used for
subsequent model development must come from 2000-2016 calibration data. 2017-2024
is evaluated only as an out-of-sample stability diagnostic.

For each response, fit continuous segmented regression:
 y = b0 + b1*Kt + b2*max(0,Kt-c)
Search c in 0.30..0.80 step 0.005, requiring at least 20 days on each side.
"""
from __future__ import annotations
import csv,math
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'processed_51463'
INFILE=DATA/'main51463_dtr_srad_daily.csv'
OUT=DATA/'kt_breakpoint_results.csv'
README=DATA/'README_KT_BREAKPOINT.md'
LAT=43.7833;DTRC=14.8

def ra(doy):
    phi=math.radians(LAT);dr=1+0.033*math.cos(2*math.pi*doy/365)
    de=0.409*math.sin(2*math.pi*doy/365-1.39)
    arg=max(-1,min(1,-math.tan(phi)*math.tan(de)));ws=math.acos(arg)
    return (24*60/math.pi)*0.0820*dr*(ws*math.sin(phi)*math.sin(de)+math.cos(phi)*math.cos(de)*math.sin(ws))

def solve3(a,b):
    m=[list(a[i])+[b[i]] for i in range(3)]
    for col in range(3):
        p=max(range(col,3),key=lambda r:abs(m[r][col]))
        if abs(m[p][col])<1e-12:return None
        m[col],m[p]=m[p],m[col];z=m[col][col]
        for j in range(col,4):m[col][j]/=z
        for r in range(3):
            if r==col:continue
            z=m[r][col]
            for j in range(col,4):m[r][j]-=z*m[col][j]
    return [m[i][3] for i in range(3)]

def fit_hinge(rows,response,c):
    vals=[(r['kt'],r[response]) for r in rows if math.isfinite(r[response])]
    lo=sum(x<=c for x,_ in vals);hi=len(vals)-lo
    if min(lo,hi)<20:return None
    xs=[(1.0,x,max(0.0,x-c)) for x,_ in vals];ys=[y for _,y in vals]
    a=[[sum(z[i]*z[j] for z in xs) for j in range(3)] for i in range(3)]
    b=[sum(z[i]*y for z,y in zip(xs,ys)) for i in range(3)]
    beta=solve3(a,b)
    if beta is None:return None
    sse=sum((y-sum(beta[i]*z[i] for i in range(3)))**2 for z,y in zip(xs,ys))
    return {'breakpoint_kt':c,'n':len(vals),'n_low':lo,'n_high':hi,'b0':beta[0],'slope_low':beta[1],'slope_change':beta[2],'slope_high':beta[1]+beta[2],'sse':sse}

def fit_linear(rows,response):
    vals=[(r['kt'],r[response]) for r in rows if math.isfinite(r[response])];n=len(vals)
    mx=sum(x for x,_ in vals)/n;my=sum(y for _,y in vals)/n;den=sum((x-mx)**2 for x,_ in vals)
    b1=sum((x-mx)*(y-my) for x,y in vals)/den;b0=my-b1*mx;sse=sum((y-(b0+b1*x))**2 for x,y in vals)
    return n,b0,b1,sse

def search(rows,response):
    best=None
    for i in range(101):
        c=0.30+i*0.005;r=fit_hinge(rows,response,c)
        if r and (best is None or r['sse']<best['sse']):best=r
    if best is None:return None
    n,b0,b1,sse=fit_linear(rows,response);best['linear_sse']=sse;best['sse_reduction_pct']=100*(sse-best['sse'])/sse
    best['delta_aic']=n*math.log(best['sse']/n)+2*4-(n*math.log(sse/n)+2*2)
    # linear zero crossing as an additional physical diagnostic, not the selected breakpoint.
    best['linear_zero_crossing_kt']=(-b0/b1 if abs(b1)>1e-12 else float('nan'))
    return best

def main():
    rows=[]
    with INFILE.open('r',newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            d=datetime.strptime(r['date'],'%Y-%m-%d').date();dtr=float(r['dtr'])
            if dtr<DTRC:continue
            rr={'date':d,'year':int(r['year']),'dtr':dtr,'kt':float(r['srad'])/ra(d.timetuple().tm_yday),
                'daily_rmse':float(r['daily_rmse']),'afternoon_rmse':float(r['afternoon_rmse']),'afternoon_bias':float(r['afternoon_bias'])}
            rows.append(rr)
    subsets=[('CAL_2000_2016',[r for r in rows if r['year']<=2016]),('VAL_2017_2024',[r for r in rows if r['year']>=2017]),('ALL_2000_2024',rows)]
    responses=['daily_rmse','afternoon_rmse','afternoon_bias'];out=[]
    for response in responses:
        for name,rs in subsets:
            res=search(rs,response)
            if not res:continue
            rec={'response':response,'subset':name};rec.update(res);out.append(rec)
    fields=list(out[0].keys())
    with OUT.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
    mp={(r['response'],r['subset']):r for r in out}
    cal_bias=mp[('afternoon_bias','CAL_2000_2016')];cal_rmse=mp[('daily_rmse','CAL_2000_2016')];cal_armse=mp[('afternoon_rmse','CAL_2000_2016')]
    val_bias=mp.get(('afternoon_bias','VAL_2017_2024'));val_rmse=mp.get(('daily_rmse','VAL_2017_2024'))
    text=f'''# Main 51463 high-DTR Kt breakpoint diagnosis\n\nOnly DTR >= {DTRC:.1f} C May-Sep days are used. The formal Kt threshold must come from 2000-2016 calibration only.\n\n## Calibration-only breakpoints\n\n| Response | Kt breakpoint | slope below | slope above | SSE reduction vs linear | Delta AIC | linear zero crossing |\n|---|---:|---:|---:|---:|---:|---:|\n| Daily RMSE | {cal_rmse['breakpoint_kt']:.3f} | {cal_rmse['slope_low']:.3f} | {cal_rmse['slope_high']:.3f} | {cal_rmse['sse_reduction_pct']:.2f}% | {cal_rmse['delta_aic']:.2f} | {cal_rmse['linear_zero_crossing_kt']:.3f} |\n| Afternoon RMSE | {cal_armse['breakpoint_kt']:.3f} | {cal_armse['slope_low']:.3f} | {cal_armse['slope_high']:.3f} | {cal_armse['sse_reduction_pct']:.2f}% | {cal_armse['delta_aic']:.2f} | {cal_armse['linear_zero_crossing_kt']:.3f} |\n| Afternoon Bias | {cal_bias['breakpoint_kt']:.3f} | {cal_bias['slope_low']:.3f} | {cal_bias['slope_high']:.3f} | {cal_bias['sse_reduction_pct']:.2f}% | {cal_bias['delta_aic']:.2f} | {cal_bias['linear_zero_crossing_kt']:.3f} |\n\n## Validation-only stability diagnostic\n\n- Afternoon-bias breakpoint: **{val_bias['breakpoint_kt']:.3f}** Kt\n- Daily-RMSE breakpoint: **{val_rmse['breakpoint_kt']:.3f}** Kt\n\nThe validation breakpoints are reported only to assess temporal stability; they are not allowed to set the model trigger.\n'''
    README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
