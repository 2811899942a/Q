#!/usr/bin/env python3
"""Apply the frozen M15 hourly-temperature reconstruction variants.

This wrapper reuses the audited M15 source transformation and only replaces
its frozen calibration constants. No crop/yield information is used here.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ENC = "latin-1"
VARIANTS = {
    "13p5": (13.5, 6.407985379809223),
    "13p8": (13.8, 6.749813473189908),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_root", type=Path)
    ap.add_argument("--variant", choices=sorted(VARIANTS), default="13p5")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    base = here / "apply_m15_htemp_patch.py"
    subprocess.run([sys.executable, str(base), str(args.source_root)], check=True)

    hmet = args.source_root / "Weather" / "HMET.for"
    text = hmet.read_text(encoding=ENC)
    old = "PARAMETER (DTRC=14.8, ALPHA=7.8094)"
    if text.count(old) != 1:
        raise SystemExit("Frozen M15 wrapper: expected generic M15 parameter line exactly once")

    dtrc, alpha = VARIANTS[args.variant]
    new = f"PARAMETER (DTRC={dtrc:.1f}, ALPHA={alpha:.15f})"
    text = text.replace(old, new, 1)
    text = text.replace(
        "C    DTRC  = 14.8 C, primary Urumqi calibration period (2000-2016)",
        f"C    DTRC  = {dtrc:.1f} C, frozen Urumqi calibration threshold",
    )
    text = text.replace(
        "C    ALPHA = 7.8094, dense Diwopu sunset-anchor calibration (2000-2016)",
        f"C    ALPHA = {alpha:.15f}, frozen sunset-anchor coefficient",
    )
    hmet.write_text(text, encoding=ENC)

    out = hmet.read_text(encoding=ENC)
    if new not in out:
        raise SystemExit("Frozen M15 wrapper validation failed")
    print(f"Applied frozen M15-{args.variant}: DTRC={dtrc}, ALPHA={alpha}")


if __name__ == "__main__":
    main()
