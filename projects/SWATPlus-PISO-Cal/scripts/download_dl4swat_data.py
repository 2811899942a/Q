"""Download the CC BY 4.0 DL4SWAT public dataset from Zenodo.

The script uses the Zenodo REST metadata endpoint rather than hard-coding a
transient file URL. It verifies the MD5 published on the record page.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

RECORD_ID = 7271945
EXPECTED_MD5 = "d9547cebe2a6607dec5355a45296d5bd"


def md5sum(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.md5()  # noqa: S324 - checksum validation, not security
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/raw/dl4swat/Data.zip"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(f"https://zenodo.org/api/records/{RECORD_ID}") as response:
        metadata = json.load(response)
    files = metadata.get("files", [])
    match = next((item for item in files if item.get("key") == "Data.zip"), None)
    if match is None:
        raise RuntimeError("Data.zip was not found in the Zenodo record metadata")
    url = match["links"]["self"]
    print(f"Downloading {url} -> {args.output}")
    urllib.request.urlretrieve(url, args.output)
    actual = md5sum(args.output)
    if actual != EXPECTED_MD5:
        raise RuntimeError(f"MD5 mismatch: expected {EXPECTED_MD5}, got {actual}")
    print(f"OK md5={actual}")


if __name__ == "__main__":
    main()
