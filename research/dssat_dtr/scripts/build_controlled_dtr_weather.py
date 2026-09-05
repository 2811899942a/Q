#!/usr/bin/env python3
"""Create a controlled high-DTR DSSAT weather file for causal M20 tests.

Only TMAX is increased during a specified DOY window. M0 and M20 receive the
same modified daily weather, so their difference isolates the source bridge.
This is a mechanistic stress test, not an observed-weather validation dataset.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--delta-tmax", type=float, default=4.0)
    parser.add_argument("--start-doy", type=int, default=121)
    parser.add_argument("--end-doy", type=int, default=273)
    args = parser.parse_args()

    out = []
    changed = 0
    for raw in args.input.read_text(encoding="utf-8", errors="replace").splitlines():
        s = raw.strip()
        if not s or s.startswith(("*", "@")):
            out.append(raw)
            continue
        parts = s.split()
        if len(parts) < 5 or not parts[0].isdigit():
            out.append(raw)
            continue
        doy = int(parts[0][-3:])
        srad, tmax, tmin, rain = map(float, parts[1:5])
        if args.start_doy <= doy <= args.end_doy:
            tmax += args.delta_tmax
            changed += 1
        out.append(f"{parts[0]:>5s} {srad:5.1f} {tmax:5.1f} {tmin:5.1f} {rain:5.1f}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(
        f"controlled DTR weather: {args.input.name} -> {args.output.name}; "
        f"delta_tmax={args.delta_tmax:+.1f} C; changed_days={changed}"
    )


if __name__ == "__main__":
    main()
