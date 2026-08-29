from __future__ import annotations

import csv
import datetime as dt
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

STATION = 'CHM00051356'
YEARS = {2019, 2020}
OUT = Path('research/dssat_dtr/data/shihezi_real_case/ghcn_daily_51356')
OUT.mkdir(parents=True, exist_ok=True)
UA = 'Mozilla/5.0 DSSAT-Xinjiang-research/1.0'


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), r.headers.get('Content-Type', '')
    except urllib.error.HTTPError as e:
        return e.code, e.read(), str(e.headers.get('Content-Type', ''))
    except Exception as e:
        return None, str(e).encode(), ''


urls = [
    f'https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/{STATION}.csv',
    f'https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/{STATION}.dly',
]
probe = []
raw_csv = None
raw_dly = None
for url in urls:
    status, data, ctype = fetch(url)
    probe.append((url, status, len(data), ctype))
    if status == 200 and len(data) > 1000:
        if url.endswith('.csv'):
            raw_csv = data
            (OUT / f'{STATION}.csv').write_bytes(data)
        else:
            raw_dly = data
            (OUT / f'{STATION}.dly').write_bytes(data)

records = defaultdict(dict)
source = None

# Prefer NCEI station CSV when its schema has daily element rows or wide daily fields.
if raw_csv:
    text = raw_csv.decode('utf-8', 'replace').splitlines()
    reader = csv.DictReader(text)
    fields = reader.fieldnames or []
    rows = list(reader)
    # Common NCEI station-access format is wide with DATE,TMAX,TMIN,PRCP.
    if 'DATE' in fields and any(k in fields for k in ('TMAX','TMIN','PRCP')):
        for r in rows:
            try:
                d = dt.date.fromisoformat(r['DATE'][:10])
            except Exception:
                continue
            if d.year not in YEARS:
                continue
            for key in ('TMAX','TMIN','PRCP'):
                val = r.get(key, '')
                if val not in ('', None):
                    try:
                        records[d][key] = float(val)
                    except Exception:
                        pass
        if records:
            source = 'NCEI GHCN-D station CSV'

# Fixed-width .dly fallback / cross-check.
if raw_dly and not records:
    for line in raw_dly.decode('ascii', 'replace').splitlines():
        if len(line) < 269 or line[:11] != STATION:
            continue
        year = int(line[11:15]); month = int(line[15:17]); element = line[17:21]
        if year not in YEARS or element not in ('TMAX','TMIN','PRCP'):
            continue
        for day in range(1, 32):
            base = 21 + (day-1)*8
            value_s = line[base:base+5]
            mflag = line[base+5:base+6]
            qflag = line[base+6:base+7]
            sflag = line[base+7:base+8]
            try:
                value = int(value_s)
            except Exception:
                continue
            if value == -9999:
                continue
            try:
                d = dt.date(year, month, day)
            except ValueError:
                continue
            # GHCN-D TMAX/TMIN are tenths C; PRCP is tenths mm.
            records[d][element] = value / 10.0
            records[d][element + '_MFLAG'] = mflag
            records[d][element + '_QFLAG'] = qflag
            records[d][element + '_SFLAG'] = sflag
    if records:
        source = 'NCEI GHCN-D fixed-width DLY'

out_rows = []
for d in sorted(records):
    r = records[d]
    out_rows.append({
        'date': d.isoformat(),
        'TMAX_C': r.get('TMAX', ''),
        'TMIN_C': r.get('TMIN', ''),
        'PRCP_mm': r.get('PRCP', ''),
        'TMAX_QFLAG': r.get('TMAX_QFLAG', ''),
        'TMIN_QFLAG': r.get('TMIN_QFLAG', ''),
        'PRCP_QFLAG': r.get('PRCP_QFLAG', ''),
    })

with (OUT / 'shihezi_51356_2019_2020_daily.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['date','TMAX_C','TMIN_C','PRCP_mm','TMAX_QFLAG','TMIN_QFLAG','PRCP_QFLAG'])
    w.writeheader(); w.writerows(out_rows)

lines = [
    '# Shihezi WMO 51356 - GHCN-Daily recovery', '',
    f'Station candidate: {STATION} (WMO 51356).',
    f'Chosen parsed source: {source}', '',
    '## Endpoint probe', '',
]
for url, status, n, ctype in probe:
    lines.append(f'- `{status}` {url} - {n} bytes - {ctype}')

lines += ['', '## Coverage', '']
for year in sorted(YEARS):
    yr = [r for r in out_rows if r['date'].startswith(str(year))]
    grow = [r for r in yr if '-05-' in r['date'] or '-06-' in r['date'] or '-07-' in r['date'] or '-08-' in r['date'] or '-09-' in r['date']]
    for label, rr in [('full year', yr), ('May-Sep', grow)]:
        n = len(rr)
        ntmax = sum(r['TMAX_C'] != '' for r in rr)
        ntmin = sum(r['TMIN_C'] != '' for r in rr)
        nprcp = sum(r['PRCP_mm'] != '' for r in rr)
        badq = sum(any(str(r[k]).strip() for k in ('TMAX_QFLAG','TMIN_QFLAG','PRCP_QFLAG')) for r in rr)
        lines.append(f'- {year} {label}: rows={n}, TMAX={ntmax}, TMIN={ntmin}, PRCP={nprcp}, rows_with_nonblank_quality_flag={badq}')

complete_growing = True
for year in YEARS:
    d0 = dt.date(year,5,1); d1 = dt.date(year,9,30)
    expected = (d1-d0).days+1
    rr = [r for r in out_rows if d0.isoformat() <= r['date'] <= d1.isoformat()]
    if len(rr) != expected or any(r['TMAX_C']=='' or r['TMIN_C']=='' for r in rr):
        complete_growing = False

lines += ['', '## Decision', '']
if complete_growing:
    lines.append('PASS: 2019-2020 May-Sep has complete daily TMAX/TMIN coverage. This can serve as the station-observation temperature backbone for the Shihezi DSSAT WTH reconstruction; PRCP coverage should be checked separately, and SRAD can be sourced consistently with the thesis (NASA).')
elif out_rows:
    lines.append('PARTIAL: GHCN-D contains station data, but growing-season TMAX/TMIN coverage is incomplete. Use observed days where available and do not silently gap-fill; a documented complementary source is required.')
else:
    lines.append('FAIL: CHM00051356 did not yield usable 2019-2020 GHCN-Daily records. Continue through CMA/National Meteorological Science Data Center.')

(OUT / 'README_GHCN_DAILY_51356.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('\n'.join(lines[-12:]))
