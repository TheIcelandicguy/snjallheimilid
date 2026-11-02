"""Check CLAUDE.md against the site: every backticked file path must exist and every #id must be in index.html."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
doc = (ROOT / 'CLAUDE.md').read_text(encoding='utf-8')
html = (ROOT / 'index.html').read_text(encoding='utf-8')
js = (ROOT / 'site.js').read_text(encoding='utf-8')
fails = []
for tok in set(re.findall(r'`([^`\n]+)`', doc)):
    if tok.startswith('#'):
        if f'id="{tok[1:]}"' not in html:
            fails.append(f'id {tok} not in index.html')
    elif re.fullmatch(r'[\w.\-/]+\.(html|css|js|svg|md|py|json)|\.nojekyll|CNAME|LICENSE', tok):
        if not (ROOT / tok).exists() and tok != 'CNAME':
            fails.append(f'file {tok} missing')
    elif re.fullmatch(r'[A-Z_]{3,}', tok):
        if f'const {tok}' not in js:
            fails.append(f'constant {tok} not in site.js')
    elif tok.startswith('[data-'):
        if tok[1:-1].split('=')[0] not in html:
            fails.append(f'attribute {tok} not in index.html')
for f in fails:
    print('FAIL', f)
print(f'check_docs: {len(fails)} failure(s)')
sys.exit(1 if fails else 0)
