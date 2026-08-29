from pathlib import Path
from datetime import date
import shutil
import re
import csv
import subprocess
import json
import sys

repo = Path.cwd()
pristine = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/clean_M0')
out = repo / 'research/dssat_dtr/data/shihezi_real_case/soil_sloc_clean_m0_v5'
out.mkdir(parents=True, exist_ok=True)


def add_cultivar(root: Path):
    cul = next(root.rglob('MZCER048.CUL'))
    txt = cul.read_text(encoding='latin-1')
    row = (
        f"{'XY0066':6s} {'Xinyu 66':16s}     . {'IB0001':6s} "
        f"{104.7:5.1f} {1.824:5.3f} {957.2:5.1f} {671.0:5.1f} {15.82:5.2f} {42.97:5.2f}"
    )
    assert len(row) == 72, (len(row), repr(row))
    if 'XY0066' not in txt:
        cul.write_text(txt.rstrip('\r\n') + '\n' + row + '\n', encoding='latin-1')


SOIL = '''*Soils: Shihezi University Modern Water-saving Irrigation Key Experimental Station

*SHIH000100  SHIHEZI     -99     100 Guo2025 measured 0-100 cm profile
@SITE        COUNTRY          LAT     LONG SCS FAMILY
 Shihezi     China          44.3244  85.9964 -99
@ SCOM  SALB  SLU1  SLDR  SLRO  SLNF  SLPF  SMHB  SMPX  SMKE
    -99  0.15  6.00  0.50  60.0  1.00  1.00 IB001 IB001 IB001
@  SLB  SLMH  SLLL  SDUL  SSAT  SRGF  SSKS  SBDM  SLOC  SLCL  SLSI  SLCF  SLNI  SLHW  SLHB  SCEC  SADC
    20   -99 0.122 0.237 0.457  1.00   -99  1.51   -99 32.75 51.93   0.0   -99   -99   -99   -99   -99
    40   -99 0.136 0.264 0.425  0.85   -99  1.54   -99 31.52 54.11   0.0   -99   -99   -99   -99   -99
    60   -99 0.120 0.231 0.371  0.70   -99  1.59   -99 43.28 44.53   0.0   -99   -99   -99   -99   -99
    80   -99 0.113 0.214 0.346  0.55   -99  1.63   -99 30.21 60.74   0.0   -99   -99   -99   -99   -99
   100   -99 0.105 0.236 0.385  0.40   -99  1.61   -99 29.13 49.76   0.0   -99   -99   -99   -99   -99
'''


def write_soil(root: Path, slocs):
    p = root / 'Soil' / 'SH.SOL'
    p.write_text(SOIL, encoding='latin-1')
    lines = p.read_text(encoding='latin-1').splitlines()
    result = []
    active = False
    k = 0
    for line in lines:
        if line.startswith('@  SLB'):
            active = True
            result.append(line)
            continue
        if active and line.strip() and not line.startswith(('@', '*')) and k < 5:
            assert len(line) >= 102, (len(line), repr(line))
            old = line
            # DSSAT SOL layer fields are 6 chars wide. SLOC is field 9 => [48:54].
            line = line[:48] + f'{slocs[k]:6.3f}' + line[54:]
            assert len(line) == len(old)
            assert line[:48] == old[:48] and line[54:] == old[54:]
            k += 1
        result.append(line)
    assert k == 5
    p.write_text('\n'.join(result) + '\n', encoding='latin-1')
    return p


def write_weather(root: Path):
    src = repo / 'research/dssat_dtr/data/shihezi_real_case/power_daily/shihezi_power_2019_2020_wth_inputs.csv'
    rows = []
    with src.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if int(r['year']) == 2020:
                rows.append(r)
    wh = [
        '*WEATHER DATA : Shihezi Guo2025 provisional NASA POWER reconstruction',
        '',
        '@ INSI      LAT     LONG  ELEV   TAV   AMP REFHT WNDHT',
        '  SHIH   44.3244   85.9964   412   9.0  40.0  2.00  3.00',
        '@DATE  SRAD  TMAX  TMIN  RAIN',
    ]
    for r in rows:
        wh.append(
            f"20{int(r['doy']):03d} {float(r['SRAD_MJ_m2_d']):5.1f} "
            f"{float(r['TMAX_C']):5.1f} {float(r['TMIN_C']):5.1f} {float(r['RAIN_mm']):5.1f}"
        )
    wth = '\n'.join(wh) + '\n'
    p = root / 'Weather' / 'SHIH2001.WTH'
    p.write_text(wth, encoding='latin-1')
    # Frozen standalone run reports blank DATA PATH; provide the same file in cwd too.
    (root / 'Maize' / 'SHIH2001.WTH').write_text(wth, encoding='latin-1')
    return p


def yydoy(d: date):
    return f'{d.year % 100:02d}{d.timetuple().tm_yday:03d}'


def repl(txt, start, end, body):
    m = re.search(re.escape(start) + r'.*?(?=' + re.escape(end) + r')', txt, re.S)
    if not m:
        raise RuntimeError('missing ' + start)
    return txt[:m.start()] + body.rstrip() + '\n\n' + txt[m.end():]


def write_experiment(root: Path):
    template = (root / 'Maize' / 'UFGA8201.MZX').read_text(encoding='latin-1')
    x = template
    x = re.sub(
        r'^\*EXP\.DETAILS:.*$',
        '*EXP.DETAILS: SHIH2002MZ GUO2025 SHIHEZI 2020 W2 SLOC AUDIT',
        x,
        count=1,
        flags=re.M,
    )
    levels = [1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1]
    treat = (
        f'{1:3d}{1:1d} {0:1d} {0:1d} '
        + f'{"GUO2025 XINYU66 REAL":25s}'
        + ''.join(f'{v:3d}' for v in levels)
    )
    x = repl(
        x,
        '*TREATMENTS',
        '*CULTIVARS',
        '*TREATMENTS                        -------------FACTOR LEVELS------------\n'
        '@N R O C TNAME.................... CU FL SA IC MP MI MF MR MC MT ME MH SM\n'
        + treat,
    )
    x = repl(x, '*CULTIVARS', '*FIELDS', '*CULTIVARS\n@C CR INGENO CNAME\n 1 MZ XY0066 Xinyu 66 Guo2025')
    x = repl(
        x,
        '*FIELDS',
        '*INITIAL CONDITIONS',
        '''*FIELDS
@L ID_FIELD WSTA....  FLSA  FLOB  FLDT  FLDD  FLDS  FLST SLTX  SLDP  ID_SOIL    FLNAME
 1 SHIH0001 SHIH       -99     0 DR000     0     0 00000 -99    100  SHIH000100 Shihezi Guo2025
@L ...........XCRD ...........YCRD .....ELEV .............AREA .SLEN .FLWR .SLAS FLHST FHDUR
 1          44.3244        85.9964       412                 0     0     0     0   -99   -99''',
    )
    x = repl(
        x,
        '*INITIAL CONDITIONS',
        '*PLANTING DETAILS',
        '''*INITIAL CONDITIONS
@C   PCR ICDAT  ICRT  ICND  ICRN  ICRE  ICWD ICRES ICREN ICREP ICRIP ICRID ICNAME
 1    MZ 20125   100     0     1     1   -99     0     0     0     0     0 Guo2025 DUL assumption
@C  ICBL  SH2O  SNH4  SNO3
 1    20  .237    1.0    1.0
 1    40  .264    1.0    1.0
 1    60  .231    1.0    1.0
 1    80  .214    1.0    1.0
 1   100  .236    1.0    1.0''',
    )
    x = repl(
        x,
        '*PLANTING DETAILS',
        '*IRRIGATION AND WATER MANAGEMENT',
        '''*PLANTING DETAILS
@P PDATE EDATE  PPOP  PPOE  PLME  PLDS  PLRS  PLRD  PLDP  PLWT  PAGE  PENV  PLPH  SPRL                        PLNAME
 1 20126   -99  8.89  8.89     S     R    45     0     4   -99   -99   -99   -99     0                        Guo2025 derived density''',
    )

    irr_dates = [
        date(2020, 5, 5), date(2020, 6, 15), date(2020, 6, 23), date(2020, 7, 2), date(2020, 7, 9),
        date(2020, 7, 16), date(2020, 7, 23), date(2020, 7, 30), date(2020, 8, 10), date(2020, 8, 24),
    ]
    irr_vals = [52.5, 35, 35, 35, 78.75, 78.75, 78.75, 39.375, 39.375, 52.5]
    ir = [
        '*IRRIGATION AND WATER MANAGEMENT',
        '@I  EFIR  IDEP  ITHR  IEPT  IOFF  IAME  IAMT IRNAME',
        ' 1     1   -99   -99   -99   -99   -99   -99 Guo2025 W2',
        '@I IDATE  IROP IRVAL',
    ]
    for d, v in zip(irr_dates, irr_vals):
        ir.append(f' 1 {yydoy(d)} IR001 {v:6.2f}')
    x = repl(x, '*IRRIGATION AND WATER MANAGEMENT', '*FERTILIZERS (INORGANIC)', '\n'.join(ir))

    fert_dates = [
        date(2020, 5, 6), date(2020, 6, 15), date(2020, 6, 23), date(2020, 7, 2), date(2020, 7, 9),
        date(2020, 7, 16), date(2020, 7, 23), date(2020, 7, 30), date(2020, 8, 10), date(2020, 8, 24),
    ]
    fr = [
        '*FERTILIZERS (INORGANIC)',
        '@F FDATE  FMCD  FACD  FDEP  FAMN  FAMP  FAMK  FAMC  FAMO  FOCD FERNAME',
    ]
    for d in fert_dates:
        fr.append(f' 1 {yydoy(d)} FE005 AP001   5.0 {12.88:5.2f}   0.0   0.0   0.0   0.0   -99 N129 diagnostic')
    x = repl(x, '*FERTILIZERS (INORGANIC)', '*SIMULATION CONTROLS', '\n'.join(fr))

    sim = '''*SIMULATION CONTROLS
@N GENERAL     NYERS NREPS START SDATE RSEED SNAME.................... SMODEL
 1 GE              1     1     S 20125  2150 GUO2025 2020 W2 SLOC AUDIT
@N OPTIONS     WATER NITRO SYMBI PHOSP POTAS DISES  CHEM  TILL   CO2
 1 OP              Y     Y     N     N     N     N     N     N     M
@N METHODS     WTHER INCON LIGHT EVAPO INFIL PHOTO HYDRO NSWIT MESOM MESEV MESOL
 1 ME              M     M     E     R     S     R     R     1     G     R     2
@N MANAGEMENT  PLANT IRRIG FERTI RESID HARVS
 1 MA              R     R     R     N     M
@N OUTPUTS     FNAME OVVEW SUMRY FROPT GROUT CAOUT WAOUT NIOUT MIOUT DIOUT VBOSE CHOUT OPOUT FMOPT
 1 OU              N     Y     Y     1     Y     N     Y     Y     N     N     Y     N     Y     A

@  AUTOMATIC MANAGEMENT
@N PLANTING    PFRST PLAST PH2OL PH2OU PH2OD PSTMX PSTMN
 1 PL          20126 20126    40   100    30    40     5
@N IRRIGATION  IMDEP ITHRL ITHRU IROFF IMETH IRAMT IREFF
 1 IR             30    50   100 GS000 IR001    10     1
@N NITROGEN    NMDEP NMTHR NAMNT NCODE NAOFF
 1 NI             30    50    25 FE001 GS000
@N RESIDUES    RIPCN RTIME RIDEP
 1 RE              0     1    20
@N HARVEST     HFRST HLAST HPCNP HPCNR
 1 HA              0 20299   100     0'''
    m = re.search(r'\*SIMULATION CONTROLS.*?(?:\x1a|\Z)', x, re.S)
    if not m:
        raise RuntimeError('simulation controls missing')
    x = x[:m.start()] + sim + '\n\n\x1a\n'
    p = root / 'Maize' / 'SHIH2002.MZX'
    p.write_text(x, encoding='latin-1')
    return p


def parse_summary(path: Path):
    lines = path.read_text(errors='replace').splitlines()
    hi = next(i for i, l in enumerate(lines) if l.startswith('@') and 'HWAM' in l)
    h = lines[hi]
    d = next(l for l in lines[hi + 1:] if l.strip() and not l.startswith(('@', '!', '*')))
    names = h[1:].split()
    vals = d.split()
    idx = names.index('HWAM')
    return dict(zip(names[idx:], vals[-len(names[idx:]):]))


def parse_info_oc(txt: str):
    rows = []
    active = False
    for line in txt.splitlines():
        if 'LYR  cm    cm  frac  frac  frac  Grow g/cm3' in line:
            active = True
            continue
        if active:
            if not line.strip() and rows:
                break
            t = line.split()
            if t and t[0].isdigit() and len(t) >= 9:
                rows.append({'layer': int(t[0]), 'depth_cm': float(t[1]), 'OC_pct': float(t[8])})
    return rows


configs = {
    'LOWOM': [0.0861, 0.0818, 0.0733, 0.0758, 0.0593],
    'HIGHOM': [0.8614, 0.8179, 0.7332, 0.7581, 0.5928],
}
result = {}

for name, slocs in configs.items():
    root = Path('/tmp') / f'clean_v5_{name}'
    shutil.copytree(pristine, root)
    assert not list(root.rglob('DSSAT48.INP')), 'pristine copy unexpectedly contains DSSAT48.INP'
    add_cultivar(root)
    sol = write_soil(root, slocs)
    weather = write_weather(root)
    xfile = write_experiment(root)

    # Cache invariant immediately before the first DSSAT execution in this fresh copy.
    for p in root.rglob('DSSAT48.INP'):
        p.unlink()
    assert not list(root.rglob('DSSAT48.INP'))
    assert (root / 'Weather' / 'SHIH2001.WTH').exists()
    assert (root / 'Maize' / 'SHIH2001.WTH').exists()

    subprocess.run(['sudo', 'rm', '-rf', '/DSSAT48'], check=True)
    subprocess.run(['sudo', 'ln', '-s', str(root), '/DSSAT48'], check=True)
    wd = root / 'Maize'
    cp = subprocess.run(
        [str(root / 'dscsm048'), 'A', 'SHIH2002.MZX'],
        cwd=wd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if cp.returncode != 0:
        err = (wd / 'ERROR.OUT').read_text(errors='replace') if (wd / 'ERROR.OUT').exists() else ''
        warn = (wd / 'WARNING.OUT').read_text(errors='replace') if (wd / 'WARNING.OUT').exists() else ''
        raise RuntimeError(name + ' failed\n' + cp.stdout + '\n' + err + '\n' + warn)

    z = parse_summary(wd / 'Summary.OUT')
    info = (wd / 'INFO.OUT').read_text(errors='replace')
    result[name] = {
        'intended_SLOC_pct': slocs,
        'model_read_OC': parse_info_oc(info),
        'HWAM': float(z['HWAM']),
        'CWAM': z.get('CWAM'),
        'NI#M': z.get('NI#M'),
        'NICM': z.get('NICM'),
        'NUCM': z.get('NUCM'),
        'NLCM': z.get('NLCM'),
        'NMINC': z.get('NMINC'),
        'DSSAT48_INP_exists_after_run': bool(list(root.rglob('DSSAT48.INP'))),
    }

    shutil.copy2(sol, out / f'{name}_SH.SOL')
    shutil.copy2(weather, out / f'{name}_SHIH2001.WTH')
    shutil.copy2(xfile, out / f'{name}_SHIH2002.MZX')
    shutil.copy2(wd / 'INFO.OUT', out / f'{name}_INFO.OUT')
    shutil.copy2(wd / 'Summary.OUT', out / f'{name}_Summary.OUT')
    for p in root.rglob('DSSAT48.INP'):
        shutil.copy2(p, out / f'{name}_DSSAT48.INP')
        break
    for fn in ['SoilNi.OUT', 'PlantN.OUT', 'SoilNBalSum.OUT']:
        p = wd / fn
        if p.exists():
            shutil.copy2(p, out / f'{name}_{fn}')

(out / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
lo = result['LOWOM']
hi = result['HIGHOM']
md = [
    '# Shihezi clean M0-only SLOC audit V5',
    '',
    '**Design:** LOWOM and HIGHOM start from the same pristine frozen M0 installation before any DSSAT execution. No inherited DSSAT48.INP exists. The identical WTH is placed in both Weather/ and Maize/ to satisfy frozen standalone path resolution. Only fixed-width SLOC differs.',
    '',
    f"- LOWOM intended SLOC: `{lo['intended_SLOC_pct']}`; model-read OC: `{lo['model_read_OC']}`; HWAM **{lo['HWAM']:.0f} kg/ha**; NICM `{lo['NICM']}`.",
    f"- HIGHOM intended SLOC: `{hi['intended_SLOC_pct']}`; model-read OC: `{hi['model_read_OC']}`; HWAM **{hi['HWAM']:.0f} kg/ha**; NICM `{hi['NICM']}`.",
    f"- HIGHOM minus LOWOM HWAM: **{hi['HWAM'] - lo['HWAM']:+.0f} kg/ha**.",
    '',
    'Decision rule: if model-read OC differs in the intended direction, prior non-propagation was due stale/preprocessed runtime input and this is a valid OM comparison. If model-read OC remains identical, close the OM engineering line and proceed to plastic mulch / first-irrigation reconstruction.',
]
(out / 'README_CLEAN_M0_SLOC_V5.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print('\n'.join(md))
