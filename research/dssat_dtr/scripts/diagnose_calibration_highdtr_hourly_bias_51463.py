#!/usr/bin/env python3
"""Calibration-only hourly residual profile for high-DTR Urumqi days.

Purpose: determine when the high-DTR residual becomes warm-biased in 2000-2016
without using validation years to define a source-model breakpoint.
"""
import csv, statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'/'processed_51463';IN=DATA/'htemp_pointwise_2000_2024.csv';OUT=DATA/'calibration_highdtr_hourly_bias.csv';README=DATA/'README_CALIBRATION_HIGHDTR_HOURLY_BIAS.md';DTRC=14.8

def main():
 g=defaultdict(list)
 with IN.open('r',newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   y=int(r['solar_date'][:4]);m=int(r['month']);d=float(r['formal_dtr_c'])
   if y>2016 or not 5<=m<=9 or d<=DTRC:continue
   h=int(float(r['solar_hour']));g[h].append((float(r['solar_hour']),float(r['error_c'])))
 rows=[]
 for h in sorted(g):
  vals=g[h];rows.append({'solar_hour_bin':h,'n':len(vals),'mean_actual_solar_hour':round(statistics.mean(x[0] for x in vals),3),'mean_bias_c':round(statistics.mean(x[1] for x in vals),4),'median_bias_c':round(statistics.median(x[1] for x in vals),4),'rmse_c':round((statistics.mean(x[1]**2 for x in vals))**.5,4)})
 with OUT.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
 first_pos=next((r for r in rows if 6<=r['solar_hour_bin']<=14 and r['mean_bias_c']>0),None)
 last_neg=next((r for r in reversed(rows) if 6<=r['solar_hour_bin']<=14 and r['mean_bias_c']<=0),None)
 text='# Calibration-only high-DTR hourly residual profile\n\nOnly 2000-2016 May-Sep days with DTR>14.8 C are used.\n\n| Solar-hour bin | N | Mean actual hour | Mean Bias | Median Bias | RMSE |\n|---|---:|---:|---:|---:|---:|\n'
 for r in rows:text+=f"| {r['solar_hour_bin']} | {r['n']} | {r['mean_actual_solar_hour']:.3f} | {r['mean_bias_c']:+.3f} | {r['median_bias_c']:+.3f} | {r['rmse_c']:.3f} |\n"
 text+='\n'
 if first_pos:text+=f"First supported 06-14 bin with positive mean bias: **{first_pos['solar_hour_bin']}** (mean actual solar hour {first_pos['mean_actual_solar_hour']:.3f}, Bias {first_pos['mean_bias_c']:+.3f} C).\n"
 if last_neg:text+=f"Last supported 06-14 bin with non-positive mean bias: **{last_neg['solar_hour_bin']}** (Bias {last_neg['mean_bias_c']:+.3f} C).\n"
 README.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
