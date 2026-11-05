"""The home page in other languages (owner 2026-11-04: English, Spanish, Polish). index.html stays the Icelandic
source; this writes en/index.html, es/index.html and pl/index.html from it, every text node and text attribute
looked up in i18n/<lang>.json (Icelandic text -> translation; nothing inside svg, script or style). A text without a
translation stops the build and is listed, so the pages never ship half-translated.

  python tools/i18n.py          build the three pages
  python tools/i18n.py --dump   print every text of index.html that needs a translation, as JSON keys

Relative links and sources get ../ in front; the film and its captions take the language's own files
(video/einn-dagur.<lang>.mp4, tools/film/timeline.<lang>.json), and site.js gets its few strings in window.I18N."""
import html
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
LANGS = ['en', 'es', 'pl']
HOST = 'https://xn--snjallheimili-gkb.is/'
ATTRS = ('content', 'alt', 'aria-label', 'placeholder', 'title')
SKIP = re.compile(r'<(svg|script|style)\b.*?</\1>', re.S)
TAG_TEXT = re.compile(r'>([^<>]+)<')
ATTR = re.compile(r'\b(' + '|'.join(ATTRS) + r')="([^"]+)"')
# the strings site.js shows: keyed by the Icelandic text, as in the JSON files
JS_STRINGS = ['Nafn, netfang og erindi þarf að fylla út.', 'Sendi…', 'Takk, erindið er komið. Ég svara eins fljótt og ég get.',
              'Sending tókst ekki ({err}). Reyndu aftur, eða sendu póst beint.', 'Fyrirspurn af snjallheimilið.is', 'Spila', 'Stöðva']
# the room names and circuit labels drawn in the hero's svg (text class rn / gr); the svg is skipped as a whole above,
# so these are looked up here, in the same JSON files
SVG_STRINGS = ['Stofa', 'Eldhús', 'Svefnherbergi', 'Baðherbergi', 'Forstofa', 'Gr.1', 'Gr.2']
SVG_TEXT = re.compile(r'(<text class="(?:rn|gr)"[^>]*>)([^<]+)(</text>)')


def plain(s):
    return html.unescape(s).strip()


def needs(s):
    """A text that is words, not a number, a symbol or a name that stays the same in every language."""
    t = plain(s)
    return bool(t) and bool(re.search(r'[A-Za-zÀ-ÿÞþÐðÆæÖö]{2}', t)) and '=' not in t and t not in ('Snjallheimilið', 'GitHub', 'Akureyri', 'Snjallheimilið · Akureyri', 'IS', 'EN', 'ES', 'PL', 'website', 'Íslenska', 'English', 'Español', 'Polski')


def pathlike(t):
    return bool(re.fullmatch(r'[\w-]*[./][\w./-]*', t))


def segments(src):
    """Every translatable text of the page, in order of first appearance."""
    out = []
    pos = 0
    for m in SKIP.finditer(src):
        out += segments_of(src[pos:m.start()])
        pos = m.end()
    out += segments_of(src[pos:])
    seen, uniq = set(), []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


def segments_of(part):
    out = [plain(m.group(1)) for m in TAG_TEXT.finditer(part) if needs(m.group(1))]
    out += [plain(m.group(2)) for m in ATTR.finditer(part) if needs(m.group(2)) and not pathlike(plain(m.group(2)))]
    return out


def translate(src, tr, lang, missing):
    def text(m):
        t = plain(m.group(1))
        if not needs(t):
            return m.group(0)
        if t not in tr:
            missing.add(t)
            return m.group(0)
        return '>' + m.group(1).replace(m.group(1).strip(), html.escape(tr[t], quote=False)) + '<'

    def attr(m):
        t = plain(m.group(2))
        if not needs(t) or pathlike(t):
            return m.group(0)
        if t not in tr:
            missing.add(t)
            return m.group(0)
        return f'{m.group(1)}="{html.escape(tr[t])}"'

    out, pos = [], 0
    for m in SKIP.finditer(src):
        out.append(ATTR.sub(attr, TAG_TEXT.sub(text, src[pos:m.start()])))
        out.append(m.group(0))
        pos = m.end()
    out.append(ATTR.sub(attr, TAG_TEXT.sub(text, src[pos:])))
    s = ''.join(out)
    for k in SVG_STRINGS:
        if k not in tr:
            missing.add(k)
    s = SVG_TEXT.sub(lambda m: m.group(1) + html.escape(tr.get(m.group(2), m.group(2)), quote=False) + m.group(3), s)
    s = s.replace('<html lang="is">', f'<html lang="{lang}">')
    # one level down: relative links and sources
    s = re.sub(r'\b(href|src|poster)="(?!https?:|#|/|data:|mailto:|\.\./)([^"]+)"', lambda m: f'{m.group(1)}="../{m.group(2)[2:] if m.group(2).startswith("./") else m.group(2)}"', s)
    s = s.replace('../video/einn-dagur.mp4', f'../video/einn-dagur.{lang}.mp4')
    js = {k: tr[k] for k in JS_STRINGS if k in tr}
    for k in JS_STRINGS:
        if k not in tr:
            missing.add(k)
    s = s.replace('<script src="../site.js"></script>', '<script>window.I18N=' + json.dumps({'lang': lang, 't': js}, ensure_ascii=False) + '</script>\n<script src="../site.js"></script>')
    return s


def main():
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    if '--dump' in sys.argv:
        print(json.dumps({s: '' for s in segments(src) + JS_STRINGS + SVG_STRINGS}, ensure_ascii=False, indent=2))
        return
    for lang in LANGS:
        tr = json.load(open(os.path.join(ROOT, 'i18n', f'{lang}.json'), encoding='utf-8'))
        missing = set()
        page = translate(src, tr, lang, missing)
        if missing:
            print(f'{lang}: {len(missing)} text(s) without a translation:')
            for t in sorted(missing):
                print('  ', json.dumps(t, ensure_ascii=False))
            sys.exit(1)
        os.makedirs(os.path.join(ROOT, lang), exist_ok=True)
        with open(os.path.join(ROOT, lang, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(page)
        unused = [k for k in tr if k not in segments(src) and k not in JS_STRINGS and k not in SVG_STRINGS]
        print(f'{lang}/index.html written' + (f'; unused keys: {unused}' if unused else ''))


if __name__ == '__main__':
    main()
