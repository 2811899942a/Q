from __future__ import annotations

import argparse

from a0_utils import load_provenance, make_paths, print_result

from swatplus_piso.audit.dataset import build_broad_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the exact A0 broad theta/qsim/qobs tensors")
    parser.add_argument("--root", "--asset-root", dest="root")
    parser.add_argument("--config")
    parser.add_argument("--out")
    parser.add_argument("--qobs-root", help="override the external clean observation directory")
    args = parser.parse_args()
    paths = make_paths(args.root, args.config, args.out, args.qobs_root)
    provenance = load_provenance(paths)
    result = build_broad_dataset(paths, provenance)
    print_result("A0 dataset", result["metadata"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
