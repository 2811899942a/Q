#!/usr/bin/env python3
"""Hourly/DTR residual diagnosis at dense Urumqi Diwopu station 51463599999.

Uses >=20-observation solar days. Daily Tmax/Tmin are derived from the dense hourly
observations, then original DSSAT HTEMP is evaluated at every real observation time.
Outputs DTR-bin x solar-hour residual patterns and Tmax timing statistics to identify
which mechanism transfers across the two Urumqi stations.
"""
import csv,io,math,statistics,urllib.request
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path
import analyze_dense_514635_shape as ds
OUT=Path(__file__).resolve().parents[1]/'data'/'processed_514635';ST='51463599999'
def mean(x):return statistics.mean(x) if x else float('nan')
def median(x):return statistics.median(x) if x else float('nan')
def pearson(x,y):
    if len(x)<3:return float('nan')
    mx,my=mean(x),mean(y);sx=sum((a-mx)**2 for a in x);sy=sum((b-my)**2 for b in y)
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(sx*sy) if sx>0 and sy>0 else float('nan')
def main():
    rec=[]
    for y in range(2000,2025):
        url=f'https://www.ncei.noaa.gov/data/global-hourly/access/{y}/{ST}.csv';req=urllib.request.Request(url,headers={'User-Agent':'DSSAT-DTR-research/1.0'})
        with urllib.request.urlopen(req,timeout=60) as rr:text=rr.read().decode('utf-8-sig',errors='replace')
        for r in csv.DictReader(io.StringIO(text)):
            t,q=ds.parse_tmp(r.get('TMP',''))
            if t is None or q in ds.BAD:continue
            try:d=datetime.fromisoformat(r['DATE'].replace('Z',''))
            except:continue
            sol=ds.solar(d+timedelta(hours=8));slot=sol.replace(minute=0,second=0,microsecond=0);rec.append({'sol':sol,'slot':slot,'temp':t})
    gg=defaultdict(list)
    for r in rec:gg[r['slot']].append(r)
    hourly=[min(rs,key=lambda r:abs((r['sol']-slot).total_seconds())) for slot,rs in gg.items()]
    bd=defaultdict(list)
    for r in hourly:bd[r['sol'].date()].append(r)
    points=[];daystats=[]
    for date,rs in sorted(bd.items()):
        hrs={r['sol'].hour for r in rs}
        if len(hrs)<20:continue
        rs=sorted(rs,key=lambda r:r['sol']);ts=[r['temp'] for r in rs];tmax=max(ts);tmin=min(ts);dtr=tmax-tmin;doy=date.timetuple().tm_yday;dl,su,sd=ds.daylen(doy);peaks=[r for r in rs if abs(r['temp']-tmax)<1e-9];ph=median([r['sol'].hour+r['sol'].minute/60 for r in peaks])
        for r in rs:
            hs=r['sol'].hour+r['sol'].minute/60+r['sol'].second/3600;pred=ds.htemp(hs,tmax,tmin,dl,su,sd);points.append({'date':date.isoformat(),'year':date.year,'month':date.month,'dtr':dtr,'dtr_bin':ds.dbin(dtr),'solar_hour':hs,'hour_bin':int(hs)%24,'obs':r['temp'],'pred':pred,'error':pred-r['temp'],'tmax_hour':ph})
        daystats.append({'date':date.isoformat(),'year':date.year,'month':date.month,'dtr':dtr,'dtr_bin':ds.dbin(dtr),'tmax_hour':ph})
    sums=[]
    for split,pbase in [('All',points),('Calibration',[r for r in points if r['year']<=2016]),('Validation',[r for r in points if r['year']>=2017])]:
        pbase=[r for r in pbase if 5<=r['month']<=9]
        for b in ['<10','10-<14.5','14.5-<18','18-<20','>=20']:
            for h in range(24):
                s=[r for r in pbase if r['dtr_bin']==b and r['hour_bin']==h]
                if not s:continue
                e=[r['error'] for r in s]
                sums.append({'split':split,'dtr_bin':b,'solar_hour_bin':h,'n_points':len(s),'rmse':round(math.sqrt(mean([x*x for x in e])),4),'mae':round(mean([abs(x) for x in e]),4),'bias':round(mean(e),4)})
    with (OUT/'dense_residual_by_hour_dtr.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(sums[0].keys()));w.writeheader();w.writerows(sums)
    # Tmax timing relationship by split and DTR group
    timing=[]
    for split,d in [('All',daystats),('Calibration',[r for r in daystats if r['year']<=2016]),('Validation',[r for r in daystats if r['year']>=2017])]:
        d=[r for r in d if 5<=r['month']<=9]
        timing.append({'split':split,'n_days':len(d),'pearson_dtr_vs_tmax_hour':round(pearson([r['dtr'] for r in d],[r['tmax_hour'] for r in d]),4),'median_tmax_hour_dtr_lt14.5':round(median([r['tmax_hour'] for r in d if r['dtr']<14.5]),3),'median_tmax_hour_dtr_ge14.5':round(median([r['tmax_hour'] for r in d if r['dtr']>=14.5]),3),'n_dtr_ge14.5':sum(r['dtr']>=14.5 for r in d)})
    with (OUT/'dense_tmax_timing.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(timing[0].keys()));w.writeheader();w.writerows(timing)
    # compact validation table for main hours with data
    val=[r for r in sums if r['split']=='Validation'];main=[r for r in val if r['dtr_bin'] in {'10-<14.5','14.5-<18'} and r['solar_hour_bin'] in {12,13,14,15,16,17,18,19}]
    txt='# Dense Diwopu HTEMP residual mechanism by hour\n\n'
    for r in timing:txt+=f"- {r['split']}: DTR vs Tmax-hour r={r['pearson_dtr_vs_tmax_hour']}; median Tmax <14.5C DTR={r['median_tmax_hour_dtr_lt14.5']} h, >=14.5C={r['median_tmax_hour_dtr_ge14.5']} h (n high={r['n_dtr_ge14.5']}).\n"
    txt+='\n## Independent validation residuals around midday/afternoon\n\n| DTR | solar hour | N | RMSE | Bias |\n|---|---:|---:|---:|---:|\n'
    for r in main:txt+=f"| {r['dtr_bin']} | {r['solar_hour_bin']} | {r['n_points']} | {r['rmse']:.3f} | {r['bias']:.3f} |\n"
    txt+='\nCross-station mechanism claims should retain only patterns that persist here with dense real-hour observations.\n';(OUT/'README_DENSE_RESIDUAL_HOURS.md').write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
