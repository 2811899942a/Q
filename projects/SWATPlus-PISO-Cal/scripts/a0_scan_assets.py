from __future__ import annotations

import argparse

from a0_utils import make_paths, print_result

from swatplus_piso.audit.assets import scan_assets, write_inventory


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan the locked South Branch local assets without running SWAT+")
    parser.add_argument("--root", "--asset-root", dest="root")
    parser.add_argument("--config")
    parser.add_argument("--out")
    parser.add_argument("--qobs-root", help="override the external clean observation directory")
    args = parser.parse_args()
    paths = make_paths(args.root, args.config, args.out, args.qobs_root)
    inventory = scan_assets(paths)
    write_inventory(paths, inventory)
    print_result("A0 asset scan", {"file_count": inventory["file_count"], "candidate_projects": len(inventory["candidate_projects"]), "engine": inventory["executable"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
