"""Check CLAUDE.md against the site: every backticked file path must exist and every #id must be in index.html or vorur.html.
Also checks every page against its Content-Security-Policy (see page_fails below)."""
import base64
import hashlib
import html as html_mod
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
doc = (ROOT / 'CLAUDE.md').read_text(encoding='utf-8')
html = (ROOT / 'index.html').read_text(encoding='utf-8') + (ROOT / 'vorur.html').read_text(encoding='utf-8')  # the two pages
js = (ROOT / 'site.js').read_text(encoding='utf-8')
fails = []
for tok in set(re.findall(r'`([^`\n]+)`', doc)):
    if tok.startswith('#'):
        if f'id="{tok[1:]}"' not in html:
            fails.append(f'id {tok} not in the pages')
    elif re.fullmatch(r'[\w.\-/]+\.(html|css|js|svg|md|py|json)|\.nojekyll|CNAME|LICENSE', tok):
        if not (ROOT / tok).exists() and tok != 'CNAME':
            fails.append(f'file {tok} missing')
    elif re.fullmatch(r'[A-Z_]{3,}', tok):
        if f'const {tok}' not in js:
            fails.append(f'constant {tok} not in site.js')
    elif tok.startswith('[data-'):
        if tok[1:-1].split('=')[0] not in html:
            fails.append(f'attribute {tok} not in the pages')

# The pages' Content-Security-Policy. Every page (the two sources and their en / es / pl copies) must state the same policy as
# index.html, and must hold nothing the policy would refuse: a script written in the page must be named in script-src by its
# hash (the failure prints the hash to write), a script from another host must be listed there and carry an integrity hash,
# and there is no handler written as an attribute. Hashes are taken with LF line ends, as git stores and Pages serves the files.
CSP_RE = re.compile(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">')
SCRIPT_RE = re.compile(r'<script\b([^>]*)>(.*?)</script>', re.S)


def page_fails(name, text, want):
    out = []
    m = CSP_RE.search(text)
    if not m:
        return [f'{name}: no Content-Security-Policy']
    csp = html_mod.unescape(m.group(1))
    if csp != want:
        out.append(f'{name}: its Content-Security-Policy is not index.html\'s (run tools/products.py and tools/i18n.py)')
    rules = {r.split()[0]: r.split()[1:] for r in csp.split(';') if r.strip()}
    scripts = rules.get('script-src', [])
    for attrs, body in SCRIPT_RE.findall(text):
        src = re.search(r'\bsrc="([^"]*)"', attrs)
        kind = re.search(r'\btype="([^"]*)"', attrs)
        if src:
            if re.match(r'(https?:)?//', src.group(1)):
                if src.group(1) not in scripts:
                    out.append(f'{name}: script {src.group(1)} is not in script-src')
                if 'integrity="sha' not in attrs:
                    out.append(f'{name}: script {src.group(1)} has no integrity hash')
        elif not kind or kind.group(1) in ('module', 'text/javascript'):  # a JSON block is data and is not run
            h = "'sha256-" + base64.b64encode(hashlib.sha256(body.encode('utf-8')).digest()).decode() + "'"
            if h not in scripts:
                out.append(f'{name}: a script written in the page is not in script-src; move it to a file, or add {h}')
    for m in re.finditer(r'<[a-z][^>]*\s(on[a-z]+)="', SCRIPT_RE.sub('', text)):
        out.append(f'{name}: handler {m.group(1)} written as an attribute')
    if re.search(r'(href|src|action)="\s*javascript:', text):
        out.append(f'{name}: a javascript: address')
    return out


pages = ['index.html', 'vorur.html'] + [f'{lang}/{p}' for lang in ('en', 'es', 'pl') for p in ('index.html', 'vorur.html')]
texts = {p: (ROOT / p).read_text(encoding='utf-8').replace('\r\n', '\n') for p in pages}
first = CSP_RE.search(texts['index.html'])
for p in pages:
    fails += page_fails(p, texts[p], html_mod.unescape(first.group(1)) if first else '')

for f in fails:
    print('FAIL', f)
print(f'check_docs: {len(fails)} failure(s)')
sys.exit(1 if fails else 0)
