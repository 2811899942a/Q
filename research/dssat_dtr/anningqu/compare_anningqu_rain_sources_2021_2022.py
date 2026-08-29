#!/usr/bin/env python3
"""Compare public precipitation sources for the Anningqu 2021-2022 DSSAT build.

Inputs already generated:
- `anningqu_wth_daily_2021_2022.csv` contains NASA POWER PRECTOTCORR.

Independent observed comparison:
- NOAA GHCN-Daily CHM00051463 PRCP (quality-flag-clean records only).

The script reports annual, May-Oct, and Tang et al. five sowing-to-expected-harvest
windows for each year. It does not silently choose or scale a rainfall source.
"""
from __future__ import annotations
import csv,gzip,io,urllib.request
from datetime import datetime,date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data'/'anningqu';DAILY=OUT/'anningqu_wth_daily_2021_2022.csv';CSVOUT=OUT/'anningqu_rain_source_comparison.csv';README=OUT/'README_ANINGQU_RAIN_SOURCES.md'
GHCN='CHM00051463'
WINDOWS={
 'A':((4,21),(9,4)),
 'B':((4,26),(9,7)),
 'C':((5,6),(9,15)),
 'D':((5,16),(9,27)),
 'E':((5,26),(10,13)),
}

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'DSSAT-Urumqi-public-reconstruction/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:return r.read()
def load_power():
 out={}
 with DAILY.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):out[datetime.strptime(r['date'],'%Y-%m-%d').date()]=float(r['rain_mm'])
 return out
def load_ghcn():
 url=f'https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/{GHCN}.csv.gz';raw=gzip.decompress(get(url)).decode('utf-8',errors='replace');out={}
 for row in csv.reader(io.StringIO(raw)):
  if len(row)<6 or row[2]!='PRCP':continue
  qflag=row[5].strip()
  if qflag:continue
  try:d=datetime.strptime(row[1],'%Y%m%d').date();v=float(row[3])/10.0
  except:continue
  if v>=0:out[d]=v
 return out,url
def days(y,sm,sd,em,ed):
 s=date(y,sm,sd);e=date(y,em,ed);return [d for d in sorted(set(list_power)|set(list_ghcn)) if s<=d<=e]
def summarize(y,label,sm,sd,em,ed,power,ghcn):
 ds=[];d=date(y,sm,sd);end=date(y,em,ed)
 from datetime import timedelta
 while d<=end:ds.append(d);d+=timedelta(days=1)
 pg=[power[d] for d in ds if d in power];gg=[ghcn[d] for d in ds if d in ghcn]
 return {'year':y,'window':label,'start':date(y,sm,sd).isoformat(),'end':date(y,em,ed).isoformat(),'n_days':len(ds),'power_days':len(pg),'ghcn_days':len(gg),'power_rain_mm':round(sum(pg),2),'ghcn_rain_mm':round(sum(gg),2) if gg else '','ghcn_coverage_pct':round(100*len(gg)/len(ds),2)}
def main():
 global list_power,list_ghcn
 power=load_power();ghcn,url=load_ghcn();list_power=power;list_ghcn=ghcn
 rows=[]
 for y in [2021,2022]:
  rows.append(summarize(y,'FULL_YEAR',1,1,12,31,power,ghcn));rows.append(summarize(y,'MAY_OCT',5,1,10,31,power,ghcn))
  for lab,(s,e) in WINDOWS.items():rows.append(summarize(y,'TANG_'+lab,s[0],s[1],e[0],e[1],power,ghcn))
 with CSVOUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
 r22=next(r for r in rows if r['year']==2022 and r['window']=='MAY_OCT')
 vals22=[r for r in rows if r['year']==2022 and r['window'].startswith('TANG_')]
 text=f'''# Anningqu 2021-2022 precipitation-source comparison\n\nTwo independent public sources are compared without rescaling:\n- NASA POWER `PRECTOTCORR` at 87.49 E, 43.95 N, LST;\n- NOAA GHCN-Daily `{GHCN}` `PRCP`, clean records only.\n\nThe nearby Anningqu 2022 DSSAT peanut study reports **63.1 mm** total growing-season rainfall. Its exact crop-season window differs from the fixed May-Oct comparison below, so this number is an external magnitude check rather than a fitting target.\n\n## 2022 May-Oct\n- POWER: **{r22['power_rain_mm']} mm**\n- GHCN: **{r22['ghcn_rain_mm']} mm**, coverage **{r22['ghcn_coverage_pct']}%**\n\n## 2022 Tang maize windows\n| Sowing window | POWER rain | GHCN rain | GHCN coverage |\n|---|---:|---:|---:|\n'''
 for r in vals22:text+=f"| {r['window']} ({r['start'][5:]} to {r['end'][5:]}) | {r['power_rain_mm']} | {r['ghcn_rain_mm']} | {r['ghcn_coverage_pct']}% |\n"
 text+=f'''\nGHCN download used: `{url}`.\n\nDecision rule: prefer GHCN for formal WTH rainfall only if daily coverage is essentially complete and values are internally plausible. If observed-station and gridded precipitation materially disagree, retain both as a rainfall sensitivity pair; do not force either source to match 63.1 mm. The first M0-vs-M15 crop propagation experiment remains the fully irrigated treatment, reducing sensitivity to this rainfall choice.\n''';README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
