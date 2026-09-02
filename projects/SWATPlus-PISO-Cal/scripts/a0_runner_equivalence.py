from __future__ import annotations

import argparse

from a0_utils import make_paths, print_result

from swatplus_piso.audit.equivalence import run_equivalence


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real old/new South Branch runner equivalence cases")
    parser.add_argument("--root", "--asset-root", dest="root")
    parser.add_argument("--config")
    parser.add_argument("--out")
    parser.add_argument("--qobs-root", help="override the external clean observation directory")
    parser.add_argument("--cases", type=int, default=4)
    args = parser.parse_args()
    if not 3 <= args.cases <= 5:
        parser.error("--cases must be between 3 and 5")
    paths = make_paths(args.root, args.config, args.out, args.qobs_root)
    result = run_equivalence(paths, args.cases)
    print_result("A0 runner equivalence", result)
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
