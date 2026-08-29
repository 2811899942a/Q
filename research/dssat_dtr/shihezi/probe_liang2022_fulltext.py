from __future__ import annotations

import html
import io
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path('research/dssat_dtr/data/shihezi_real_case/liang2022_probe')
OUT.mkdir(parents=True, exist_ok=True)
UA = 'Mozilla/5.0 DSSAT-Xinjiang-research/1.0'

SEEDS = [
    'https://www.ggpsxb.com/jgpxxb/ch/reader/view_abstract.aspx?file_no=20220106',
    'https://www.ggpsxb.com/jgpxxb/ch/reader/view_abstract.aspx?file_no=20220106&flag=1',
    'https://doi.org/10.13522/j.cnki.ggps.2021337',
]


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/pdf,*/*'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get('Content-Type',''), r.read(), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, str(e.headers.get('Content-Type','')), e.read(), url
    except Exception as e:
        return None, '', str(e).encode('utf-8','replace'), url


def strip_html(s):
    s = re.sub(r'(?is)<script.*?</script>|<style.*?</style>', ' ', s)
    s = re.sub(r'(?s)<[^>]+>', ' ', s)
    s = html.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()


report = ['# Liang et al. 2022 official fulltext evidence probe', '']
all_links = []
pages = []
for seed in SEEDS:
    status, ctype, data, final = fetch(seed)
    report.append(f'- seed `{seed}` -> status={status}, type={ctype}, final={final}, bytes={len(data)}')
    if status == 200 and b'%PDF' not in data[:20]:
        text = data.decode('utf-8', 'replace')
        pages.append((final, text))
        for m in re.finditer(r'(?is)(?:href|src)\s*=\s*["\']([^"\']+)["\']', text):
            all_links.append(urllib.parse.urljoin(final, html.unescape(m.group(1))))
        # Also collect literal URL-ish strings and JS create/download links.
        for m in re.finditer(r'(?i)([^"\'<>\s]*(?:pdf|download|create_pdf)[^"\'<>\s]*)', text):
            u = html.unescape(m.group(1))
            if u:
                all_links.append(urllib.parse.urljoin(final, u))

# Common reader-system PDF endpoint guesses, tested only on the official journal host.
all_links += [
    'https://www.ggpsxb.com/jgpxxb/ch/reader/create_pdf.aspx?file_no=20220106&flag=1&journal_id=jgpxxb&year_id=2022',
    'https://www.ggpsxb.com/jgpxxb/ch/reader/create_pdf.aspx?file_no=20220106',
]

# Keep relevant candidates only, de-duplicate, same journal/DOI destination preferred.
candidates = []
seen = set()
for u in all_links:
    if u in seen:
        continue
    seen.add(u)
    low = u.lower()
    if 'ggpsxb.com' in low and any(k in low for k in ('pdf','download','reader','20220106')):
        candidates.append(u)

report += ['', '## Candidate links discovered', '']
for u in candidates[:100]:
    report.append(f'- {u}')

pdf_data = None
pdf_url = None
probe_rows = []
for u in candidates[:60]:
    status, ctype, data, final = fetch(u)
    is_pdf = data[:5] == b'%PDF-' or 'application/pdf' in ctype.lower()
    probe_rows.append((u, status, ctype, len(data), final, is_pdf))
    if is_pdf and len(data) > 10000:
        pdf_data = data; pdf_url = final; break

report += ['', '## Candidate fetch probe', '']
for row in probe_rows[:60]:
    u,status,ctype,n,final,is_pdf = row
    report.append(f'- status={status}, pdf={is_pdf}, bytes={n}, type={ctype}, url={u}, final={final}')

# Extract only bounded evidence snippets; do not save/republish the full third-party article.
keywords = ['施肥','尿素','肥料','氮肥','磷肥','钾肥','密度','株距','行距','新玉','P1','P2','P5','G2','G3','PHINT','W1','W2','W3','W4','产量','干物质','叶面积']

if pdf_data:
    report += ['', f'## PDF recovered', '', f'- URL: {pdf_url}', f'- bytes: {len(pdf_data)}']
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_data))
        texts = []
        for i,p in enumerate(reader.pages):
            t = p.extract_text() or ''
            texts.append(t)
        report.append(f'- pages: {len(texts)}')
        report += ['', '## Keyword evidence snippets', '']
        count = 0
        for i,t in enumerate(texts, 1):
            clean = re.sub(r'\s+', ' ', t)
            for kw in keywords:
                start = 0
                while True:
                    j = clean.find(kw, start)
                    if j < 0: break
                    a=max(0,j-180); b=min(len(clean),j+300)
                    snip=clean[a:b].replace('|','/')
                    report.append(f'- p.{i} `{kw}`: {snip}')
                    count += 1
                    start = j + len(kw)
                    if count >= 80: break
                if count >= 80: break
            if count >= 80: break
    except Exception as e:
        report.append(f'- PDF parse error: {e}')
else:
    report += ['', '## PDF recovery', '', '- No official PDF was automatically recovered from the journal page/DOI during this probe.']
    # Still inspect official abstract-page text for keywords.
    report += ['', '## Official page keyword snippets', '']
    count=0
    for url,text in pages:
        clean=strip_html(text)
        for kw in keywords:
            j=clean.find(kw)
            if j>=0:
                report.append(f'- `{kw}`: {clean[max(0,j-180):min(len(clean),j+300)]}')
                count+=1
                if count>=30: break
        if count>=30: break

(OUT/'README_LIANG2022_FULLTEXT_PROBE.md').write_text('\n'.join(report)+'\n', encoding='utf-8')
print('\n'.join(report[-20:]))
