#!/usr/bin/env python3
"""Basic integrity checks for downloaded official paper assets."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys, zipfile

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dir',default='vendor/nature'); a=ap.parse_args()
    d=pathlib.Path(a.dir)
    expected=['41467_2026_70417_MOESM1_ESM.pdf','41467_2026_70417_MOESM2_ESM.pdf','41467_2026_70417_MOESM3_ESM.pdf','41467_2026_70417_MOESM4_ESM.xlsx']
    ok=True; rows=[]
    for n in expected:
        p=d/n
        if not p.exists(): print('[MISSING]',n); ok=False; continue
        sig=p.read_bytes()[:8]
        if n.endswith('.pdf') and not sig.startswith(b'%PDF-'): print('[BAD PDF]',n); ok=False
        if n.endswith('.xlsx') and not zipfile.is_zipfile(p): print('[BAD XLSX]',n); ok=False
        rows.append({'file':n,'size':p.stat().st_size,'sha256':digest(p)})
    print(json.dumps(rows,indent=2))
    sys.exit(0 if ok else 2)
if __name__=='__main__': main()
