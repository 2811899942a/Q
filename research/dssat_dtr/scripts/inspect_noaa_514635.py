#!/usr/bin/env python3
"""Inspect NOAA Global Hourly coverage of Urumqi-area station 51463599999.

Goal: determine whether this second known Urumqi station provides denser hourly/METAR
temperature observations that can resolve Tmax timing and early post-peak cooling.
No interpolation is performed.
"""
import csv,io,urllib.request,statistics
from collections import defaultdict,Counter
from datetime import datetime,timedelta
from pathlib import Path
ST='51463599999'; YEARS=range(2000,2025); ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data'/'processed_514635';OUT.mkdir(parents=True,exist_ok=True)
def parse_tmp(s):
    if not s:return None
    x=s.split(',')[0]
    if x in {'+9999','-9999','9999',''}:return None
    try:return int(x)/10
    except:return None
def dt(s):
    try:return datetime.fromisoformat(s.replace('Z',''))
    except:return None
def main():
    allr=[];manifest=[];meta={}
    for y in YEARS:
        url=f'https://www.ncei.noaa.gov/data/global-hourly/access/{y}/{ST}.csv'
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'DSSAT-DTR-research/1.0'})
            with urllib.request.urlopen(req,timeout=60) as rr:data=rr.read()
        except Exception as e:
            manifest.append({'year':y,'status':'MISSING','bytes':0,'error':str(e)});continue
        reader=csv.DictReader(io.StringIO(data.decode('utf-8-sig',errors='replace')));n=0
        for r in reader:
            t=parse_tmp(r.get('TMP',''));d=dt(r.get('DATE',''))
            if t is None or d is None:continue
            n+=1;local=d+timedelta(hours=8);meta={'name':r.get('NAME',''),'lat':r.get('LATITUDE',''),'lon':r.get('LONGITUDE',''),'elev':r.get('ELEVATION','')}
            allr.append({'year':y,'datetime_cst':local,'temp':t,'report':r.get('REPORT_TYPE',''),'qc':(r.get('TMP','').split(',')[1] if ',' in r.get('TMP','') else '')})
        manifest.append({'year':y,'status':'OK','bytes':len(data),'valid_temp':n,'error':''})
    # distinct local-hour slots per day
    day=defaultdict(set);reports=Counter()
    for r in allr:
        key=r['datetime_cst'].date();slot=r['datetime_cst'].replace(minute=0,second=0,microsecond=0);day[key].add(slot);reports[r['report']]+=1
    yearly=[]
    for y in YEARS:
        ds=[len(v) for d,v in day.items() if d.year==y]
        yearly.append({'year':y,'days_with_temp':len(ds),'median_distinct_hours':('' if not ds else statistics.median(ds)),'days_ge20h':sum(n>=20 for n in ds),'days_12_19h':sum(12<=n<20 for n in ds),'days_8_11h':sum(8<=n<12 for n in ds),'max_hours_day':max(ds) if ds else ''})
    def write(p,rows):
        with p.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    write(OUT/'source_manifest.csv',manifest);write(OUT/'yearly_coverage.csv',yearly)
    ok=[r for r in manifest if r['status']=='OK'];dense=sum(r['days_ge20h'] for r in yearly);d12=sum(r['days_12_19h'] for r in yearly);d8=sum(r['days_8_11h'] for r in yearly)
    txt=f'''# NOAA station {ST} Urumqi coverage inspection

- Metadata from available files: **{meta}**
- Available annual files 2000-2024: **{len(ok)}/25**.
- Valid temperature reports: **{len(allr):,}**.
- Days with >=20 distinct local-hour slots: **{dense:,}**.
- Days with 12-19 slots: **{d12:,}**.
- Days with 8-11 slots: **{d8:,}**.
- Report types: **{dict(reports)}**.

If this station has substantial >=20 h coverage in recent years and is spatially representative of Urumqi, it can be used to resolve true intraday peak timing/shape. Otherwise it remains secondary to 51463099999 + formal GHCN Tmax/Tmin.
''';(OUT/'README_COVERAGE.md').write_text(txt,encoding='utf-8');print(txt)
if __name__=='__main__':main()
