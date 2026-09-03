#!/usr/bin/env python3
"""Fetch official publisher assets for Guo et al. (2026)."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, time
import requests

ASSETS = {
    "supplementary": "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM1_ESM.pdf",
    "reporting_summary": "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM2_ESM.pdf",
    "peer_review": "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM3_ESM.pdf",
    "source_data": "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-70417-z/MediaObjects/41467_2026_70417_MOESM4_ESM.xlsx",
}
CODE_OCEAN_DOI = "https://doi.org/10.24433/CO.0939560.v1"

def sha256(path: pathlib.Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def download(url: str, dest: pathlib.Path, retries: int=3) -> dict:
    last=None
    for attempt in range(1,retries+1):
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with dest.open('wb') as f:
                    for chunk in r.iter_content(1024*1024):
                        if chunk: f.write(chunk)
            return {"url":url,"file":dest.name,"size":dest.stat().st_size,"sha256":sha256(dest)}
        except Exception as e:
            last=e
            if dest.exists(): dest.unlink()
            time.sleep(attempt*2)
    raise RuntimeError(f"failed after {retries} attempts: {url}: {last}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out', default='vendor/nature')
    args=ap.parse_args()
    out=pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    manifest=[]
    for key,url in ASSETS.items():
        name=url.rsplit('/',1)[-1]
        print(f"[FETCH] {key}: {name}")
        manifest.append(download(url,out/name))
    (out/'SHA256_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('[OK] Nature assets downloaded and hashed')
    try:
        r=requests.get(CODE_OCEAN_DOI, allow_redirects=True, timeout=30)
        print(f"[CODE OCEAN DOI] HTTP {r.status_code}: {r.url}")
        print('Export the published capsule through Code Ocean; do not invent an export URL.')
    except Exception as e:
        print(f"[CODE OCEAN DOI] resolution failed: {e}")

if __name__=='__main__': main()
