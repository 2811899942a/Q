#!/usr/bin/env python3
import argparse, re, json, sys
from pathlib import Path
from collections import Counter

def tokens(text):
    return Counter(re.findall(r'[-+]?\d+(?:\.\d+)?%?', text))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True)
    p.add_argument('--translation',required=True)
    p.add_argument('--json')
    a=p.parse_args()
    s=tokens(Path(a.source).read_text(encoding='utf-8'))
    t=tokens(Path(a.translation).read_text(encoding='utf-8'))
    r={'status':'PASS' if s==t else 'REVIEW_REQUIRED','missing':dict(s-t),'extra':dict(t-s)}
    out=json.dumps(r,ensure_ascii=False,indent=2)
    print(out)
    if a.json: Path(a.json).write_text(out,encoding='utf-8')
    return 0 if r['status']=='PASS' else 1

if __name__=='__main__': sys.exit(main())
