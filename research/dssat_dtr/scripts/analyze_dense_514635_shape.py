#!/usr/bin/env python3
"""Dense-hourly validation of Urumqi DTR mechanism using NOAA 51463599999 (Diwopu).

This second Urumqi station has near-hourly METAR observations. It is used as an
independent mechanism dataset to test whether the 51463 findings generalize:
1) Does observed Tmax timing shift with DTR?
2) Does normalized cooling in the first 1-3 h after Tmax strengthen with DTR?
3) Does original DSSAT HTEMP error show a breakpoint near 14.5 C?

No parameters are imported from validation outcomes into the primary-station fit.
"""
import csv,io,math,statistics,urllib.request
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path
ST='51463599999';LAT=43.907106;LON=87.474244;TZ=8;STD=120.0;PI=3.14159;RAD=PI/180
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data'/'processed_514635';OUT.mkdir(parents=True,exist_ok=True)
BAD={'2','3','6','7'}
def parse_tmp(s):
    if not s:return None,''
    p=s.split(',');x=p[0];q=p[1] if len(p)>1 else ''
    if x in {'+9999','-9999','9999',''}:return None,q
    try:return int(x)/10,q
    except:return None,q
def eot(doy):
    b=math.radians((360/365)*(doy-81));return 9.87*math.sin(2*b)-7.53*math.cos(b)-1.5*math.sin(b)
def solar(dt_cst):
    return dt_cst+timedelta(minutes=4*(LON-STD)+eot(dt_cst.timetuple().tm_yday))
def daylen(doy):
    dec=-23.45*math.cos(2*PI*(doy+10)/365);soc=math.tan(RAD*dec)*math.tan(RAD*LAT);soc=max(-1,min(1,soc));dl=12+24*math.asin(soc)/PI;return dl,12-dl/2,12+dl/2
def htemp(hs,tmax,tmin,dayl,snup,sndn,A=2,B=2.2,C=1):
    tmin_time=snup+C;tmax_time=tmin_time+dayl/2+A;t=.5*PI*(sndn-tmin_time)/(tmax_time-tmin_time);ts=tmin+(tmax-tmin)*math.sin(t);eb=math.exp(-B);tmini=(tmin-ts*eb)/(1-eb);hdecay=24+C-dayl
    if hs>=snup+C and hs<=sndn:
        t=.5*PI*(hs-tmin_time)/(tmax_time-tmin_time);return tmin+(tmax-tmin)*math.sin(t)
    tt=(24+hs-sndn) if hs<snup+C else (hs-sndn);return tmini+(ts-tmini)*math.exp(-B*tt/hdecay)
def mean(x):return statistics.mean(x) if x else float('nan')
def median(x):return statistics.median(x) if x else float('nan')
def rmse(x):return math.sqrt(mean([z*z for z in x])) if x else float('nan')
def dbin(d):
    if d<10:return '<10'
    if d<14.5:return '10-<14.5'
    if d<18:return '14.5-<18'
    if d<20:return '18-<20'
    return '>=20'
def main():
    rec=[]
    for y in range(2000,2025):
        url=f'https://www.ncei.noaa.gov/data/global-hourly/access/{y}/{ST}.csv';req=urllib.request.Request(url,headers={'User-Agent':'DSSAT-DTR-research/1.0'})
        with urllib.request.urlopen(req,timeout=60) as rr:text=rr.read().decode('utf-8-sig',errors='replace')
        for r in csv.DictReader(io.StringIO(text)):
            t,q=parse_tmp(r.get('TMP',''))
            if t is None or q in BAD:continue
            try:d=datetime.fromisoformat(r['DATE'].replace('Z',''))
            except:continue
            cst=d+timedelta(hours=8);sol=solar(cst);slot=sol.replace(minute=0,second=0,microsecond=0)
            rec.append({'sol':sol,'slot':slot,'temp':t,'report':r.get('REPORT_TYPE','')})
    # one observation per solar-hour slot, closest to the exact hour
    g=defaultdict(list)
    for r in rec:g[r['slot']].append(r)
    hourly=[]
    for s,rs in g.items():hourly.append(min(rs,key=lambda r:abs((r['sol']-s).total_seconds())))
    byday=defaultdict(list)
    for r in hourly:byday[r['sol'].date()].append(r)
    days=[];points=[]
    for date,rs in sorted(byday.items()):
        rs=sorted(rs,key=lambda r:r['sol']);hours={r['sol'].hour for r in rs}
        if len(hours)<20:continue
        temps=[r['temp'] for r in rs];tmax=max(temps);tmin=min(temps);dtr=tmax-tmin
        # use median time of tied hourly Tmax values
        peaks=[r for r in rs if abs(r['temp']-tmax)<1e-9];ph=median([r['sol'].hour+r['sol'].minute/60 for r in peaks])
        doy=date.timetuple().tm_yday;dl,su,sd=daylen(doy)
        errs=[]
        for r in rs:
            hs=r['sol'].hour+r['sol'].minute/60+r['sol'].second/3600;pred=htemp(hs,tmax,tmin,dl,su,sd);err=pred-r['temp'];errs.append(err);points.append({'date':date.isoformat(),'year':date.year,'month':date.month,'dtr':dtr,'dtr_bin':dbin(dtr),'solar_hour':hs,'obs':r['temp'],'pred':pred,'error':err})
        # observed drops at approximately +1,+2,+3 h from selected observed peak checkpoint
        peakr=min(rs,key=lambda r:abs((r['sol'].hour+r['sol'].minute/60)-ph))
        pdt=peakr['sol'];drops={}
        for lag in [1,2,3]:
            target=pdt+timedelta(hours=lag);cand=min(rs,key=lambda r:abs((r['sol']-target).total_seconds()))
            if abs((cand['sol']-target).total_seconds())<=2700:
                drops[lag]=tmax-cand['temp']
            else:drops[lag]=None
        days.append({'date':date.isoformat(),'year':date.year,'month':date.month,'n_hours':len(hours),'tmax_c':tmax,'tmin_c':tmin,'dtr_c':dtr,'dtr_bin':dbin(dtr),'observed_tmax_solar_h':ph,'tmax_minus_1h_c':drops[1] if drops[1] is not None else '','tmax_minus_2h_c':drops[2] if drops[2] is not None else '','tmax_minus_3h_c':drops[3] if drops[3] is not None else '','norm_drop_1h':drops[1]/dtr if drops[1] is not None and dtr>0 else '','norm_drop_2h':drops[2]/dtr if drops[2] is not None and dtr>0 else '','norm_drop_3h':drops[3]/dtr if drops[3] is not None and dtr>0 else '','htemp_daily_rmse':rmse(errs),'htemp_daily_bias':mean(errs)})
    # summaries May-Sep, full / calibration / validation
    sums=[]
    for split,subset in [('All',[r for r in days if 5<=r['month']<=9]),('Calibration',[r for r in days if 5<=r['month']<=9 and r['year']<=2016]),('Validation',[r for r in days if 5<=r['month']<=9 and r['year']>=2017])]:
        for b in ['<10','10-<14.5','14.5-<18','18-<20','>=20']:
            s=[r for r in subset if r['dtr_bin']==b]
            if not s:continue
            row={'split':split,'dtr_bin':b,'n_days':len(s),'mean_dtr':round(mean([r['dtr_c'] for r in s]),3),'median_tmax_solar_h':round(median([r['observed_tmax_solar_h'] for r in s]),3),'mean_htemp_rmse':round(mean([r['htemp_daily_rmse'] for r in s]),4),'mean_htemp_bias':round(mean([r['htemp_daily_bias'] for r in s]),4)}
            for lag in [1,2,3]:
                v=[float(r[f'norm_drop_{lag}h']) for r in s if r[f'norm_drop_{lag}h']!=''];row[f'median_norm_drop_{lag}h']=round(median(v),4) if v else ''
            sums.append(row)
    # breakpoint search daily RMSE in May-Sep (same continuous hinge model, simple OLS 3x3)
    def solve3(A,b):
        m=[list(A[i])+[b[i]] for i in range(3)]
        for c in range(3):
            p=max(range(c,3),key=lambda r:abs(m[r][c]));m[c],m[p]=m[p],m[c];z=m[c][c]
            if abs(z)<1e-12:return None
            for j in range(c,4):m[c][j]/=z
            for rr in range(3):
                if rr==c:continue
                f=m[rr][c]
                for j in range(c,4):m[rr][j]-=f*m[c][j]
        return [m[i][3] for i in range(3)]
    def bp(sub):
        vals=[(r['dtr_c'],r['htemp_daily_rmse']) for r in sub];best=None
        for i in range(81):
            c=10+i*.1
            if sum(x<=c for x,y in vals)<100 or sum(x>c for x,y in vals)<100:continue
            X=[(1,x,max(0,x-c)) for x,y in vals];A=[[sum(xx[i]*xx[j] for xx in X) for j in range(3)] for i in range(3)];b=[sum(xx[i]*y for xx,(x,y) in zip(X,vals)) for i in range(3)];be=solve3(A,b)
            if not be:continue
            sse=sum((y-sum(be[j]*xx[j] for j in range(3)))**2 for xx,(x,y) in zip(X,vals))
            if best is None or sse<best[0]:best=(sse,c,be)
        return best
    may=[r for r in days if 5<=r['month']<=9];cal=[r for r in may if r['year']<=2016];val=[r for r in may if r['year']>=2017];ba=bp(may);bc=bp(cal);bv=bp(val)
    def write(p,rows):
        with p.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    write(OUT/'dense_daily_shape.csv',days);write(OUT/'dense_shape_by_dtr.csv',sums)
    txt=f'''# Dense-hourly Urumqi mechanism validation — Diwopu 51463599999

- >=20-hour solar days used: **{len(days):,}**.
- May-Sep days: **{len(may):,}**.
- Independent mechanism station: Diwopu (43.907106 N, 87.474244 E, 647.7 m).

## HTEMP RMSE breakpoint from dense daily curves
- All 2000-2024: **{ba[1]:.1f} C**.
- Calibration-era 2000-2016: **{bc[1]:.1f} C**.
- Validation-era 2017-2024: **{bv[1]:.1f} C**.

## May-Sep DTR groups
| Split | DTR | N days | Median observed Tmax solar hour | Median normalized drop +1h | +2h | +3h | Mean official HTEMP RMSE |
|---|---|---:|---:|---:|---:|---:|---:|
'''
    for r in sums:
        if r['split'] in {'All','Validation'}:txt+=f"| {r['split']} | {r['dtr_bin']} | {r['n_days']} | {r['median_tmax_solar_h']:.3f} | {r['median_norm_drop_1h']} | {r['median_norm_drop_2h']} | {r['median_norm_drop_3h']} | {r['mean_htemp_rmse']:.3f} |\n"
    txt+='''\nInterpretation: an earlier observed Tmax with rising DTR would support a timing component; larger normalized 1-3 h drops would support faster post-peak cooling. Reproduction of a ~14-15 C RMSE breakpoint at this dense second Urumqi station would be strong spatial/observational validation of the primary-station mechanism.\n'''
    (OUT/'README_DENSE_SHAPE.md').write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
