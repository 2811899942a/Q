from __future__ import annotations

import csv
import gzip
import io
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

LAT = 44 + 19/60 + 28/3600
LON = 85 + 59/60 + 47/3600
YEARS = (2019, 2020)
OUT = Path('research/dssat_dtr/data/shihezi_real_case/weather_probe')
RAW = OUT / 'raw'
OUT.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)
for p in RAW.glob('ogimet_51356_*.html'):
    p.unlink()

UA = 'Mozilla/5.0 DSSAT-Xinjiang-research/1.0'


def fetch(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get('Content-Type', ''), r.read(), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, str(e.headers.get('Content-Type', '')), e.read(), url
    except Exception as e:
        return None, '', str(e).encode('utf-8', 'replace'), url


def save_bytes(name: str, data: bytes):
    (RAW / name).write_bytes(data)


def count_csv_rows(data: bytes):
    try:
        text = data.decode('utf-8', 'replace')
        rows = list(csv.reader(io.StringIO(text)))
        return max(0, len(rows)-1), rows[0] if rows else []
    except Exception:
        return None, []


results = []

def add(source, year, url, status, detail, usable, kind):
    results.append({
        'source': source, 'year': year, 'url': url, 'status': status,
        'detail': detail, 'usable': usable, 'kind': kind
    })

# 1) NOAA/NCEI Global Hourly direct WMO+99999 candidate.
for year in YEARS:
    url = f'https://www.ncei.noaa.gov/data/global-hourly/access/{year}/51356099999.csv'
    status, ctype, data, final = fetch(url)
    rows, header = count_csv_rows(data) if status == 200 else (None, [])
    good = bool(status == 200 and rows and rows > 100)
    if good:
        save_bytes(f'noaa_global_hourly_51356099999_{year}.csv', data)
    add('NOAA Global Hourly 51356099999', year, url, status,
        f'rows={rows}; header={header[:8]}; content_type={ctype}', good, 'station_hourly')

# 2) NOAA/NCEI GSOD daily direct candidate.
for year in YEARS:
    url = f'https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{year}/51356099999.csv'
    status, ctype, data, final = fetch(url)
    rows, header = count_csv_rows(data) if status == 200 else (None, [])
    good = bool(status == 200 and rows and rows > 100)
    if good:
        save_bytes(f'noaa_gsod_51356099999_{year}.csv', data)
    add('NOAA GSOD 51356099999', year, url, status,
        f'rows={rows}; header={header[:8]}; content_type={ctype}', good, 'station_daily')

# 3) Search NOAA Global Hourly directory listing for any filename containing WMO 51356.
for year in YEARS:
    url = f'https://www.ncei.noaa.gov/data/global-hourly/access/{year}/'
    status, ctype, data, final = fetch(url)
    text = data.decode('utf-8', 'replace') if status == 200 else ''
    hits = sorted(set(re.findall(r'href=["\']([^"\']*51356[^"\']*\.csv)["\']', text, re.I)))
    add('NOAA Global Hourly directory search WMO 51356', year, url, status,
        f'hits={hits[:20]} count={len(hits)}', bool(hits), 'station_hourly_index')

# 4) Meteostat bulk hourly candidate station ID 51356.
for year in YEARS:
    candidates = [
        f'https://bulk.meteostat.net/v2/hourly/{year}/51356.csv.gz',
        f'https://bulk.meteostat.net/v2/hourly/{year}/51356.csv.gz?download=1',
    ]
    succeeded = False
    for url in candidates:
        status, ctype, data, final = fetch(url)
        detail = f'bytes={len(data)}; content_type={ctype}'
        good = False
        if status == 200 and len(data) > 100:
            try:
                dec = gzip.decompress(data)
                good = len(dec) > 1000
                detail += f'; decompressed_bytes={len(dec)}; first={dec[:120]!r}'
                if good:
                    save_bytes(f'meteostat_hourly_51356_{year}.csv', dec)
                    succeeded = True
            except Exception as e:
                detail += f'; gzip_error={e}'
        add('Meteostat bulk hourly 51356', year, url, status, detail, good, 'station_hourly')
        if succeeded:
            break

# 4b) Meteostat bulk daily uses station-level file rather than year folders.
url = 'https://bulk.meteostat.net/v2/daily/51356.csv.gz'
status, ctype, data, final = fetch(url)
detail = f'bytes={len(data)}; content_type={ctype}'
good = False
if status == 200 and len(data) > 100:
    try:
        dec = gzip.decompress(data)
        text = dec.decode('utf-8', 'replace')
        n2019 = text.count('2019-')
        n2020 = text.count('2020-')
        good = n2019 > 100 and n2020 > 100
        detail += f'; decompressed_bytes={len(dec)}; n2019={n2019}; n2020={n2020}; first={dec[:120]!r}'
        if good:
            save_bytes('meteostat_daily_51356.csv', dec)
    except Exception as e:
        detail += f'; gzip_error={e}'
add('Meteostat bulk daily 51356', '2019-2020', url, status, detail, good, 'station_daily')

# 5) Meteostat station metadata bulk: confirm whether 51356 is catalogued and inspect nearby stations.
url = 'https://bulk.meteostat.net/v2/stations/lite.json.gz'
status, ctype, data, final = fetch(url)
detail = f'bytes={len(data)}; content_type={ctype}'
good = False
if status == 200 and len(data) > 100:
    try:
        dec = gzip.decompress(data)
        obj = json.loads(dec)
        matches = []
        nearby = []
        items = obj if isinstance(obj, list) else obj.values()
        for it in items:
            if '51356' in json.dumps(it, ensure_ascii=False):
                matches.append(it)
            try:
                la = float(it.get('location', {}).get('latitude', it.get('latitude')))
                lo = float(it.get('location', {}).get('longitude', it.get('longitude')))
                if abs(la-LAT) < 1.5 and abs(lo-LON) < 1.5:
                    nearby.append(it)
            except Exception:
                pass
        detail += f'; matches_51356={matches[:5]}; nearby_count={len(nearby)}; nearby={nearby[:10]}'
        good = bool(matches or nearby)
        (RAW / 'meteostat_station_matches.json').write_text(json.dumps({'matches_51356': matches, 'nearby': nearby}, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as e:
        detail += f'; parse_error={e}'
add('Meteostat station metadata', 'all', url, status, detail, good, 'station_metadata')

# 6) Ogimet SYNOP probe. A page which says NO DATA FOUND is explicitly unusable.
for year in YEARS:
    for month, day in [(6,30), (7,31), (8,31)]:
        url = (f'https://www.ogimet.com/cgi-bin/gsynres?ind=51356&lang=en&decoded=yes'
               f'&ndays=5&ano={year}&mes={month:02d}&day={day:02d}&hora=23')
        status, ctype, data, final = fetch(url)
        text = data.decode('latin-1', 'replace') if status == 200 else ''
        no_data = 'NO DATA FOUND' in text.upper()
        station_mentions = text.count('51356')
        date_mentions = text.count(str(year))
        # Decoded data pages contain meteorological data rows; metadata-only/no-data pages do not count.
        data_tokens = sum(text.upper().count(tok) for tok in ['TEMPERATURE', 'DEW POINT', 'PRESSURE', 'PRECIPITATION'])
        good = bool(status == 200 and not no_data and len(text) > 2500 and date_mentions > 3 and data_tokens > 2)
        if good:
            save_bytes(f'ogimet_51356_{year}_{month:02d}.html', data)
        add('Ogimet SYNOP 51356', f'{year}-{month:02d}', url, status,
            f'bytes={len(data)}; no_data={no_data}; station_mentions={station_mentions}; year_mentions={date_mentions}; data_tokens={data_tokens}; content_type={ctype}', good, 'station_synop')

# 7) NASA POWER hourly as explicit reanalysis/satellite-model fallback, not station observations.
for year in YEARS:
    start = f'{year}0501'; end = f'{year}1001'
    url = ('https://power.larc.nasa.gov/api/temporal/hourly/point?'
           f'parameters=T2M&community=AG&longitude={LON:.6f}&latitude={LAT:.6f}'
           f'&start={start}&end={end}&format=JSON')
    status, ctype, data, final = fetch(url, timeout=60)
    good = False
    detail = f'bytes={len(data)}; content_type={ctype}'
    if status == 200:
        try:
            obj = json.loads(data)
            vals = obj.get('properties', {}).get('parameter', {}).get('T2M', {})
            good = len(vals) > 1000
            detail += f'; hourly_T2M_count={len(vals)}'
            if good:
                save_bytes(f'nasa_power_hourly_T2M_{year}.json', data)
        except Exception as e:
            detail += f'; parse_error={e}'
    add('NASA POWER hourly T2M', year, url, status, detail, good, 'reanalysis_fallback')

with (OUT / 'weather_source_probe.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['source','year','status','usable','kind','detail','url'])
    w.writeheader(); w.writerows(results)

lines = [
    '# Shihezi 2019-2020 weather-source probe', '',
    f'Experiment coordinate: {LAT:.6f} N, {LON:.6f} E (Guo 2025).',
    'Priority: real station hourly temperature > real station daily > reanalysis fallback.', '',
    '| Source | Year/window | Status | Usable | Type | Detail |',
    '|---|---|---:|---|---|---|'
]
for r in results:
    detail = str(r['detail']).replace('|','/').replace('\n',' ')[:700]
    lines.append(f"| {r['source']} | {r['year']} | {r['status']} | {r['usable']} | {r['kind']} | {detail} |")

station_hourly = [r for r in results if r['kind'] in ('station_hourly','station_synop') and r['usable']]
station_daily = [r for r in results if r['kind'] == 'station_daily' and r['usable']]
rean = [r for r in results if r['kind'] == 'reanalysis_fallback' and r['usable']]
lines += ['', '## Decision', '']
if station_hourly:
    lines.append('At least one real/subdaily station-data route responded with usable data. Inspect saved raw files first and prefer this route for the formal M15 validation.')
elif station_daily:
    lines.append('No usable real hourly station route was recovered in this probe, but real daily station data are available. Use these for the published-M0 WTH reconstruction while continuing the hourly search.')
elif rean:
    lines.append('Only a reanalysis fallback was recovered in this probe. It can support a sensitivity calculation but cannot be labelled as measured station-hourly validation. The formal station-data route should continue through CMA/National Meteorological Science Data Center.')
else:
    lines.append('No source recovered usable data. Do not fabricate weather; continue with CMA/National Meteorological Science Data Center or another station archive.')

(OUT / 'README_WEATHER_SOURCE_PROBE.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('\n'.join(lines[-8:]))
