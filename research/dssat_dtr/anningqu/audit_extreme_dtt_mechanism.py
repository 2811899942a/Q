#!/usr/bin/env python3
"""Pure-Python audit of official CERES extreme DTT vs HMET and frozen M15 TGRO.

Equations are direct translations of DSSAT v4.8.5.0 DAYLEN, SOLAR, HTEMP and
CERES-Maize MZ_PHENOL extreme-day integration. This is a mechanism audit only:
it does not replace the real DSSAT four-arm run.
"""
from pathlib import Path
from datetime import date,timedelta
import csv,math

PI=3.14159; RAD=PI/180.0
LAT=43.950; TBASE=8.0; DOPT=34.0; DTRC=14.8; ALPHA=7.8094
A=2.0; B=2.2; C=1.0
SOW=[('Apr21',4,21,9,4),('Apr26',4,26,9,7),('May06',5,6,9,15),('May16',5,16,9,27),('May26',5,26,10,13)]

def daylen(doy):
    dec=-23.45*math.cos(2.0*PI*(doy+10.0)/365.0)
    soc=math.tan(RAD*dec)*math.tan(RAD*LAT); soc=min(max(soc,-1.0),1.0)
    dl=12.0+24.0*math.asin(soc)/PI; dl=min(max(dl,0.0),24.0)
    return dl,dec,12.0-dl/2.0,12.0+dl/2.0

def clouds(srad,dl,dec):
    ssin=math.sin(RAD*dec)*math.sin(RAD*LAT)
    ccos=math.cos(RAD*dec)*math.cos(RAD*LAT)
    soc=ssin/ccos; soc=min(max(soc,-1.0),1.0)
    dsinb=3600.0*(dl*ssin+24.0/PI*ccos*math.sqrt(max(0.0,1.0-soc**2)))
    s0d=1368.0*dsinb
    sclear=0.77*s0d*1e-6
    return min(max(1.0-srad/sclear,0.0),1.0) if sclear>0 else 0.0

def htemp(tmax,tmin,dl,snup,sndn):
    out=[]; tminhr=snup+C; tmaxhr=tminhr+dl/2.0+A
    t=0.5*PI*(sndn-tminhr)/(tmaxhr-tminhr)
    ts=tmin+(tmax-tmin)*math.sin(t)
    eb=math.exp(-B); tmini=(tmin-ts*eb)/(1.0-eb); hdecay=24.0+C-dl
    for h in range(1,25):
        hs=float(h)
        if hs>=snup+C and hs<=sndn:
            t=0.5*PI*(hs-tminhr)/(tmaxhr-tminhr)
            th=tmin+(tmax-tmin)*math.sin(t)
        else:
            if hs<snup+C: t=24.0+hs-sndn
            else: t=hs-sndn
            th=tmini+(ts-tmini)*math.exp(-B*t/hdecay)
        out.append(th)
    return out

def m15(base,tmax,tmin,dl,snup,sndn,cld):
    out=list(base); dtr=tmax-tmin
    if dtr<=DTRC or cld<=0: return out
    tminhr=snup+C; tmaxhr=tminhr+dl/2.0+A
    t=0.5*PI*(sndn-tminhr)/(tmaxhr-tminhr)
    ts0=tmin+(tmax-tmin)*math.sin(t)
    ts1=max(tmin,ts0-ALPHA*(dtr-DTRC)*cld)
    eb=math.exp(-B); tmini1=(tmin-ts1*eb)/(1.0-eb); hdecay=24.0+C-dl
    for idx,h in enumerate(range(1,25)):
        hs=float(h); th=base[idx]
        if hs>tmaxhr and hs<=sndn:
            den=tmax-ts0
            if abs(den)>1e-6:
                r=(tmax-th)/den; r=min(max(r,0.0),1.0)
                out[idx]=tmax-(tmax-ts1)*r
        elif hs>sndn or hs<tminhr:
            tt=24.0+hs-sndn if hs<tminhr else hs-sndn
            out[idx]=tmini1+(ts1-tmini1)*math.exp(-B*tt/hdecay)
    return out

def dtt_sine(tmax,tmin):
    vals=[]
    for i in range(1,25):
        th=(tmax+tmin)/2.0+(tmax-tmin)/2.0*math.sin(3.14/12.0*i)
        th=min(max(th,TBASE),DOPT); vals.append(th-TBASE)
    return sum(vals)/24.0

def dtt_hourly(xs):
    return sum(min(max(x,TBASE),DOPT)-TBASE for x in xs)/24.0

def read_wth(path,year):
    z={}
    for line in Path(path).read_text().splitlines():
        s=line.strip()
        if not s or s[0] in '*!@': continue
        p=s.split()
        if len(p)<5 or not p[0].isdigit(): continue
        code=p[0]; yy=2000+int(code[:2]); doy=int(code[2:])
        if yy!=year: continue
        d=date(year,1,1)+timedelta(days=doy-1)
        z[d]=(float(p[1]),float(p[2]),float(p[3]))
    return z

rows=[]
for year in (2021,2022):
    w=read_wth(f'research/dssat_dtr/data/anningqu/formal_ghcn_rain/ANQH{year%100:02d}01.WTH',year)
    for d,(srad,tmax,tmin) in sorted(w.items()):
        if not (tmin<TBASE or tmax>DOPT): continue
        doy=d.timetuple().tm_yday; dl,dec,snup,sndn=daylen(doy); cld=clouds(srad,dl,dec)
        h0=htemp(tmax,tmin,dl,snup,sndn); hm=m15(h0,tmax,tmin,dl,snup,sndn,cld)
        ds=dtt_sine(tmax,tmin); dh=dtt_hourly(h0); dm=dtt_hourly(hm)
        rows.append(dict(date=d.isoformat(),year=year,doy=doy,srad=srad,tmax=tmax,tmin=tmin,dtr=tmax-tmin,clouds=cld,
                         m15_active=int((tmax-tmin)>DTRC and cld>0),dtt_sine=ds,dtt_h0tt=dh,dtt_m15tt=dm,
                         generic_delta=dh-ds,local_delta=dm-dh,total_delta=dm-ds))

out=Path('research/dssat_dtr/data/anningqu/extreme_dtt_mechanism'); out.mkdir(parents=True,exist_ok=True)
with (out/'daily_extreme_dtt_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
    wr=csv.DictWriter(f,fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)

md=['# Anningqu extreme-day DTT mechanism audit','',
    'Direct equation translation of DSSAT v4.8.5 DAYLEN/SOLAR/HTEMP and CERES-Maize extreme-day DTT. Thresholds TBASE=8 C, DOPT=34 C; frozen M15 DTRc=14.8 C, alpha=7.8094.','',
    '|Year|Sowing|Extreme days|M15-active extreme days|Sum DTT sine|Sum DTT H0TT|Sum DTT M15TT|Generic ΔDTT|Local ΔDTT|Total ΔDTT|',
    '|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for year in (2021,2022):
    for name,sm,sd,hm,hd in SOW:
        a=date(year,sm,sd); b=date(year,hm,hd); rr=[r for r in rows if r['year']==year and a<=date.fromisoformat(r['date'])<=b]
        s=lambda k:sum(float(r[k]) for r in rr)
        md.append(f"|{year}|{name}|{len(rr)}|{sum(r['m15_active'] for r in rr)}|{s('dtt_sine'):.2f}|{s('dtt_h0tt'):.2f}|{s('dtt_m15tt'):.2f}|{s('generic_delta'):+.2f}|{s('local_delta'):+.2f}|{s('total_delta'):+.2f}|")
active=[r for r in rows if r['m15_active']]
md += ['',f'- Extreme days audited: **{len(rows)}** across full 2021-2022 calendar.',f'- M15-active extreme days: **{len(active)}**.',
       f"- Mean generic ΔDTT on all extreme days: **{sum(r['generic_delta'] for r in rows)/len(rows):+.3f} C d/day**.",
       f"- Mean local M15 ΔDTT on M15-active extreme days: **{sum(r['local_delta'] for r in active)/len(active):+.3f} C d/day**." if active else '- No M15-active extreme days.',
       '', 'Largest absolute local M15 DTT effects:','',
       '|Date|Tmax|Tmin|DTR|Clouds|Generic ΔDTT|Local ΔDTT|Total ΔDTT|','|:---|---:|---:|---:|---:|---:|---:|---:|']
for r in sorted(active,key=lambda x:abs(x['local_delta']),reverse=True)[:12]:
    md.append(f"|{r['date']}|{r['tmax']:.1f}|{r['tmin']:.1f}|{r['dtr']:.1f}|{r['clouds']:.3f}|{r['generic_delta']:+.3f}|{r['local_delta']:+.3f}|{r['total_delta']:+.3f}|")
(out/'README_EXTREME_DTT_MECHANISM.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print('\n'.join(md))
