#!/usr/bin/env python3
"""Result-first Shihezi screen for M15-13.8 + joint hourly crop response.

Hard gate: same Guo 2025 Shihezi 8-treatment chain used by the frozen lower-bound
audit. The new model must beat locked M15-13.8 RMSE=2656.200011 kg/ha.
KRT=0 for every patched mode must reproduce the locked M15 treatment vector.
"""
from __future__ import annotations
import csv, importlib.util, math, os, shutil, subprocess
from pathlib import Path

ROOT=Path('research/dssat_dtr')
BASE_SCRIPT=ROOT/'scripts/shihezi_dtrc_fourlevel_ablation.py'
spec=importlib.util.spec_from_file_location('oldm',BASE_SCRIPT)
m=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(m)

OUT=ROOT/'data/shihezi_real_case/joint_thermal_crop_v1'
DTRC=13.8; ALPHA=6.7498
LOCKED_RMSE=2656.20001129433
LOCKED_H0_RMSE=2977.2722205065497
KGRID=[0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0]
ARMS=['BASE13P8','PRFT13P8','RGFIL13P8','BOTH13P8']
MODES={'PRFT13P8':'prft','RGFIL13P8':'rgfill','BOTH13P8':'both'}
ROOTS={a:Path('/tmp')/f'run_{a}' for a in ARMS}

m.ARMS=ARMS; m.ROOTS=ROOTS


def run(cmd,cwd=None,env=None,quiet=False):
    kw={'cwd':cwd,'env':env,'check':True,'text':True}
    if quiet: kw.update(stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    return subprocess.run(cmd,**kw)


def build():
    for p in [Path('/tmp/os_joint0'),Path('/tmp/data_joint')]:
        if p.exists(): shutil.rmtree(p)
    for a in ARMS:
        for p in [Path('/tmp')/f'os_joint_{a}',Path('/tmp')/f'build_joint_{a}',ROOTS[a]]:
            if p.exists(): shutil.rmtree(p)
    run(['git','clone','-q','https://github.com/DSSAT/dssat-csm-os.git','/tmp/os_joint0'])
    run(['git','-C','/tmp/os_joint0','checkout','-q','0b91373806786b600d89ccfcfff78fa2f82cb26b'])
    run(['git','clone','-q','https://github.com/DSSAT/dssat-csm-data.git','/tmp/data_joint'])
    run(['git','-C','/tmp/data_joint','checkout','-q','79cb5db71bbca186add92a6a9695866a09c8b51d'])
    for a in ARMS:
        src=Path('/tmp')/f'os_joint_{a}'
        shutil.copytree('/tmp/os_joint0',src,symlinks=True)
        run(['python',str(ROOT/'dssat485/apply_m15_htemp_patch.py'),str(src)])
        run(['python',str(ROOT/'dssat485/apply_m15_extreme_dtt_patch.py'),str(src)])
        hp=src/'Weather/HMET.for'; txt=hp.read_text(encoding='latin-1')
        old='PARAMETER (DTRC=14.8, ALPHA=7.8094)'
        assert txt.count(old)==1
        txt=txt.replace(old,f'PARAMETER (DTRC={DTRC:.1f}, ALPHA={ALPHA:.4f})',1)
        hp.write_text(txt,encoding='latin-1')
        if a in MODES:
            run(['python',str(ROOT/'dssat485/apply_joint_hourly_crop_response.py'),str(src),'--mode',MODES[a]])
        bld=Path('/tmp')/f'build_joint_{a}'; dst=ROOTS[a]
        run(['cmake','-S',str(src),'-B',str(bld),'-DCMAKE_BUILD_TYPE=RELEASE',f'-DCMAKE_INSTALL_PREFIX={dst}'],quiet=True)
        run(['cmake','--build',str(bld),'--parallel','2'],quiet=True)
        run(['cmake','--install',str(bld)],quiet=True)
        shutil.copytree('/tmp/data_joint',dst,dirs_exist_ok=True)


def prepare_inputs():
    m.build_inputs()
    pre=m.audit_shared()
    if not all(x['byte_identical_all_arms'] for x in pre): raise RuntimeError('pre-SRAD shared input gate failed')
    for a in ARMS:
        m.scale_srad(ROOTS[a]/'Weather/SHIH1901.WTH',m.SRAD_FACTOR[2019])
        m.scale_srad(ROOTS[a]/'Weather/SHIH2001.WTH',m.SRAD_FACTOR[2020])
    post=m.audit_shared()
    if not all(x['byte_identical_all_arms'] for x in post): raise RuntimeError('post-SRAD shared input gate failed')
    return pre,post


def one_case(arm,krt,year,yy,j,tr):
    root=ROOTS[arm]; maize=root/'Maize'
    subprocess.run(['sudo','rm','-rf','/DSSAT48'],check=True)
    subprocess.run(['sudo','ln','-s',str(root),'/DSSAT48'],check=True)
    case=f'SHIH{yy}{j:02d}'
    for fn in ('Summary.OUT','PlantGro.OUT','INFO.OUT','ERROR.OUT','WARNING.OUT'):
        p=maize/fn
        if p.exists(): p.unlink()
    env=os.environ.copy(); env['DSSAT_KRT']=f'{krt:.6f}'
    cp=subprocess.run(['../dscsm048','A',case+'.MZX'],cwd=maize,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if cp.returncode!=0 or not (maize/'Summary.OUT').exists():
        raise RuntimeError(f'{arm} KRT={krt} {case} failed\n{cp.stdout[-3000:]}')
    z=m.parse_summary(maize/'Summary.OUT'); pred=float(z['HWAM']); obs=m.OBS[(year,tr)]
    return {'arm':arm,'mode':MODES.get(arm,'m15_13p8'),'KRT':krt,'year':year,'treatment':tr,
            'obs':obs,'HWAM':pred,'error':pred-obs,'abs_error':abs(pred-obs),'SRADA':float(z['SRADA'])}


def metrics(rows):
    out=[]
    keys=sorted(set((r['arm'],r['KRT']) for r in rows))
    for arm,k in keys:
        q=[r for r in rows if r['arm']==arm and r['KRT']==k]
        for period in (2019,2020,'ALL8'):
            z=[r for r in q if period=='ALL8' or r['year']==period]
            e=[r['error'] for r in z]
            rm=math.sqrt(sum(x*x for x in e)/len(e)); mae=sum(abs(x) for x in e)/len(e); bias=sum(e)/len(e)
            out.append({'arm':arm,'mode':MODES.get(arm,'m15_13p8'),'KRT':k,'period':period,
                        'RMSE_kg_ha':rm,'MAE_kg_ha':mae,'Bias_kg_ha':bias,
                        'improvement_vs_M15_13p8_pct':100*(LOCKED_RMSE-rm)/LOCKED_RMSE,
                        'improvement_vs_H0TT_pct':100*(LOCKED_H0_RMSE-rm)/LOCKED_H0_RMSE})
    return out


def write_csv(path,rows):
    if not rows:return
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    build(); pre,post=prepare_inputs()
    rows=[]
    for arm in ARMS:
        grid=[0.0] if arm=='BASE13P8' else KGRID
        for k in grid:
            for year,yy in ((2019,'19'),(2020,'20')):
                for j,tr in enumerate(('W1','W2','W3','W4'),1):
                    rows.append(one_case(arm,k,year,yy,j,tr))
    met=metrics(rows)
    base_vec=[r['HWAM'] for r in rows if r['arm']=='BASE13P8' and r['KRT']==0]
    base_rmse=next(r['RMSE_kg_ha'] for r in met if r['arm']=='BASE13P8' and r['period']=='ALL8')
    baseline_close=abs(base_rmse-LOCKED_RMSE)<1e-6
    neutral={}
    for arm in MODES:
        vec=[r['HWAM'] for r in rows if r['arm']==arm and r['KRT']==0]
        neutral[arm]=(vec==base_vec)
    candidates=[r for r in met if r['arm']!='BASE13P8' and r['period']=='ALL8' and r['KRT']>0]
    best=min(candidates,key=lambda r:r['RMSE_kg_ha'])
    passed=baseline_close and all(neutral.values()) and best['RMSE_kg_ha']<LOCKED_RMSE
    write_csv(OUT/'treatment_rows.csv',rows); write_csv(OUT/'metrics.csv',met)
    write_csv(OUT/'shared_input_audit_pre_srad.csv',pre); write_csv(OUT/'shared_input_audit_post_srad.csv',post)
    lines=['# Shihezi joint thermal-crop V1','',
           f'- Locked H0TT RMSE: {LOCKED_H0_RMSE:.6f} kg/ha',
           f'- Locked M15-13.8 RMSE: {LOCKED_RMSE:.6f} kg/ha',
           f'- Rebuilt M15-13.8 RMSE: {base_rmse:.6f} kg/ha; closure: {"PASS" if baseline_close else "FAIL"}',
           f'- Neutral KRT=0 closure: {neutral}', '',
           '|Mode|KRT|ALL8 RMSE|2019 RMSE|2020 RMSE|vs M15|vs H0TT|','|---|---:|---:|---:|---:|---:|---:|']
    for arm in MODES:
        for k in KGRID:
            a=next(r for r in met if r['arm']==arm and r['KRT']==k and r['period']=='ALL8')
            y19=next(r for r in met if r['arm']==arm and r['KRT']==k and r['period']==2019)
            y20=next(r for r in met if r['arm']==arm and r['KRT']==k and r['period']==2020)
            lines.append(f"|{a['mode']}|{k:.1f}|{a['RMSE_kg_ha']:.2f}|{y19['RMSE_kg_ha']:.2f}|{y20['RMSE_kg_ha']:.2f}|{a['improvement_vs_M15_13p8_pct']:+.2f}%|{a['improvement_vs_H0TT_pct']:+.2f}%|")
    lines += ['',f"## Best: {best['mode']} KRT={best['KRT']:.1f}",
              f"RMSE={best['RMSE_kg_ha']:.6f} kg/ha; improvement vs M15-13.8={best['improvement_vs_M15_13p8_pct']:+.3f}%; vs H0TT={best['improvement_vs_H0TT_pct']:+.3f}%.",
              f"HARD_GATE={'PASS' if passed else 'FAIL'}",'']
    (OUT/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    print('\n'.join(lines))
    if not baseline_close: raise SystemExit('locked M15-13.8 rebuild closure failed')
    if not all(neutral.values()): raise SystemExit('KRT=0 neutral closure failed')

if __name__=='__main__': main()
