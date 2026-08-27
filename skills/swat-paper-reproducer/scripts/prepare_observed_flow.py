#!/usr/bin/env python3
"""Prepare SWAT-CUP observed flow text files from monthly CSV/XLSX data."""
import argparse
from pathlib import Path
import pandas as pd


def main():
    p = argparse.ArgumentParser()
    p.add_argument('monthly_file')
    p.add_argument('--date-col', default='date')
    p.add_argument('--flow-col', required=True)
    p.add_argument('--start', required=True, help='YYYY-MM')
    p.add_argument('--end', required=True, help='YYYY-MM')
    p.add_argument('--out-txt', required=True)
    p.add_argument('--out-csv')
    args = p.parse_args()
    path = Path(args.monthly_file)
    df = pd.read_excel(path) if path.suffix.lower() in ['.xlsx', '.xls'] else pd.read_csv(path)
    if args.date_col in df.columns:
        df['date'] = pd.to_datetime(df[args.date_col])
    else:
        df['date'] = pd.to_datetime(dict(year=df['year'], month=df['month'], day=1))
    start = pd.to_datetime(args.start + '-01')
    end = pd.to_datetime(args.end + '-01')
    out = df[(df['date'] >= start) & (df['date'] <= end)].copy()
    out = out.sort_values('date').reset_index(drop=True)
    out['index'] = range(1, len(out) + 1)
    result = out[['index', args.flow_col]].rename(columns={args.flow_col: 'flow_m3s'})
    Path(args.out_txt).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.out_txt, sep=' ', header=False, index=False, float_format='%.6f')
    if args.out_csv:
        Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(args.out_csv, index=False)
    print(f'wrote {len(result)} observed rows to {args.out_txt}')


if __name__ == '__main__':
    main()
