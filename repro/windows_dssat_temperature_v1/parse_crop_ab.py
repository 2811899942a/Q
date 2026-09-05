#!/usr/bin/env python3
"""Parse Windows M0/M15/M19 DSSAT Summary.OUT copies into compact A/B evidence."""
from __future__ import annotations
import argparse,csv,re,statistics
from pathlib import Path

MODELS=('M0','M15','M19')
SCENARIOS=[f'ANQH{yy}{i:02d}' for yy in ('21','22') for i in range(1,6)]
DATES={1:'Apr21',2:'Apr26',3:'May06',4:'May16',5:'May26'}
TARGETS=['PDAT','EDAT','ADAT','MDAT','HDAT','CWAM','HWAM','HIAM','LAIX','NDCH','TMAXA','TMINA','SRADA','DAYLA','CRST']
COMPARE=['ADAT','MDAT','CWAM','HWAM','HIAM','LAIX']

def parse_summary(path:Path):
    lines=path.read_text(errors='replace').splitlines()
    hi=next(i for i,l in enumerate(lines) if l.startswith('@') and 'RUNNO' in l and 'HWAM' in l)
    header=lines[hi]
    starts=[x.start() for x in re.finditer(r'\S+',header)]
    names=[x.group() for x in re.finditer(r'\S+',header)]
    if names[0]=='@':names=names[1:];starts=starts[1:]
    data=next(l for l in lines[hi+1:] if l.strip() and not l.startswith('!') and not l.startswith('@'))
    out={}
    for j,n in enumerate(names):
        a=starts[j];b=starts[j+1] if j+1<len(starts) else len(data)
        out[n]=data[a:b].strip()
    return out

def fnum(x):
    try:return float(x)
    except:return None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('results_root',type=Path);ap.add_argument('output_dir',type=Path);args=ap.parse_args()
    rows=[]
    for sc in SCENARIOS:
        got={m:parse_summary(args.results_root/m/f'{sc}_Summary.OUT') for m in MODELS}
        r={'scenario':sc,'year':2000+int(sc[4:6]),'sowing':DATES[int(sc[6:8])]}
        for m in MODELS:
            for k in TARGETS:r[f'{m}_{k}']=got[m].get(k,'')
        for m in ('M15','M19'):
            for k in COMPARE:
                try:r[f'{m}_minus_M0_{k}']=float(got[m][k])-float(got['M0'][k])
                except:r[f'{m}_minus_M0_{k}']=''
        rows.append(r)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    with (args.output_dir/'m0_m15_m19_crop_outputs.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    sums=[]
    for m in ('M15','M19'):
        dy=[fnum(r[f'{m}_minus_M0_HWAM']) for r in rows];dy=[x for x in dy if x is not None]
        da=[fnum(r[f'{m}_minus_M0_ADAT']) for r in rows];da=[x for x in da if x is not None]
        dm=[fnum(r[f'{m}_minus_M0_MDAT']) for r in rows];dm=[x for x in dm if x is not None]
        changed=sum(1 for r in rows if any(abs(fnum(r.get(f'{m}_minus_M0_{k}')) or 0)>1e-9 for k in COMPARE))
        sums.append({'model':m,'scenarios':len(rows),'changed_scenarios':changed,'mean_delta_yield_kg_ha':statistics.mean(dy),'max_abs_delta_yield_kg_ha':max(abs(x) for x in dy),'mean_delta_anthesis_day':statistics.mean(da),'mean_delta_maturity_day':statistics.mean(dm)})
    with (args.output_dir/'propagation_summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(sums[0]));w.writeheader();w.writerows(sums)
    md=['# Windows source-level DSSAT M0/M15/M19 propagation','',
        'All arms share identical weather, soil, crop, sowing-date, water and nitrogen settings. Only HTEMP source differs.','',
        '|Model|Changed scenarios|Mean delta yield vs M0 (kg/ha)|Max abs delta yield (kg/ha)|Mean delta anthesis (d)|Mean delta maturity (d)|','|---|---:|---:|---:|---:|---:|']
    for s in sums:md.append(f"|{s['model']}|{s['changed_scenarios']}/{s['scenarios']}|{s['mean_delta_yield_kg_ha']:.2f}|{s['max_abs_delta_yield_kg_ha']:.2f}|{s['mean_delta_anthesis_day']:.2f}|{s['mean_delta_maturity_day']:.2f}|")
    md+=['','PASS criterion for mechanism reproduction: M19 must compile/run cleanly and produce at least one reproducible crop-output difference from M0 under identical inputs. Exact Linux/Windows floating-point equality is not required.']
    (args.output_dir/'README.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print('\n'.join(md))
if __name__=='__main__':main()
