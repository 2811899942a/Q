#!/usr/bin/env python3
"""Create the formal Anningqu 2021-2022 WTH pair with observed GHCN rainfall.

The existing public reconstruction already fixes temperature and SRAD. This script
changes only RAIN using NOAA GHCN-Daily CHM00051463 PRCP when a clean record is
available; NASA POWER PRECTOTCORR is retained only as an explicit gap fallback.

The original POWER-rain daily series is preserved as a sensitivity dataset.
"""
from __future__ import annotations
import csv,gzip,io,shutil,urllib.request
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data'/'anningqu';DAILY=BASE/'anningqu_wth_daily_2021_2022.csv'
FORMAL=BASE/'formal_ghcn_rain';SENS=BASE/'sensitivity_power_rain';FORMAL.mkdir(parents=True,exist_ok=True);SENS.mkdir(parents=True,exist_ok=True)
GHCN='CHM00051463';INSI='ANQH';LAT=43.95;LON=87.49;ELEV=590

def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'DSSAT-Urumqi-public-reconstruction/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:return r.read()
def ghcn_prcp():
 url=f'https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/{GHCN}.csv.gz';raw=gzip.decompress(get(url)).decode('utf-8',errors='replace');out={}
 for row in csv.reader(io.StringIO(raw)):
  if len(row)<6 or row[2]!='PRCP' or row[5].strip():continue
  try:d=datetime.strptime(row[1],'%Y%m%d').date();v=float(row[3])/10.
  except:continue
  if v>=0:out[d]=v
 return out,url
def parse_header(path):
 lines=path.read_text(encoding='ascii').splitlines();station=next(x for x in lines if x.startswith('  ANQH'))
 vals=station.split();return float(vals[4]),float(vals[5])
def write_wth(path,year,rows,tav,amp):
 with path.open('w',encoding='ascii',newline='\n') as f:
  f.write('*WEATHER DATA : Anningqu,Urumqi,Xinjiang,China - formal public reconstruction\n\n')
  f.write('@ INSI      LAT     LONG  ELEV   TAV   AMP REFHT WNDHT\n')
  f.write(f'  {INSI:<4s}  {LAT:7.3f}  {LON:8.3f} {ELEV:5d} {tav:5.1f} {amp:5.1f}  2.00  3.00\n')
  f.write('@DATE  SRAD  TMAX  TMIN  RAIN\n');yy=str(year)[-2:]
  for r in rows:f.write(f"{yy}{int(r['doy']):03d} {float(r['srad_mj_m2_d']):5.1f} {float(r['tmax_c']):5.1f} {float(r['tmin_c']):5.1f} {float(r['formal_rain_mm']):5.1f}\n")
def main():
 rows=[]
 with DAILY.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):r['date_obj']=datetime.strptime(r['date'],'%Y-%m-%d').date();rows.append(r)
 prcp,url=ghcn_prcp();tav,amp=parse_header(BASE/'ANQH2101.WTH')
 # Archive existing POWER-rain standard files before formal observed-rain creation.
 for y in [2021,2022]:
  shutil.copy2(BASE/f'ANQH{str(y)[-2:]}01.WTH',SENS/f'ANQH{str(y)[-2:]}01.WTH')
 for r in rows:
  d=r['date_obj'];power=float(r['rain_mm'])
  if d in prcp:r['formal_rain_mm']=prcp[d];r['rain_source']='NOAA_GHCN_CHM00051463_PRCP'
  else:r['formal_rain_mm']=power;r['rain_source']='NASA_POWER_PRECTOTCORR_FALLBACK'
 for y in [2021,2022]:write_wth(FORMAL/f'ANQH{str(y)[-2:]}01.WTH',y,[r for r in rows if int(r['year'])==y],tav,amp)
 outcsv=FORMAL/'anningqu_formal_daily_2021_2022.csv';fields=['date','year','doy','srad_mj_m2_d','tmax_c','tmin_c','formal_rain_mm','temperature_source','dense_observed_hours','rain_source']
 with outcsv.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:r[k] for k in fields} for r in rows])
 counts={y:{'ghcn':0,'fallback':0,'rain':0.} for y in [2021,2022]}
 for r in rows:
  y=int(r['year']);counts[y]['rain']+=float(r['formal_rain_mm']);counts[y]['ghcn']+=r['rain_source'].startswith('NOAA');counts[y]['fallback']+=r['rain_source'].startswith('NASA')
 def win(y,sm,sd,em,ed):
  z=[r for r in rows if int(r['year'])==y and (sm,sd)<= (r['date_obj'].month,r['date_obj'].day)<= (em,ed)];return sum(float(r['formal_rain_mm']) for r in z)
 r22mo=win(2022,5,1,10,31)
 tang=[('A',4,21,9,4),('B',4,26,9,7),('C',5,6,9,15),('D',5,16,9,27),('E',5,26,10,13)]
 text=f'''# Formal Anningqu DSSAT weather rainfall selection\n\nFormal M0/M15 crop runs use GHCN-Daily `{GHCN}` precipitation wherever a clean daily PRCP record exists. NASA POWER rainfall is used only for missing GHCN days. SRAD remains NASA POWER; TMAX/TMIN remain the previously QC-controlled dense-station hierarchy.\n\nThe original all-POWER-rain WTH pair is preserved under `sensitivity_power_rain/`.\n\n## Rainfall coverage\n| Year | GHCN rain days | POWER fallback days | Annual formal rain |\n|---|---:|---:|---:|\n| 2021 | {counts[2021]['ghcn']} | {counts[2021]['fallback']} | {counts[2021]['rain']:.1f} mm |\n| 2022 | {counts[2022]['ghcn']} | {counts[2022]['fallback']} | {counts[2022]['rain']:.1f} mm |\n\n2022 May-Oct formal rainfall: **{r22mo:.1f} mm**. The nearby Anningqu DSSAT peanut paper reports about **63.1 mm** for its own 2022 growing season; this is an external magnitude check, not a rescaling target.\n\n## 2022 Tang sowing-to-expected-harvest windows\n'''
 for lab,sm,sd,em,ed in tang:text+=f'- {lab}: **{win(2022,sm,sd,em,ed):.1f} mm**\n'
 text+=f'''\nGHCN source: `{url}`.\n\nFormal comparison rule: M0 and M15 use byte-identical weather inputs. The POWER-rain pair is used only for rainfall-source sensitivity and is never used to tune M15.\n''';(FORMAL/'README_FORMAL_WTH.md').write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
