#!/usr/bin/env python3
"""Convert generated Anningqu Stage A2 MZX files to the standard CERES water path.

The first Stage A2 attempt used EVAPO=Z / PHOTO=L to test an hourly
energy/water pathway. DSSAT v4.8.5 CERES-Maize cannot use that path with the
frozen official maize species data because ETPHOT expects a !*PHOT block that
MZCER048.SPE does not contain. EVAPO=H also depends on maize PHSV/PHTV, which
are absent from the official species file. The Anningqu WTH files contain only
SRAD/TMAX/TMIN/RAIN, so weather variables required by alternative Penman paths
are not invented.

This patch therefore changes only the fixed-width METHODS row to the standard,
source-supported configuration:

    WATER=Y, NITRO=N, EVAPO=R, PHOTO=R

No title, treatment, date, field, cultivar, irrigation, soil, or weather text is
changed. This restriction is intentional because DSSAT experiment files are
fixed-column records and even a one-character title edit can shift IPEXP input
fields.
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

if len(old_methods) != len(new_methods):
    raise SystemExit("METHODS replacement is not fixed-width safe")

for path in files:
    text = path.read_text(encoding="latin-1")
    if text.count(old_methods) != 1:
        raise SystemExit(f"{path.name}: expected exactly one frozen Z/L METHODS row")
    patched = text.replace(old_methods, new_methods)
    if len(patched) != len(text):
        raise SystemExit(f"{path.name}: fixed-width safety check failed")
    path.write_text(patched, encoding="latin-1")
    print(f"patched {path.name}: WATER=Y NITRO=N EVAPO=R PHOTO=R; byte length preserved")
