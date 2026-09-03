#!/usr/bin/env python3
"""Verify the four official Springer Nature assets against the audited snapshot.

The SHA256 values below were computed from the user-supplied official asset bundle
on 2026-09-03. A hash mismatch does not automatically mean a file is malicious; it
means it is a different byte-level snapshot and must be audited before being used as
identical evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

EXPECTED = {
    "41467_2026_70417_MOESM1_ESM.pdf": {
        "bytes": 13259266,
        "sha256": "40f77c118e541b71b1c5eca8a979d1c6b14dc8ce008c23ea42de67be8948967b",
    },
    "41467_2026_70417_MOESM2_ESM.pdf": {
        "bytes": 82633,
        "sha256": "903c4a1a64f40d8a78a9eed562d5b87b7d004e29dd5b654596b329b7944d3a4a",
    },
    "41467_2026_70417_MOESM3_ESM.pdf": {
        "bytes": 5479393,
        "sha256": "085a5ed84a899436a3a1d3e6cd4eabb573e864cc8decc694284a15dddeb56ea7",
    },
    "41467_2026_70417_MOESM4_ESM.xlsx": {
        "bytes": 5429017,
        "sha256": "1bbbe011e8ad7841703c3b80a5e815295b8aeb5ec8c216fba183eaad6a07c924",
    },
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="vendor/nature", help="directory containing the four official files")
    args = ap.parse_args()
    root = Path(args.dir)
    ok = True
    report = []

    for name, exp in EXPECTED.items():
        path = root / name
        row = {"file": name, "exists": path.exists()}
        if not path.exists():
            row["state"] = "MISSING"
            report.append(row)
            ok = False
            continue

        sig = path.read_bytes()[:8]
        type_ok = True
        if name.endswith(".pdf"):
            type_ok = sig.startswith(b"%PDF-")
        elif name.endswith(".xlsx"):
            type_ok = zipfile.is_zipfile(path)

        actual_size = path.stat().st_size
        actual_hash = digest(path)
        size_ok = actual_size == exp["bytes"]
        hash_ok = actual_hash == exp["sha256"]
        row.update(
            {
                "type_ok": type_ok,
                "bytes": actual_size,
                "expected_bytes": exp["bytes"],
                "size_ok": size_ok,
                "sha256": actual_hash,
                "expected_sha256": exp["sha256"],
                "hash_ok": hash_ok,
                "state": "PASS" if type_ok and size_ok and hash_ok else "DIFFERENT_SNAPSHOT",
            }
        )
        report.append(row)
        ok &= type_ok and size_ok and hash_ok

    print(json.dumps(report, indent=2))
    print("NATURE_ASSET_VERIFICATION=" + ("PASS" if ok else "FAIL"))
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
