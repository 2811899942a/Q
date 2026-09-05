#!/usr/bin/env python3
"""M17b: rerun the preregistered M17 selection with an expanded k bound.
Scientific formula/candidate q/Kt0 grids are unchanged. This audit exists because
M17 k_pre hit the numerical upper bound 10. Results go to a new directory.
"""
import importlib.util
from pathlib import Path
from scipy.optimize import minimize_scalar

HERE=Path(__file__).resolve(); spec=importlib.util.spec_from_file_location('m17',HERE.with_name('m17_regional_radiative_monotonic_warp.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.OUT=m.ROOT/'data'/'m17b_regional_radwarp_boundary_audit'

def fitk40(rows,prof,q,kt0,br):
    active=[r for r in rows if m.segment(r)[0]==br and m.exposure(r,prof,q,kt0)>0]
    if not active:return 0.
    def loss(k):
        return m.mean([(m.pred(r,prof,q,kt0,k if br=='pre' else 0,k if br=='post' else 0)-r['obs'])**2 for r in active])
    z=minimize_scalar(loss,bounds=(0,40),method='bounded',options={'xatol':1e-6})
    return float(z.x)
m.fitk=fitk40
m.main()
# Append the expanded-bound audit declaration without changing the computed table.
p=m.OUT/'README.md';p.write_text(p.read_text()+'\nExpanded numerical coefficient bound: 0 <= k <= 40. Formula and discrete candidate grids unchanged.\n')
