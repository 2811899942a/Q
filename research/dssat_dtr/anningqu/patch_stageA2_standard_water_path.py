#!/usr/bin/env python3
"""Convert generated Anningqu Stage A2 MZX files to the standard CERES water path.

Why this exists
---------------
The first Stage A2 attempt intentionally tried EVAPO=Z / PHOTO=L to make the
M15 hourly air-temperature correction enter the hourly energy/water pathway.
DSSAT v4.8.5 CERES-Maize cannot use that path with the frozen official maize
species data: ETPHOT expects a !*PHOT parameter block that MZCER048.SPE does
not contain. EVAPO=H was also rejected because TRANS requires maize PHSV/PHTV,
which are absent from the same official species file.

The Anningqu WTH files contain SRAD/TMAX/TMIN/RAIN only, so Penman variants
that need additional humidity/dew-point/wind forcing are not introduced here.
This diagnostic therefore uses the ordinary source-supported CERES setup:

    WATER=Y, NITRO=N, EVAPO=R, PHOTO=R

M0 and M15 still receive identical weather, soil, cultivar and Water-6
management. The purpose is deliberately narrow: test whether the already
verified M15 thermal change propagates into standard water/crop state without
inventing any new crop or weather parameter.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_stageA2_standard_water_path.py MZX_DIR")

root = Path(sys.argv[1])
files = sorted(root.glob("ANQH2[12][0-9][0-9].MZX"))
if len(files) != 10:
    raise SystemExit(f"expected 10 Stage A2 MZX files, found {len(files)} in {root}")

old_methods = " 1 ME              M     M     E     Z     S     L     R     1     G     R     2"
new_methods = " 1 ME              M     M     E     R     S     R     R     1     G     R     2"

for path in files:
    text = path.read_text(encoding="latin-1")
    if text.count(old_methods) != 1:
        raise SystemExit(f"{path.name}: expected exactly one frozen Z/L METHODS row")
    text = text.replace(old_methods, new_methods)
    text = text.replace("M15 WATER6 HR-ET", "M15 WATER6 STD-ET")
    text = text.replace("ANNINGQU A2 W6", "ANNINGQU A2R W6")
    text = text.replace("STAGEA2 WATER6", "STAGEA2R WATER6")
    path.write_text(text, encoding="latin-1")
    print(f"patched {path.name}: WATER=Y NITRO=N EVAPO=R PHOTO=R")
