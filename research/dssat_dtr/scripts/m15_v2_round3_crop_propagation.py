#!/usr/bin/env python3
"""Downstream crop propagation for promoted p=.5 + Bnight=1.05 temperature model."""
from __future__ import annotations
from pathlib import Path
import csv, hashlib, json, math, shutil, statistics, subprocess
import shihezi_dtrc_fourlevel_ablation as base

REPO=Path.cwd();ROOT=REPO/'research'/'dssat_dtr';OUT=ROOT/'data'/'m15_temp_v2'/'crop_propagation_round3'
RESULT_CP=ROOT/'CHECKPOINT_20260830_M15_V2_ROUND3_CROP_PROPAGATION_RESULT.md'
OS_COMMIT='0b91373806786b600d89ccfcfff78fa2f82cb26b';DATA_COMMIT='79cb5db71bbca186add92a6a9695866a09c8b51d'
ARMS=['H0TT','M15_13P5','M15_13P8','R1_P05','R3_P05_B105'];ROOTS={a:Path('/tmp')/f'run_{a}' for a in ARMS}
PARAMS={'M15_13P5':(13.5,6.4080),'M15_13P8':(13.8,6.7498),'R1_P05':(13.5,6.4080),'R3_P05_B105':(13.5,6.4080)}
EXPECTED={'H0TT':(2977.2722,26.9147158),'M15_13P5':(2820.48666,25.4973651),'M15_13P8':(2656.20001,24.0122042),'R1_P05':(2820.48666,25.4973651)}

def mean(x):return statistics.mean(x) if x else float('nan')
def rmse(x):return math.sqrt(mean([v*v for v in x])) if x else float('nan')
def run(cmd,cwd=None,quiet=False):
    kw={'cwd':cwd,'check':True,'text':True}
    if quiet:kw.update(stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return subprocess.run(cmd,**kw)
def sha(path):
    h=hashlib.sha256();h.update(path.read_bytes());return h.hexdigest()
def write_csv(path,rows):
    if not rows:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def patch_m15_arm(src,arm,dtrc,alpha):
    run(['python','research/dssat_dtr/dssat485/apply_m15_htemp_patch.py',str(src)])
    run(['python','research/dssat_dtr/dssat485/apply_m15_extreme_dtt_patch.py',str(src)])
    p=src/'Weather/HMET.for';txt=p.read_text(encoding='latin-1')
    old='PARAMETER (DTRC=14.8, ALPHA=7.8094)';assert txt.count(old)==1
    txt=txt.replace(old,f'PARAMETER (DTRC={dtrc:.1f}, ALPHA={alpha:.4f})',1)
    if arm in ('R1_P05','R3_P05_B105'):
        oldshape='          TAIRHR = TMAX - (TMAX-TS1)*R';newshape='          TAIRHR = TMAX - (TMAX-TS1)*SQRT(R)';assert txt.count(oldshape)==1;txt=txt.replace(oldshape,newshape,1)
    if arm=='R3_P05_B105':
        s=txt.index('      SUBROUTINE HTEMP_DTRCLOUD(');e=txt.index('      END SUBROUTINE HTEMP_DTRCLOUD',s);seg=txt[s:e]
        oldb='      PARAMETER (A=2.0, B=2.2, C=1.0, PI=3.14159)';newb='      PARAMETER (A=2.0, B=1.05, C=1.0, PI=3.14159)';assert seg.count(oldb)==1
        seg=seg.replace(oldb,newb,1);txt=txt[:s]+seg+txt[e:]
    p.write_text(txt,encoding='latin-1')

def line_diffs(a,b):
    aa=a.read_text(encoding='latin-1').splitlines();bb=b.read_text(encoding='latin-1').splitlines();assert len(aa)==len(bb)
    return [(i+1,x,y) for i,(x,y) in enumerate(zip(aa,bb)) if x!=y]

def build_sources():
    for p in [Path('/tmp/os0'),Path('/tmp/data')]:
        if p.exists():shutil.rmtree(p)
    for a in ARMS:
        for p in [Path('/tmp')/f'os_{a}',Path('/tmp')/f'build_{a}',ROOTS[a]]:
            if p.exists():shutil.rmtree(p)
    run(['git','clone','-q','https://github.com/DSSAT/dssat-csm-os.git','/tmp/os0']);run(['git','-C','/tmp/os0','checkout','-q',OS_COMMIT])
    run(['git','clone','-q','https://github.com/DSSAT/dssat-csm-data.git','/tmp/data']);run(['git','-C','/tmp/data','checkout','-q',DATA_COMMIT])
    for a in ARMS:shutil.copytree('/tmp/os0',Path('/tmp')/f'os_{a}',symlinks=True)
    run(['python','research/dssat_dtr/dssat485/apply_extreme_dtt_tgro_patch.py','/tmp/os_H0TT'])
    for a,pv in PARAMS.items():patch_m15_arm(Path('/tmp')/f'os_{a}',a,*pv)
    dshape=line_diffs(Path('/tmp/os_M15_13P5/Weather/HMET.for'),Path('/tmp/os_R1_P05/Weather/HMET.for'))
    db=line_diffs(Path('/tmp/os_R1_P05/Weather/HMET.for'),Path('/tmp/os_R3_P05_B105/Weather/HMET.for'))
    if len(dshape)!=1 or '*R' not in dshape[0][1] or '*SQRT(R)' not in dshape[0][2]:raise RuntimeError(f'R1 source isolation failed {dshape}')
    if len(db)!=1 or 'B=2.2' not in db[0][1] or 'B=1.05' not in db[0][2]:raise RuntimeError(f'R3 B source isolation failed {db}')
    audit=[]
    for a in ARMS:audit.append({'arm':a,'HMET_sha256':sha(Path('/tmp')/f'os_{a}'/'Weather/HMET.for')})
    audit += [{'arm':'M15_13P5_vs_R1_P05','HMET_sha256':f'one_line_shape_diff_at_{dshape[0][0]}'},{'arm':'R1_P05_vs_R3_P05_B105','HMET_sha256':f'one_line_B_diff_at_{db[0][0]}'}]
    for a in ARMS:
        src=Path('/tmp')/f'os_{a}';bld=Path('/tmp')/f'build_{a}';dst=ROOTS[a]
        run(['cmake','-S',str(src),'-B',str(bld),'-DCMAKE_BUILD_TYPE=RELEASE',f'-DCMAKE_INSTALL_PREFIX={dst}'],quiet=True);run(['cmake','--build',str(bld),'--parallel','2'],quiet=True);run(['cmake','--install',str(bld)],quiet=True);shutil.copytree('/tmp/data',dst,dirs_exist_ok=True)
    return audit,dshape,db

def build_inputs():
    base.ARMS=ARMS;base.ROOTS=ROOTS;base.build_inputs();a=base.audit_shared()
    if not all(x['byte_identical_all_arms'] for x in a):raise RuntimeError('pre-SRAD input mismatch')
    for arm in ARMS:
        base.scale_srad(ROOTS[arm]/'Weather/SHIH1901.WTH',base.SRAD_FACTOR[2019]);base.scale_srad(ROOTS[arm]/'Weather/SHIH2001.WTH',base.SRAD_FACTOR[2020])
    a=base.audit_shared()
    if not all(x['byte_identical_all_arms'] for x in a):raise RuntimeError('post-SRAD input mismatch')
    return a

def crop():
    rows=[]
    for a in ARMS:
        subprocess.run(['sudo','rm','-rf','/DSSAT48'],check=True);subprocess.run(['sudo','ln','-s',str(ROOTS[a]),'/DSSAT48'],check=True);maize=ROOTS[a]/'Maize'
        for year,yy in ((2019,'19'),(2020,'20')):
            for j,tr in enumerate(('W1','W2','W3','W4'),1):
                case=f'SHIH{yy}{j:02d}'
                for fn in ('Summary.OUT','PlantGro.OUT','INFO.OUT','ERROR.OUT','WARNING.OUT'):
                    q=maize/fn
                    if q.exists():q.unlink()
                cp=subprocess.run(['../dscsm048','A',case+'.MZX'],cwd=maize,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                if cp.returncode!=0 or not (maize/'Summary.OUT').exists():raise RuntimeError(f'{a} {case} failed\n{cp.stdout[-3000:]}')
                z=base.parse_summary(maize/'Summary.OUT');pred=float(z['HWAM']);obs=float(base.OBS[(year,tr)])
                rows.append({'arm':a,'year':year,'treatment':tr,'obs':obs,'HWAM':pred,'error':pred-obs,'abs_error':abs(pred-obs),'ARE_pct':100*abs(pred-obs)/obs,'SRADA':float(z['SRADA'])})
    return rows

def metrics(rows):
    out=[]
    for a in ARMS:
        for period in (2019,2020,'ALL8'):
            q=[r for r in rows if r['arm']==a and (period=='ALL8' or r['year']==period)];e=[r['error'] for r in q];o=[r['obs'] for r in q]
            out.append({'arm':a,'period':period,'n':len(q),'RMSE_kg_ha':rmse(e),'RRMSE_pct':100*rmse(e)/mean(o),'MAE_kg_ha':mean([abs(x) for x in e]),'Bias_kg_ha':mean(e),'mean_HWAM_kg_ha':mean([r['HWAM'] for r in q])})
    return out
def all8(ms,a):return next(r for r in ms if r['arm']==a and str(r['period'])=='ALL8')
def reproduce(ms,rows):
    rec=[]
    for a,(er,err) in EXPECTED.items():
        z=all8(ms,a);ok=abs(z['RMSE_kg_ha']-er)<=.02 and abs(z['RRMSE_pct']-err)<=.0002;rec.append({'arm':a,'actual_RMSE':z['RMSE_kg_ha'],'actual_RRMSE':z['RRMSE_pct'],'PASS':ok})
    idx={(r['arm'],r['year'],r['treatment']):r for r in rows};eq=all(idx[('M15_13P5',y,t)]['HWAM']==idx[('R1_P05',y,t)]['HWAM'] for y in (2019,2020) for t in ('W1','W2','W3','W4'))
    rec.append({'arm':'R1_P05_treatment_HWAM_equals_M15_13P5','actual_RMSE':'','actual_RRMSE':'','PASS':eq})
    if not all(r['PASS'] for r in rec):raise RuntimeError('baseline reproduction failed '+json.dumps(rec))
    return rec

def contrasts(rows):
    I={(r['arm'],r['year'],r['treatment']):r for r in rows};out=[]
    for y in (2019,2020):
        for t in ('W1','W2','W3','W4'):
            a=I[('R1_P05',y,t)];v=I[('R3_P05_B105',y,t)];r8=I[('M15_13P8',y,t)]
            out.append({'year':y,'treatment':t,'obs':v['obs'],'R1_HWAM':a['HWAM'],'R3_HWAM':v['HWAM'],'M15_13P8_HWAM':r8['HWAM'],'R3_minus_R1_HWAM':v['HWAM']-a['HWAM'],'R3_abs_error':v['abs_error'],'R1_abs_error':a['abs_error'],'M15_13P8_abs_error':r8['abs_error'],'R3_win_vs_R1':v['abs_error']<a['abs_error'],'R3_win_vs_13P8':v['abs_error']<r8['abs_error']})
    return out

def main():
    if OUT.exists():shutil.rmtree(OUT)
    OUT.mkdir(parents=True);source,dshape,db=build_sources();shared=build_inputs();rows=crop();ms=metrics(rows);repro=reproduce(ms,rows);con=contrasts(rows)
    h=all8(ms,'H0TT');p5=all8(ms,'M15_13P5');p8=all8(ms,'M15_13P8');r1m=all8(ms,'R1_P05');r3=all8(ms,'R3_P05_B105');wins=sum(x['R3_win_vs_R1'] for x in con);wins8=sum(x['R3_win_vs_13P8'] for x in con)
    if r3['RRMSE_pct']<r1m['RRMSE_pct'] and r3['RRMSE_pct']<=p8['RRMSE_pct'] and wins>=4:classification='ROUND3_CROP_STRONG'
    elif r3['RRMSE_pct']<r1m['RRMSE_pct']:classification='ROUND3_CROP_PARTIAL'
    else:classification='ROUND3_NO_CROP_GAIN'
    write_csv(OUT/'source_audit.csv',source);write_csv(OUT/'shared_input_audit.csv',shared);write_csv(OUT/'crop_treatment_rows.csv',rows);write_csv(OUT/'crop_metrics.csv',ms);write_csv(OUT/'baseline_reproduction.csv',repro);write_csv(OUT/'treatment_contrasts.csv',con)
    manifest={'source_commit':OS_COMMIT,'data_commit':DATA_COMMIT,'parameters':{'DTRc':13.5,'alpha':6.407985379809223,'p':.5,'Bnight':1.05},'shared_input_gate':True,'R1_vs_R3_source_diff_lines':len(db),'baseline_reproduction_gate':True,'H0TT_RRMSE':h['RRMSE_pct'],'M15_13P5_RRMSE':p5['RRMSE_pct'],'M15_13P8_RRMSE':p8['RRMSE_pct'],'R1_P05_RRMSE':r1m['RRMSE_pct'],'R3_RRMSE':r3['RRMSE_pct'],'R3_change_vs_R1_pp':r3['RRMSE_pct']-r1m['RRMSE_pct'],'R3_change_vs_13P8_pp':r3['RRMSE_pct']-p8['RRMSE_pct'],'wins_vs_R1':wins,'wins_vs_13P8':wins8,'classification':classification}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    text=f'''# M15-V2 Round 3 crop propagation result

## Integrity

- Source `{OS_COMMIT}`; data `{DATA_COMMIT}`.
- Shared inputs byte-identical: **PASS**.
- M15_13P5 vs R1_P05 source: exactly **{len(dshape)}** shape line difference.
- R1_P05 vs R3_P05_B105 source: exactly **{len(db)}** nighttime-B line difference.
- Frozen baseline reproduction: **PASS**.

## ALL8 metrics

|Arm|RMSE kg/ha|RRMSE|MAE|Bias|Mean HWAM|
|---|---:|---:|---:|---:|---:|
'''
    for a in ARMS:
        z=all8(ms,a);text+=f"|{a}|{z['RMSE_kg_ha']:.3f}|{z['RRMSE_pct']:.6f}%|{z['MAE_kg_ha']:.3f}|{z['Bias_kg_ha']:+.3f}|{z['mean_HWAM_kg_ha']:.3f}|\n"
    text+=f'''
## Direct contrasts

- R3 vs R1 p=.5 RRMSE: **{r1m['RRMSE_pct']:.6f}% -> {r3['RRMSE_pct']:.6f}%** ({r3['RRMSE_pct']-r1m['RRMSE_pct']:+.6f} pp).
- R3 vs M15-13.8: **{r3['RRMSE_pct']-p8['RRMSE_pct']:+.6f} pp**.
- Treatment wins vs R1: **{wins}/8**; vs M15-13.8: **{wins8}/8**.

## Year RRMSE

|Arm|2019|2020|
|---|---:|---:|
'''
    for a in ARMS:
        y1=next(x for x in ms if x['arm']==a and str(x['period'])=='2019');y2=next(x for x in ms if x['arm']==a and str(x['period'])=='2020');text+=f"|{a}|{y1['RRMSE_pct']:.4f}%|{y2['RRMSE_pct']:.4f}%|\n"
    text+=f'''
## Prespecified classification

**{classification}**

Temperature parameters remain frozen regardless of crop classification.
'''
    (OUT/'README_M15_V2_ROUND3_CROP_PROPAGATION.md').write_text(text,encoding='utf-8');RESULT_CP.write_text(text,encoding='utf-8');print(text)
if __name__=='__main__':main()
