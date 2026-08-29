from pathlib import Path
import csv, json, math, re, shutil, subprocess

ARMS = ['M0', 'H0TT', 'M15TT']
ROOTS = {a: Path('/tmp') / f'run_{a}' for a in ARMS}
OBS = {
    (2019, 'W1'): 9250, (2019, 'W2'): 10725, (2019, 'W3'): 12490, (2019, 'W4'): 12030,
    (2020, 'W1'): 9275, (2020, 'W2'): 11100, (2020, 'W3'): 12030, (2020, 'W4'): 11595,
}
OUT = Path('research/dssat_dtr/data/shihezi_real_case/three_arm_srad_n_yield_matrix')
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

# Guo Table 2-1 measured profile. Organic matter g/kg is converted to OC% by /1.724/10.
HYD = [
    (20, 0.122, 0.237, 0.457, 1.00, 1.51, 0.0861, 32.75, 51.93),
    (40, 0.136, 0.264, 0.425, 0.85, 1.54, 0.0818, 31.52, 54.11),
    (60, 0.120, 0.231, 0.371, 0.70, 1.59, 0.0733, 43.28, 44.53),
    (80, 0.113, 0.214, 0.346, 0.55, 1.63, 0.0758, 30.21, 60.74),
    (100, 0.105, 0.236, 0.385, 0.40, 1.61, 0.0593, 29.13, 49.76),
]


def soil_text():
    lines = [
        '*Soils: Shihezi University Modern Water-saving Irrigation Key Experimental Station', '',
        '*SHIH000100  SHIHEZI     -99     100 Guo Table 2-1 measured profile',
        '@SITE        COUNTRY          LAT     LONG SCS FAMILY',
        f" {'Shihezi':<11}{'China':<14}{44.324:8.3f}{85.996:9.3f} -99",
        '@ SCOM  SALB  SLU1  SLDR  SLRO  SLNF  SLPF  SMHB  SMPX  SMKE',
        '    -9  0.15   6.0  0.50  60.0  1.00  1.00 IB001 IB001 IB001',
        '@  SLB  SLMH  SLLL  SDUL  SSAT  SRGF  SSKS  SBDM  SLOC  SLCL  SLSI  SLCF  SLNI  SLHW  SLHB  SCEC  SADC',
    ]
    for dep, ll, dul, sat, rgf, bd, oc, clay, silt in HYD:
        lines.append(
            f"{dep:6d}{'-99':>6}{ll:6.3f}{dul:6.3f}{sat:6.3f}{rgf:6.3f}"
            f"{'-99':>6}{bd:6.2f}{oc:6.3f}{clay:6.2f}{silt:6.2f}{0.0:6.1f}"
            f"{'-99':>6}{'-99':>6}{'-99':>6}{'-99':>6}{'-99':>6}"
        )
    return '\n'.join(lines) + '\n'


for a, root in ROOTS.items():
    (root / 'Soil' / 'SH.SOL').write_text(soil_text(), encoding='latin-1')

# Gate: all shared input files must be byte-identical before scenario edits.
shared = ['Soil/SH.SOL', 'Weather/SHIH1901.WTH', 'Weather/SHIH2001.WTH', 'Genotype/MZCER048.CUL']
shared += [f'Maize/SHIH{yy}{j:02d}.MZX' for yy in ('19', '20') for j in range(1, 5)]
for rel in shared:
    b = [(ROOTS[a] / rel).read_bytes() for a in ARMS]
    if not (b[0] == b[1] == b[2]):
        raise RuntimeError('shared input differs before treatment: ' + rel)

# Prespecified common-input scenarios. These are NOT selected by M15 performance.
# N129 is a same-station Xinyu66 proxy: 280 kg urea/ha * 46% N = 128.8 kg N/ha (2021-22 source).
# N193 is retained only as the previously audited upper robustness bracket.
SCENARIOS = [
    ('RAW_N_OFF', False, None),
    ('SRAD19P8_N_OFF', True, None),
    ('RAW_N129_STAGE', False, 128.8),
    ('SRAD19P8_N129_STAGE', True, 128.8),
    ('SRAD19P8_N193_STAGE', True, 193.2),
]
SRAD_FACTOR = {2019: 19.8 / 23.3, 2020: 19.8 / 24.2}
STAGE_COUNTS = [1, 3, 3, 2, 1]
STAGE_SHARES = [0.10, 0.20, 0.45, 0.15, 0.10]

# Save source files once, then restore before every scenario.
orig = {}
for a, root in ROOTS.items():
    for rel in shared:
        orig[(a, rel)] = (root / rel).read_bytes()


def restore():
    for (a, rel), data in orig.items():
        (ROOTS[a] / rel).write_bytes(data)
    for a, root in ROOTS.items():
        (root / 'Soil' / 'SH.SOL').write_text(soil_text(), encoding='latin-1')
        for p in root.rglob('DSSAT48.INP'):
            p.unlink()


def scale_srad(path, factor):
    out = []
    n = 0
    for raw in path.read_text(encoding='latin-1').splitlines():
        z = raw.split()
        if len(z) >= 5 and z[0].isdigit() and len(z[0]) == 5:
            dt, sr, tx, tn, rn = z[:5]
            raw = f'{dt:>5s}{float(sr)*factor:6.1f}{float(tx):6.1f}{float(tn):6.1f}{float(rn):6.1f}'
            n += 1
        out.append(raw)
    if not n:
        raise RuntimeError('no weather rows: ' + str(path))
    path.write_text('\n'.join(out) + '\n', encoding='latin-1')


def replace_section(txt, start, end, body):
    m = re.search(re.escape(start) + r'.*?(?=' + re.escape(end) + r')', txt, re.S)
    if not m:
        raise RuntimeError('missing section ' + start)
    return txt[:m.start()] + body.rstrip() + '\n\n' + txt[m.end():]


def irrigation_dates(txt):
    m = re.search(r'\*IRRIGATION AND WATER MANAGEMENT.*?(?=\*FERTILIZERS \(INORGANIC\))', txt, re.S)
    if not m:
        raise RuntimeError('irrigation section missing')
    dates = []
    for ln in m.group(0).splitlines():
        z = ln.split()
        if len(z) >= 3 and re.fullmatch(r'\d{5}', z[0]) and z[1].startswith('IR'):
            dates.append(z[0])
    if len(dates) != 10:
        raise RuntimeError(f'expected 10 irrigation dates, got {dates}')
    return dates


def apply_stage_n(xfile, total_n):
    txt = xfile.read_text(encoding='latin-1')
    old = '  1  1  0  1  1  1  0  0  0  0  0  0  1'
    new = '  1  1  0  1  1  1  1  0  0  0  0  0  1'
    if old not in txt:
        raise RuntimeError('MF=0 factor row missing: ' + xfile.name)
    txt = txt.replace(old, new, 1)
    dates = irrigation_dates(txt)

    # Same-station practice proxy: 20% urea-N basal; remaining 80% is fertigated
    # across growth stages using the published 10/20/45/15/10 stage distribution.
    basal = total_n * 0.20
    fert = total_n * 0.80
    amounts = []
    for share, count in zip(STAGE_SHARES, STAGE_COUNTS):
        amounts.extend([fert * share / count] * count)
    if len(amounts) != 10 or abs(basal + sum(amounts) - total_n) > 1e-6:
        raise RuntimeError('N allocation arithmetic failed')

    rows = ['*FERTILIZERS (INORGANIC)',
            '@F FDATE  FMCD  FACD  FDEP  FAMN  FAMP  FAMK  FAMC  FAMO  FOCD FERNAME']
    rows.append(f' 1 {dates[0]} FE005 AP001    5 {basal:6.2f}   0.0   0.0   0.0   0.0   -99 basal_proxy')
    for d, amt in zip(dates, amounts):
        rows.append(f' 1 {d} FE005 AP001    5 {amt:6.2f}   0.0   0.0   0.0   0.0   -99 stage_proxy')
    txt = replace_section(txt, '*FERTILIZERS (INORGANIC)', '*SIMULATION CONTROLS', '\n'.join(rows))
    txt = txt.replace(' 1 OP              Y     N     N     N     N     N     N     N     M',
                      ' 1 OP              Y     Y     N     N     N     N     N     N     M')
    txt = txt.replace(' 1 MA              R     R     N     N     M',
                      ' 1 MA              R     R     R     N     M')
    xfile.write_text(txt, encoding='latin-1')
    return basal, amounts


def parse_summary(path):
    ls = path.read_text(errors='replace').splitlines()
    hi = next(i for i, l in enumerate(ls) if l.startswith('@') and 'RUNNO' in l and 'HWAM' in l)
    h = ls[hi]
    d = next(l for l in ls[hi+1:] if l.strip() and not l.startswith(('@', '!', '*')))
    names = h[1:].split(); vals = d.split(); idx = names.index('HWAM'); tail = names[idx:]
    return dict(zip(tail, vals[-len(tail):]))


rows = []
input_audit = []
try:
    for scenario, use_srad, total_n in SCENARIOS:
        restore()
        for a, root in ROOTS.items():
            if use_srad:
                scale_srad(root / 'Weather' / 'SHIH1901.WTH', SRAD_FACTOR[2019])
                scale_srad(root / 'Weather' / 'SHIH2001.WTH', SRAD_FACTOR[2020])
            if total_n is not None:
                for yy in ('19', '20'):
                    for j in range(1, 5):
                        xf = root / 'Maize' / f'SHIH{yy}{j:02d}.MZX'
                        basal, amts = apply_stage_n(xf, total_n)
                        input_audit.append({'scenario': scenario, 'arm': a, 'file': xf.name,
                                            'total_N': total_n, 'basal_N': basal,
                                            'fertigation_N': sum(amts)})

        # After common scenario transformation, non-temperature inputs must still be identical across arms.
        for rel in shared:
            b = [(ROOTS[a] / rel).read_bytes() for a in ARMS]
            if not (b[0] == b[1] == b[2]):
                raise RuntimeError(f'{scenario}: cross-arm common input difference: {rel}')

        for a, root in ROOTS.items():
            subprocess.run(['sudo', 'rm', '-rf', '/DSSAT48'], check=True)
            subprocess.run(['sudo', 'ln', '-s', str(root), '/DSSAT48'], check=True)
            maize = root / 'Maize'
            for year, yy in ((2019, '19'), (2020, '20')):
                for j, tr in enumerate(('W1', 'W2', 'W3', 'W4'), 1):
                    case = f'SHIH{yy}{j:02d}'
                    for fn in ('Summary.OUT', 'PlantGro.OUT', 'INFO.OUT', 'ERROR.OUT', 'WARNING.OUT'):
                        p = maize / fn
                        if p.exists(): p.unlink()
                    cp = subprocess.run(['../dscsm048', 'A', case + '.MZX'], cwd=maize,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    if cp.returncode != 0 or not (maize / 'Summary.OUT').exists():
                        raise RuntimeError(f'{scenario} {a} {case} failed\n{cp.stdout[-2500:]}')
                    z = parse_summary(maize / 'Summary.OUT')
                    pred = float(z['HWAM']); obs = OBS[year, tr]
                    rows.append({'scenario': scenario, 'arm': a, 'year': year, 'treatment': tr,
                                 'obs': obs, 'HWAM': pred, 'error': pred - obs,
                                 'abs_error': abs(pred - obs), 'ARE_pct': abs(pred - obs) / obs * 100,
                                 'ADAT': z.get('ADAT', ''), 'MDAT': z.get('MDAT', ''),
                                 'SRADA': float(z['SRADA']), 'PRCP': float(z['PRCP']),
                                 'NICM': z.get('NICM', ''), 'NUCM': z.get('NUCM', '')})
finally:
    restore()

metrics = []
for scenario, _, _ in SCENARIOS:
    for arm in ARMS:
        for year in (2019, 2020):
            q = [r for r in rows if r['scenario'] == scenario and r['arm'] == arm and r['year'] == year]
            err = [r['error'] for r in q]; obs = [r['obs'] for r in q]
            rmse = math.sqrt(sum(e*e for e in err) / len(err)); mean_obs = sum(obs) / len(obs)
            metrics.append({'scenario': scenario, 'arm': arm, 'year': year,
                            'RMSE_kg_ha': rmse, 'RRMSE_pct': 100 * rmse / mean_obs,
                            'MAE_kg_ha': sum(abs(e) for e in err) / len(err),
                            'Bias_kg_ha': sum(err) / len(err),
                            'mean_HWAM': sum(r['HWAM'] for r in q) / len(q),
                            'mean_SRADA': sum(r['SRADA'] for r in q) / len(q)})
        q = [r for r in rows if r['scenario'] == scenario and r['arm'] == arm]
        err = [r['error'] for r in q]; obs = [r['obs'] for r in q]
        rmse = math.sqrt(sum(e*e for e in err) / len(err)); mean_obs = sum(obs) / len(obs)
        metrics.append({'scenario': scenario, 'arm': arm, 'year': 'ALL8',
                        'RMSE_kg_ha': rmse, 'RRMSE_pct': 100 * rmse / mean_obs,
                        'MAE_kg_ha': sum(abs(e) for e in err) / len(err),
                        'Bias_kg_ha': sum(err) / len(err),
                        'mean_HWAM': sum(r['HWAM'] for r in q) / len(q),
                        'mean_SRADA': sum(r['SRADA'] for r in q) / len(q)})

M = {(m['scenario'], m['arm'], str(m['year'])): m for m in metrics}
contrasts = []
for scenario, _, _ in SCENARIOS:
    for year in ('2019', '2020', 'ALL8'):
        m0 = M[scenario, 'M0', year]; h0 = M[scenario, 'H0TT', year]; m15 = M[scenario, 'M15TT', year]
        contrasts.append({
            'scenario': scenario, 'year': year,
            'M0_RRMSE': m0['RRMSE_pct'], 'H0TT_RRMSE': h0['RRMSE_pct'], 'M15TT_RRMSE': m15['RRMSE_pct'],
            'H0TT_minus_M0_pp': h0['RRMSE_pct'] - m0['RRMSE_pct'],
            'M15TT_minus_M0_pp': m15['RRMSE_pct'] - m0['RRMSE_pct'],
            'M15TT_minus_H0TT_pp': m15['RRMSE_pct'] - h0['RRMSE_pct'],
            'M15TT_rel_improve_vs_M0_pct': 100 * (m0['RRMSE_pct'] - m15['RRMSE_pct']) / m0['RRMSE_pct'],
        })

wins = []
for scenario, _, _ in SCENARIOS:
    q = [r for r in rows if r['scenario'] == scenario]
    by = {(r['year'], r['treatment'], r['arm']): r for r in q}
    wins_m0 = sum(by[y,t,'M15TT']['abs_error'] < by[y,t,'M0']['abs_error'] for y in (2019,2020) for t in ('W1','W2','W3','W4'))
    wins_h0 = sum(by[y,t,'M15TT']['abs_error'] < by[y,t,'H0TT']['abs_error'] for y in (2019,2020) for t in ('W1','W2','W3','W4'))
    wins.append({'scenario': scenario, 'M15_better_abs_error_vs_M0_of8': wins_m0,
                 'M15_better_abs_error_vs_H0TT_of8': wins_h0})

for name, data in [('treatment_rows.csv', rows), ('metrics.csv', metrics), ('contrasts.csv', contrasts),
                   ('input_audit.csv', input_audit), ('wins.csv', wins)]:
    if data:
        with (OUT / name).open('w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)

md = [
    '# Shihezi three-arm SRAD x N yield-accuracy matrix', '',
    'Purpose: test whether the frozen M15 temperature correction improves crop-output accuracy after correcting major shared-input gaps. No common input is selected by M15 performance.', '',
    'Temperature evidence is already frozen independently: M15 reduced May-Sep hourly RMSE 2.9469 -> 2.8241 C (4.17%); on DTR>=15 C days 5.1215 -> 4.6783 C (8.65%), with bias +1.2167 -> +0.3784 C.', '',
    '## Yield RRMSE by common-input scenario', '',
    '|Scenario|Period|M0|H0TT|M15TT|M15-M0 pp|M15-H0 pp|M15 relative improvement vs M0|',
    '|---|---|---:|---:|---:|---:|---:|---:|'
]
for c in contrasts:
    md.append(f"|{c['scenario']}|{c['year']}|{c['M0_RRMSE']:.3f}|{c['H0TT_RRMSE']:.3f}|{c['M15TT_RRMSE']:.3f}|{c['M15TT_minus_M0_pp']:+.3f}|{c['M15TT_minus_H0TT_pp']:+.3f}|{c['M15TT_rel_improve_vs_M0_pct']:+.2f}%|")
md += ['', '## Paired treatment-year wins', '', '|Scenario|M15 better than M0|M15 better than H0TT|', '|---|---:|---:|']
for w in wins:
    md.append(f"|{w['scenario']}|{w['M15_better_abs_error_vs_M0_of8']}/8|{w['M15_better_abs_error_vs_H0TT_of8']}/8|")
md += ['', 'Interpretation rule:',
       '- Temperature advantage is judged only from the independent hourly validation and is not re-tuned here.',
       '- Yield advantage is supported only if M15TT lowers error under the same shared inputs. H0TT is retained to separate the generic hourly/DTT-path effect from the specific M15 correction.',
       '- N129/N193 cases are robustness/proxy scenarios because exact 2019-2020 fertilizer and initial mineral N were not reported in Guo Chapter 2; they cannot be called the exact historical field input.',
       '- If M15TT does not outperform M0/H0TT in yield, that result must be reported rather than tuned away.']
(OUT / 'README_THREE_ARM_SRAD_N_YIELD_MATRIX.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
Path('research/dssat_dtr/CHECKPOINT_20260829_THREE_ARM_YIELD_ADVANTAGE.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print('\n'.join(md))
