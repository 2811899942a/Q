from __future__ import annotations

import csv
import datetime as dt
import json
import urllib.request
from pathlib import Path

LAT = 44 + 19/60 + 28/3600
LON = 85 + 59/60 + 47/3600
YEARS = [2019, 2020]
OUT = Path('research/dssat_dtr/data/shihezi_real_case/power_daily')
OUT.mkdir(parents=True, exist_ok=True)
UA = 'Mozilla/5.0 DSSAT-Xinjiang-research/1.0'
PARAMS = 'T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN'

all_rows=[]
report=['# Shihezi Guo-2025 NASA POWER daily reconstruction','',
        f'Coordinate: {LAT:.6f} N, {LON:.6f} E; elevation in field thesis = 412 m.',
        'Source is NASA POWER point data. Guo (2025) explicitly states that meteorological inputs came from the National Meteorological Science Data Center and NASA; the thesis does not identify which variable came from which source.',
        'Therefore POWER is treated as a documented-source provisional reconstruction, not as proof of the exact original WTH.','']
for year in YEARS:
    start=f'{year}0501'; end=f'{year}1031'
    url=('https://power.larc.nasa.gov/api/temporal/daily/point?'
         f'parameters={PARAMS}&community=AG&longitude={LON:.6f}&latitude={LAT:.6f}'
         f'&start={start}&end={end}&format=JSON')
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=90) as r:
        data=r.read()
    (OUT/f'nasa_power_daily_{year}.json').write_bytes(data)
    obj=json.loads(data)
    par=obj['properties']['parameter']
    dates=sorted(set().union(*[set(par[p].keys()) for p in par]))
    rows=[]
    for ds in dates:
        d=dt.datetime.strptime(ds,'%Y%m%d').date()
        def v(p):
            x=par.get(p,{}).get(ds,-999)
            return '' if x in (-999,-999.0,None) else float(x)
        row={'date':d.isoformat(),'year':year,'doy':d.timetuple().tm_yday,
             'SRAD_MJ_m2_d':v('ALLSKY_SFC_SW_DWN'),'TMAX_C':v('T2M_MAX'),
             'TMIN_C':v('T2M_MIN'),'RAIN_mm':v('PRECTOTCORR')}
        rows.append(row); all_rows.append(row)
    with (OUT/f'power_daily_{year}.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    report += [f'## {year}', '']
    windows=[
        ('May-Aug',dt.date(year,5,1),dt.date(year,8,31)),
        ('sowing-Aug31',dt.date(year,5,3 if year==2019 else 5),dt.date(year,8,31)),
        ('May-Sep',dt.date(year,5,1),dt.date(year,9,30)),
        ('May-Oct',dt.date(year,5,1),dt.date(year,10,31)),
    ]
    for label,a,b in windows:
        rr=[x for x in rows if a.isoformat()<=x['date']<=b.isoformat()]
        rain=sum(float(x['RAIN_mm']) for x in rr if x['RAIN_mm']!='')
        tmax=sum(x['TMAX_C']!='' for x in rr); tmin=sum(x['TMIN_C']!='' for x in rr); srad=sum(x['SRAD_MJ_m2_d']!='' for x in rr)
        report.append(f'- {label} {a}..{b}: rain={rain:.2f} mm; rows={len(rr)}; TMAX={tmax}; TMIN={tmin}; SRAD={srad}.')
    pub=96.45 if year==2019 else 119.88
    report.append(f'- Guo (2025) reported growing-season rainfall: {pub:.2f} mm. Window definition is not explicitly stated in the thesis.')
    report.append('')

# DSSAT WTH-like compact CSV for downstream generation.
with (OUT/'shihezi_power_2019_2020_wth_inputs.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['date','year','doy','SRAD_MJ_m2_d','TMAX_C','TMIN_C','RAIN_mm']); w.writeheader(); w.writerows(all_rows)

report += ['## Use decision','',
           'Use this series for the first provisional M0 reproduction only after checking its rainfall/temperature consistency against Guo Fig. 2-2 and reported totals. Do not label it as the exact original station weather.',
           'For publication-grade validation, retain the CMA/National Meteorological Science Data Center series as the target weather input if it can be recovered.']
(OUT/'README_POWER_DAILY.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
print('\n'.join(report))
