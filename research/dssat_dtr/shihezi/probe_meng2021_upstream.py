from __future__ import annotations

import io
import re
import urllib.request
from pathlib import Path

URL = 'https://lwtj.shzu.edu.cn/openfile?dbid=72&lwsing=60931ddb25c7ab6ce77f44aadf98a132&objid=57_50_49_48_50'
OUT = Path('research/dssat_dtr/data/shihezi_real_case/meng2021_probe')
OUT.mkdir(parents=True, exist_ok=True)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36'

req = urllib.request.Request(URL, headers={
    'User-Agent': UA,
    'Accept': 'application/pdf,text/html;q=0.9,*/*;q=0.8',
    'Referer': 'https://lwtj.shzu.edu.cn/'
})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read(); status = r.status; ctype = r.headers.get('Content-Type',''); final = r.geturl()
except Exception as e:
    data = b''; status = None; ctype = ''; final = URL; err = repr(e)
else:
    err = ''

report = [
    '# Meng Yu 2021 upstream Shihezi field-experiment probe', '',
    f'- URL: {URL}',
    f'- status: {status}',
    f'- content type: {ctype}',
    f'- final: {final}',
    f'- bytes: {len(data)}',
    f'- error: {err}', '',
]

is_pdf = data[:5] == b'%PDF-' or 'application/pdf' in ctype.lower()
report.append(f'- recognized PDF: {is_pdf}')

keywords = [
    '施肥','肥料','尿素','磷酸','硫酸钾','氮肥','磷肥','钾肥','基肥','追肥','随水',
    '种植密度','密度','株距','行距','播种深度','新玉66','新玉 66',
    'PE','W1','W2','W3','W4','产量','籽粒','干物质','叶面积指数','LAI',
    '气象','最高气温','最低气温','降水','国家气象','51356','石河子'
]

if is_pdf and len(data) > 10000:
    # Do not save/commit the copyrighted full PDF. Extract only bounded evidence snippets.
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        texts = []
        for p in reader.pages:
            try: texts.append(p.extract_text() or '')
            except Exception: texts.append('')
        report += ['', f'## Pages: {len(texts)}', '', '## Bounded keyword evidence', '']
        hit_count = 0
        for pi,t in enumerate(texts,1):
            clean = re.sub(r'\s+', ' ', t)
            for kw in keywords:
                start = 0
                hits_this = 0
                while True:
                    j = clean.find(kw, start)
                    if j < 0: break
                    a=max(0,j-260); b=min(len(clean), j+520)
                    snip=clean[a:b].replace('|','/').replace('\n',' ')
                    report.append(f'- p.{pi} `{kw}`: {snip}')
                    hit_count += 1; hits_this += 1
                    start = j + max(1,len(kw))
                    if hits_this >= 3 or hit_count >= 180: break
                if hit_count >= 180: break
            if hit_count >= 180: break
        report += ['', f'Keyword snippet count: {hit_count}']
        # Also dump only pages 7-16-ish text if they appear to be methods, bounded to 60k chars,
        # to allow table recovery without archiving the PDF itself.
        method_chunks=[]
        for pi,t in enumerate(texts,1):
            clean=re.sub(r'\s+',' ',t)
            if any(k in clean for k in ['试验设计','试验概况','灌溉制度','试验材料','测定指标','田间管理']):
                method_chunks.append(f'\n## Extracted page {pi}\n{clean[:7000]}')
        (OUT/'METHOD_PAGES_EXTRACT.txt').write_text('\n'.join(method_chunks)[:60000], encoding='utf-8')
    except Exception as e:
        report += ['', f'PDF extraction failed: {e!r}']
else:
    preview = data[:4000].decode('utf-8','replace') if data else ''
    report += ['', '## Non-PDF preview', '', preview]

(OUT/'README_MENG2021_UPSTREAM_PROBE.md').write_text('\n'.join(report)+'\n', encoding='utf-8')
print('\n'.join(report[:14]))
print('\n'.join(report[-10:]))
