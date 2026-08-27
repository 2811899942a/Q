#!/usr/bin/env python3
"""Copy a SWAT TxtInOut folder and write selected best parameters for validation runs."""
import argparse
import re
import shutil
from pathlib import Path


def replace_param_line(path, param, value, relative=None):
    text = path.read_text(errors='ignore').splitlines()
    new_lines = []
    changed = 0
    pat = re.compile(r'^(\s*)([-+0-9.Ee]+)(.*\|\s*' + re.escape(param) + r'\b.*)$')
    for line in text:
        m = pat.match(line)
        if m:
            old = float(m.group(2))
            new = old * (1 + relative) if relative is not None else value
            line = f"{m.group(1)}{new:16.6f}{m.group(3)}"
            changed += 1
        new_lines.append(line)
    if changed:
        path.write_text('\n'.join(new_lines) + '\n')
    return changed


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--src', required=True, help='source TxtInOut')
    p.add_argument('--dst', required=True, help='destination TxtInOut')
    p.add_argument('--cn2-rel', type=float, required=True, help='relative value, e.g. -0.115 means multiply by 0.885')
    p.add_argument('--alpha-bf', type=float, required=True)
    p.add_argument('--gw-delay', type=float, required=True)
    p.add_argument('--gwqmn', type=float, required=True)
    p.add_argument('--esco', type=float, required=True)
    p.add_argument('--ch-n2', type=float, required=True)
    p.add_argument('--ch-k2', type=float, required=True)
    p.add_argument('--swat-exe')
    args = p.parse_args()
    src, dst = Path(args.src), Path(args.dst)
    if dst.exists():
        raise FileExistsError(f'destination exists: {dst}')
    shutil.copytree(src, dst)
    counts = {}
    for f in dst.glob('*.mgt'):
        counts[str(f)] = replace_param_line(f, 'CN2', None, relative=args.cn2_rel)
    for f in dst.glob('*.gw'):
        replace_param_line(f, 'ALPHA_BF', args.alpha_bf)
        replace_param_line(f, 'GW_DELAY', args.gw_delay)
        replace_param_line(f, 'GWQMN', args.gwqmn)
    for f in dst.glob('*.hru'):
        replace_param_line(f, 'ESCO', args.esco)
    for f in dst.glob('*.rte'):
        replace_param_line(f, 'CH_N2', args.ch_n2)
        replace_param_line(f, 'CH_K2', args.ch_k2)
    if args.swat_exe:
        shutil.copy2(args.swat_exe, dst / 'swat.exe')
    print(f'created validation TxtInOut: {dst}')


if __name__ == '__main__':
    main()
