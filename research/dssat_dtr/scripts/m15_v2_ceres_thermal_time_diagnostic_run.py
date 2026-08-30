#!/usr/bin/env python3
"""Compatibility launcher for the CERES DTT diagnostic.

The locked Shihezi CSV uses the canonical project header
`date,year,doy,SRAD_MJ_m2_d,TMAX_C,TMIN_C,RAIN_mm` while the diagnostic core
expects normalized names `DATE` and `SRAD_MJ_m2`. This launcher performs only
that schema normalization in a temporary file, then executes the unchanged
scientific diagnostic.
"""
from pathlib import Path
import csv
import tempfile

import m15_v2_ceres_thermal_time_diagnostic as core


def main():
    src = core.WEATHER
    tmpdir = Path(tempfile.mkdtemp(prefix='m15_dtt_weather_'))
    dst = tmpdir / 'shihezi_weather_normalized.csv'
    with src.open(encoding='utf-8-sig') as f, dst.open('w', newline='', encoding='utf-8') as g:
        reader = csv.DictReader(f)
        required = {'date','year','doy','SRAD_MJ_m2_d','TMAX_C','TMIN_C','RAIN_mm'}
        if set(reader.fieldnames or []) != required:
            raise RuntimeError(f'Unexpected Shihezi weather schema: {reader.fieldnames}')
        fields = ['DATE','YYYYDDD','SRAD_MJ_m2','TMAX_C','TMIN_C','RAIN_mm']
        writer = csv.DictWriter(g, fieldnames=fields)
        writer.writeheader()
        for r in reader:
            writer.writerow({
                'DATE': r['date'],
                'YYYYDDD': f"{int(r['year']):04d}{int(r['doy']):03d}",
                'SRAD_MJ_m2': r['SRAD_MJ_m2_d'],
                'TMAX_C': r['TMAX_C'],
                'TMIN_C': r['TMIN_C'],
                'RAIN_mm': r['RAIN_mm'],
            })
    core.WEATHER = dst
    core.main()


if __name__ == '__main__':
    main()
