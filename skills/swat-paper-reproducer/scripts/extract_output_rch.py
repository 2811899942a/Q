#!/usr/bin/env python3
"""Extract monthly outlet FLOW_OUTcms from SWAT output.rch."""
import argparse
import re
from pathlib import Path
import pandas as pd


def parse_output_rch(path):
    lines = Path(path).read_text(errors='ignore').splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if 'RCH' in line and 'MON' in line and 'FLOW_OUT' in line:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError('could not find output.rch header containing RCH, MON, FLOW_OUT')
    headers = re.split(r'\s+', lines[header_idx].strip())
    rows = []
    for line in lines[header_idx + 1:]:
        parts = re.split(r'\s+', line.strip())
        if len(parts) < len(headers):
            continue
        if not parts[0].replace('.', '', 1).isdigit():
            continue
        vals = parts[:len(headers)]
        rows.append(vals)
    df = pd.DataFrame(rows, columns=headers)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument('output_rch')
    p.add_argument('--reach', type=int, help='reach ID; default largest AREAkm2')
    p.add_argument('--start-year', type=int, required=True)
    p.add_argument('--end-year', type=int, required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    df = parse_output_rch(args.output_rch)
    area_col = next((c for c in df.columns if c.upper() == 'AREAkm2'.upper()), None)
    if args.reach is None:
        reach = int(df.groupby('RCH')[area_col].max().idxmax()) if area_col else int(df['RCH'].max())
    else:
        reach = args.reach
    flow_col = next((c for c in df.columns if c.upper().startswith('FLOW_OUT')), None)
    if flow_col is None:
        raise ValueError('FLOW_OUT column not found')
    # monthly rows have MON 1..12; yearly rows have MON as year; final averages often have other values
    m = df[(df['RCH'] == reach) & (df['MON'].between(1, 12))].copy()
    # assign years sequentially for monthly output after warm-up
    months = list(range(1, 13)) * (args.end_year - args.start_year + 1)
    years = [y for y in range(args.start_year, args.end_year + 1) for _ in range(12)]
    m = m.head(len(months)).copy()
    m['year'] = years[:len(m)]
    m['month'] = months[:len(m)]
    m['date'] = pd.to_datetime(dict(year=m['year'], month=m['month'], day=1))
    out = pd.DataFrame({
        'date': m['date'], 'year': m['year'], 'month': m['month'], 'RCH': reach,
        'AREAkm2': m[area_col] if area_col else None, 'q_sim_m3s': m[flow_col]
    })
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f'wrote {len(out)} rows for reach {reach} to {args.out}')


if __name__ == '__main__':
    main()
