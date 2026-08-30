#!/usr/bin/env python3
"""Run frozen Shihezi DSSAT arms and compare actual phenology outputs.

Diagnostic only: no parameter fitting, no crop-observation selection.
"""
from __future__ import annotations

from pathlib import Path
import csv
import json
import shutil
import subprocess

import m15_v2_round3_crop_propagation as crop

ROOT = Path.cwd() / 'research' / 'dssat_dtr'
OUT = ROOT / 'data' / 'm15_temp_v2' / 'phenology_diagnostic'
RESULT_CP = ROOT / 'CHECKPOINT_20260830_M15_V2_PHENOLOGY_DIAGNOSTIC_RESULT.md'
ARMS = ['M15_13P5','M15_13P8','R1_P05','R3_P05_B105']
CASES = [('2019_W1','SHIH1901'),('2019_W4','SHIH1904'),('2020_W1','SHIH2001'),('2020_W4','SHIH2004')]


def write_csv(path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)


def run_case(arm, case_name, case_file):
    root=crop.ROOTS[arm]
    maize=root/'Maize'
    subprocess.run(['sudo','rm','-rf','/DSSAT48'],check=True)
    subprocess.run(['sudo','ln','-s',str(root),'/DSSAT48'],check=True)
    for fn in ('Summary.OUT','PlantGro.OUT','Overview.OUT','INFO.OUT','ERROR.OUT','WARNING.OUT'):
        p=maize/fn
        if p.exists():p.unlink()
    cp=subprocess.run(['../dscsm048','A',case_file+'.MZX'],cwd=maize,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if cp.returncode!=0 or not (maize/'Summary.OUT').exists():
        raise RuntimeError(f'{arm} {case_file} failed\n{cp.stdout[-4000:]}')
    dest=OUT/'raw'/arm/case_name
    dest.mkdir(parents=True,exist_ok=True)
    retained=[]
    for fn in ('Summary.OUT','PlantGro.OUT','Overview.OUT'):
        src=maize/fn
        if src.exists():
            shutil.copy2(src,dest/fn)
            retained.append(fn)
    return dest, retained


def parse_tables(path):
    """Return generic DSSAT @header -> first following data row tables."""
    lines=path.read_text(errors='replace').splitlines()
    tables=[]
    for i,line in enumerate(lines):
        if not line.startswith('@'):
            continue
        headers=line[1:].split()
        if not headers:
            continue
        data_line=None
        for j in range(i+1,len(lines)):
            s=lines[j].strip()
            if not s: continue
            if s.startswith(('@','!','*')): break
            data_line=lines[j]
            break
        if data_line is None: continue
        vals=data_line.split()
        if len(vals)==len(headers):
            mapping=dict(zip(headers,vals))
        elif len(vals)>len(headers):
            mapping=dict(zip(headers,vals[-len(headers):]))
        else:
            mapping={h:(vals[k] if k<len(vals) else '') for k,h in enumerate(headers)}
        tables.append({'header':headers,'values':vals,'mapping':mapping,'header_line':i+1})
    return tables


def phenology_fields(tables):
    fields={}
    wanted_exact={'EDAT','ADAT','MDAT','PDAT','HDAT','SDAT','EMDAT','ANTH','MATD','EMER','SILK'}
    for t in tables:
        for k,v in t['mapping'].items():
            ku=k.upper()
            if ku in wanted_exact or ku.endswith('DAT') or 'DATE' in ku or 'DOY' in ku or 'STAGE' in ku or ku=='XSTAGE':
                fields.setdefault(ku,v)
    return fields


def parse_plantgro(path):
    if not path.exists(): return {}
    lines=path.read_text(errors='replace').splitlines()
    header_i=None
    for i,l in enumerate(lines):
        if l.startswith('@') and 'YEAR' in l and 'DOY' in l:
            header_i=i
    if header_i is None:return {}
    headers=lines[header_i][1:].split(); rows=[]
    for l in lines[header_i+1:]:
        s=l.strip()
        if not s or s.startswith(('@','!','*')):continue
        vals=l.split()
        if len(vals)>=len(headers): rows.append(dict(zip(headers,vals[:len(headers)])))
    if not rows:return {}
    out={'first_YEAR':rows[0].get('YEAR',''),'first_DOY':rows[0].get('DOY',''),'last_YEAR':rows[-1].get('YEAR',''),'last_DOY':rows[-1].get('DOY','')}
    for key in ('DAS','DAP','TSD','XSTAGE','STG','LAID','CWAD','HWAD'):
        if key in rows[-1]:out['last_'+key]=rows[-1][key]
    return out


def main():
    if OUT.exists():shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # Reuse the already-audited Round-3 source construction and identical-input gate.
    source_audit, shape_diff, b_diff = crop.build_sources()
    shared=crop.build_inputs()
    if not all(bool(x['byte_identical_all_arms']) for x in shared):
        raise RuntimeError('Shared input gate failed')

    records=[];field_rows=[];table_dump={}
    for arm in ARMS:
        for case_name,case_file in CASES:
            dest,retained=run_case(arm,case_name,case_file)
            tables=parse_tables(dest/'Summary.OUT')
            fields=phenology_fields(tables)
            pg=parse_plantgro(dest/'PlantGro.OUT')
            table_dump[f'{arm}/{case_name}']=tables
            rec={'arm':arm,'case':case_name,'case_file':case_file,'retained_files':','.join(retained),**fields,**pg}
            records.append(rec)
            for k,v in fields.items():field_rows.append({'arm':arm,'case':case_name,'field':k,'value':v})
    write_csv(OUT/'phenology_summary.csv',records)
    write_csv(OUT/'phenology_fields_long.csv',field_rows)
    write_csv(OUT/'source_audit.csv',source_audit)
    write_csv(OUT/'shared_input_audit.csv',shared)
    (OUT/'summary_tables.json').write_text(json.dumps(table_dump,indent=2),encoding='utf-8')

    # Compare every extracted phenology field across the three prespecified contrasts.
    idx={(r['arm'],r['case']):r for r in records}
    contrasts=[]
    pairdefs=[('R1_P05','M15_13P5','R1_minus_M15_13P5'),('R3_P05_B105','R1_P05','R3_minus_R1'),('M15_13P8','M15_13P5','M15_13P8_minus_13P5')]
    for cand,ref,label in pairdefs:
        for case_name,_ in CASES:
            a=idx[(cand,case_name)];b=idx[(ref,case_name)]
            common=sorted(set(a)&set(b))
            for k in common:
                if k in {'arm','case','case_file','retained_files'} or k.startswith('first_') or k.startswith('last_'):continue
                if k.endswith('DAT') or 'DATE' in k or 'DOY' in k or 'STAGE' in k or k in {'ANTH','MATD','EMER','SILK'}:
                    contrasts.append({'contrast':label,'case':case_name,'field':k,'reference_value':b[k],'candidate_value':a[k],'changed':str(a[k])!=str(b[k])})
    write_csv(OUT/'phenology_contrasts.csv',contrasts)

    def changed(label):return [r for r in contrasts if r['contrast']==label and r['changed']]
    c1=changed('R1_minus_M15_13P5');c3=changed('R3_minus_R1');c8=changed('M15_13P8_minus_13P5')
    # Check whether W1/W4 extracted phenology fields within each arm-year are identical.
    irrigation_diff=[]
    for arm in ARMS:
        for year in ('2019','2020'):
            a=idx[(arm,year+'_W1')];b=idx[(arm,year+'_W4')]
            keys=sorted(set(a)&set(b))
            dif=[k for k in keys if (k.endswith('DAT') or 'DATE' in k or 'DOY' in k or 'STAGE' in k) and str(a[k])!=str(b[k])]
            irrigation_diff.append({'arm':arm,'year':year,'n_changed_phenology_fields_W1_vs_W4':len(dif),'changed_fields':','.join(dif)})
    write_csv(OUT/'irrigation_phenology_check.csv',irrigation_diff)

    if not c1 and c3:
        interpretation='ROUND1_PHENOLOGY_UNCHANGED_ROUND3_PHENOLOGY_CHANGED'
    elif not c1 and not c3:
        interpretation='PHENOLOGY_DATES_UNCHANGED_INSPECT_OTHER_HMET_GROWTH_PATHS'
    elif c1 and c3:
        interpretation='BOTH_ROUNDS_CHANGE_PHENOLOGY_MAGNITUDE_TIMING_NEEDS_QUANTIFICATION'
    else:
        interpretation='ROUND1_CHANGES_PHENOLOGY_BUT_ROUND3_DOES_NOT_UNEXPECTED'

    manifest={'source_commit':crop.OS_COMMIT,'data_commit':crop.DATA_COMMIT,'cases':[x[0] for x in CASES],
              'source_isolation_shape_diff_lines':len(shape_diff),'source_isolation_B_diff_lines':len(b_diff),
              'shared_input_gate':True,'R1_changed_fields':c1,'R3_changed_fields':c3,'M15_13P8_changed_fields':c8,
              'irrigation_phenology_check':irrigation_diff,'interpretation':interpretation}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

    text=f'''# M15-V2 phenology propagation diagnostic result

## Integrity
- DSSAT source: `{crop.OS_COMMIT}`; data: `{crop.DATA_COMMIT}`.
- Shared SRAD19P8_N_OFF inputs: **PASS**.
- M15_13P5 vs R1 source shape difference: **{len(shape_diff)} line**.
- R1 vs R3 nighttime-B source difference: **{len(b_diff)} line**.
- Raw Summary.OUT / PlantGro.OUT / Overview.OUT retained for every probed arm/case.

## Extracted phenology fields

|Arm|Case|EDAT|ADAT|MDAT|last PlantGro DOY|
|---|---|---:|---:|---:|---:|
'''
    for r in records:
        text+=f"|{r['arm']}|{r['case']}|{r.get('EDAT','')}|{r.get('ADAT','')}|{r.get('MDAT','')}|{r.get('last_DOY','')}|\n"
    text+=f'''
## Prespecified contrasts
- Round1 vs M15-13.5 changed extracted phenology fields: **{len(c1)}**.
- Round3 vs Round1 changed extracted phenology fields: **{len(c3)}**.
- M15-13.8 vs M15-13.5 changed extracted phenology fields: **{len(c8)}**.

## Irrigation-extreme check
'''
    for r in irrigation_diff:text+=f"- {r['arm']} {r['year']}: W1 vs W4 changed fields = **{r['n_changed_phenology_fields_W1_vs_W4']}** {r['changed_fields']}\n"
    text+=f'''

## Diagnostic interpretation
**{interpretation}**

This remains a no-fit diagnostic and does not alter the current temperature winner.
'''
    (OUT/'README_M15_V2_PHENOLOGY_DIAGNOSTIC.md').write_text(text,encoding='utf-8');RESULT_CP.write_text(text,encoding='utf-8');print(text)


if __name__=='__main__':main()
