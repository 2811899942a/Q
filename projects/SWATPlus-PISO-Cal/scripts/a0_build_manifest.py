from __future__ import annotations

import argparse

from a0_utils import make_paths, print_result

from swatplus_piso.audit.provenance import build_provenance, write_provenance


def main() -> int:
    parser = argparse.ArgumentParser(description="Build South Branch A0 provenance manifests")
    parser.add_argument("--root", "--asset-root", dest="root")
    parser.add_argument("--config")
    parser.add_argument("--out")
    parser.add_argument("--qobs-root", help="override the external clean observation directory")
    args = parser.parse_args()
    paths = make_paths(args.root, args.config, args.out, args.qobs_root)
    provenance = build_provenance(paths)
    write_provenance(paths, provenance)
    print_result("A0 provenance", provenance)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
