"""The product page (owner 2026-11-27: "a full product view page with a product filter"): python tools/products.py

Writes vorur.html whole: every part each fitting line offers as a card with its computer-made picture, and filters by line, colour, kind and
smart / plain, each with a count, as a shop's filter list has them. What is on the page is tools/lines.json (the estimate's own table, kinds of part
only: no item numbers, no prices) and the pictures of img/lines3d/, so the page cannot show a part the estimate has not. A card is one part of one
line; the colours it is made in are dots on the card, and a colour picked in the filter shows the picture in that colour. vorur.js does the
filtering; without script every card shows and the filters are hidden. New texts get their en / es / pl translation from TEXTS here (written into
i18n/<lang>.json where the key is missing; es / pl are Claude's, not read by a native speaker); tools/i18n.py then writes the three copies.
"""
import io
import json
import os
import re

from lines_view import FITS, MARGIN, NAMES, OFFER, SIZES, SMART, TABS, fits_of, glyph, offered

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HOST = 'https://snjallheimilid.is/'
# the sizes of frame each line has in each colour, in positions side by side: written by the estimator's tools/lines_offer.mjs, like lines.json
# the policy and the visit counter's tag are index.html's, copied so that the two pages cannot differ
INDEX = io.open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
CSP = re.search(r'<meta http-equiv="Content-Security-Policy"[^>]*>', INDEX).group(0)
COUNTER = re.search(r'<script data-goatcounter[^>]*></script>', INDEX).group(0)
FRAMES = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frames.json'), encoding='utf-8'))

# the kinds of part, as the filter groups them: id, (is, en, es, pl), the parts
CATS = [
    ('rofar', ('Rofar', 'Switches', 'Interruptores', 'Łączniki'), ['sw1', 'sw2', 'sw3', 'neon1', 'neon2', 'bell', 'touch1', 'touch2', 'touch3', 'touch4']),
    ('tenglar', ('Tenglar', 'Sockets', 'Enchufes', 'Gniazdka'), ['socket', 'socket_cover', 'socket_usb', 'socket_usb2', 'ssocket']),
    ('hledsla', ('USB og hleðsla', 'USB and charging', 'USB y carga', 'USB i ładowanie'), ['usb', 'charger65']),
    ('net', ('Net og sjónvarp', 'Network and TV', 'Red y TV', 'Sieć i TV'), ['net', 'net2', 'tv', 'sat', 'tel', 'hdmi']),
    ('dimmerar', ('Dimmerar og hraðastillar', 'Dimmers and speed controls', 'Reguladores', 'Ściemniacze i regulatory'), ['dimmer', 'tdim', 'fan']),
    ('tjold', ('Gluggatjöld', 'Blinds and curtains', 'Persianas y cortinas', 'Rolety i zasłony'), ['blind', 'sblind', 'scurtain']),
    ('hiti', ('Hiti', 'Heating', 'Calefacción', 'Ogrzewanie'), ['heatw', 'heate']),
    ('annad', ('Annað', 'Other', 'Otros', 'Inne'), ['blank']),
]
CAT_OF = {k: c for c, _n, ks in CATS for k in ks}
DOT = {'white': '#f4f4f1', 'black': '#17181a', 'grey': '#8b9097', 'gold': '#c5a45c'}
TEXTS = {
    'title': ('Vörur – rofar, tenglar og rammar | Snjallheimilið', 'Products – switches, sockets and frames | Snjallheimilið', 'Productos – interruptores, enchufes y marcos | Snjallheimilið', 'Produkty – łączniki, gniazdka i ramki | Snjallheimilið'),
    'desc': ('Allt innlagnaefnið sem Snjallheimilið setur upp: rofar, tenglar, dimmerar og snjallhlutir eftir línu, lit og gerð.',
             'All the fittings Snjallheimilið installs: switches, sockets, dimmers and smart parts by line, colour and kind.',
             'Todo el material que instala Snjallheimilið: interruptores, enchufes, reguladores y piezas inteligentes por línea, color y tipo.',
             'Cały osprzęt, który montuje Snjallheimilið: łączniki, gniazdka, ściemniacze i części smart według linii, koloru i rodzaju.'),
    'h1': ('Innlagnaefni í boði', 'Fittings on offer', 'Material disponible', 'Dostępny osprzęt'),
    'lead': ('Hver hlutur sem línurnar bjóða. Síaðu eftir línu, lit og gerð til að sjá hvað fæst saman.',
             'Every part the lines offer. Filter by line, colour and kind to see what goes together.',
             'Cada pieza que ofrecen las líneas. Filtra por línea, color y tipo para ver qué combina.',
             'Każda część, którą oferują linie. Filtruj według linii, koloru i rodzaju, aby zobaczyć, co do siebie pasuje.'),
    'home': ('Heim', 'Home', 'Inicio', 'Start'),
    'fittings': ('Innlagnaefni', 'Fittings', 'Material', 'Osprzęt'),
    'contact': ('Samband', 'Contact', 'Contacto', 'Kontakt'),
    'langs': ('Tungumál', 'Language', 'Idioma', 'Język'),
    'filters': ('Síur', 'Filters', 'Filtros', 'Filtry'),
    'line': ('Lína', 'Line', 'Línea', 'Linia'),
    'fit': ('Litur', 'Colour', 'Color', 'Kolor'),
    'kind': ('Gerð', 'Kind', 'Tipo', 'Rodzaj'),
    'smartg': ('Snjallt eða venjulegt', 'Smart or plain', 'Inteligente o normal', 'Smart czy zwykłe'),
    'smart': ('Snjallhlutir', 'Smart parts', 'Piezas inteligentes', 'Części smart'),
    'plain': ('Venjulegir hlutir', 'Plain parts', 'Piezas normales', 'Części zwykłe'),
    'clear': ('Hreinsa síur', 'Clear filters', 'Quitar filtros', 'Wyczyść filtry'),
    'count': ('Fjöldi hluta:', 'Parts:', 'Piezas:', 'Części:'),
    'none': ('Enginn hlutur passar við þessar síur.', 'No part matches these filters.', 'Ninguna pieza coincide con estos filtros.', 'Żadna część nie pasuje do tych filtrów.'),
    'cta': ('Fá verðbil', 'Get a price range', 'Obtener un rango de precios', 'Poznaj przedział cen'),
    'note': ('Myndirnar eru tölvugerðar, ekki ljósmyndir: þær sýna gerð, stærð og lögun hlutanna, ekki nákvæmt útlit. Engin verð eru á síðunni; verðbil á efninu fæst í áætluninni.',
             'The pictures are computer-made, not photographs: they show the kind, the size and the shape of the parts, not their exact look. There are no prices on this page; the estimate gives a price range for the material.',
             'Las imágenes están hechas por ordenador, no son fotografías: muestran el tipo, el tamaño y la forma de las piezas, no su aspecto exacto. No hay precios en esta página; el presupuesto da un rango de precios del material.',
             'Obrazy są wygenerowane komputerowo, to nie zdjęcia: pokazują rodzaj, rozmiar i kształt części, a nie ich dokładny wygląd. Na tej stronie nie ma cen; wycena podaje przedział cen materiału.'),
    # the link to this page under the lines view of index.html
    'all': ('Skoða alla hluti með síum', 'See every part, with filters', 'Ver todas las piezas, con filtros', 'Zobacz wszystkie części, z filtrami'),
    # the frame builder
    'pb': ('Settu saman ramma', 'Put a frame together', 'Monta un marco', 'Złóż ramkę'),
    'pbhelp': ('Ýttu á plúsinn á hlut til að setja hann í rammann, eða dragðu hann þangað. Ýttu á hólf í rammanum til að færa það eða taka það úr.',
               'Press the plus on a part to put it in the frame, or drag it there. Press a position in the frame to move it or take it out.',
               'Pulsa el más de una pieza para ponerla en el marco, o arrástrala hasta él. Pulsa un hueco del marco para moverlo o quitarlo.',
               'Naciśnij plus na części, aby włożyć ją do ramki, albo przeciągnij ją tam. Naciśnij pole w ramce, aby je przesunąć lub wyjąć.'),
    'add': ('Setja í ramma', 'Put in the frame', 'Poner en el marco', 'Włóż do ramki'),
    'less': ('Minni rammi', 'Smaller frame', 'Marco más pequeño', 'Mniejsza ramka'),
    'more': ('Stærri rammi', 'Larger frame', 'Marco más grande', 'Większa ramka'),
    'left': ('Færa til vinstri', 'Move left', 'Mover a la izquierda', 'Przesuń w lewo'),
    'right': ('Færa til hægri', 'Move right', 'Mover a la derecha', 'Przesuń w prawo'),
    'out': ('Taka úr', 'Take out', 'Quitar', 'Wyjmij'),
    'reset': ('Tæma ramma', 'Empty the frame', 'Vaciar el marco', 'Opróżnij ramkę'),
    'slot': ('Tómt hólf', 'Empty position', 'Hueco vacío', 'Puste pole'),
    'm_full': ('Stærsti rammi línunnar í þessum lit tekur {n} hólf.', 'The largest frame of this line in this colour takes {n} positions.', 'El marco más grande de esta línea en este color tiene {n} huecos.', 'Największa ramka tej linii w tym kolorze ma {n} pól.'),
    'm_line': ('Hlutir úr annarri línu passa ekki í þennan ramma. Tæmdu rammann til að byrja á annarri línu.', 'Parts of another line do not fit this frame. Empty the frame to start on another line.',
               'Las piezas de otra línea no encajan en este marco. Vacía el marco para empezar con otra línea.', 'Części z innej linii nie pasują do tej ramki. Opróżnij ramkę, aby zacząć od innej linii.'),
    'm_fit': ('Þessi hlutur fæst ekki í litnum sem ramminn er í.', 'This part is not made in the colour of the frame.', 'Esta pieza no existe en el color del marco.', 'Ta część nie jest dostępna w kolorze ramki.'),
    's1': ('Einfaldur rammi', 'Single frame', 'Marco simple', 'Ramka pojedyncza'),
    's2': ('Tvöfaldur rammi', 'Double frame', 'Marco doble', 'Ramka podwójna'),
    's3': ('Þrefaldur rammi', 'Triple frame', 'Marco triple', 'Ramka potrójna'),
    's4': ('Fjórfaldur rammi', 'Frame of four', 'Marco cuádruple', 'Ramka poczwórna'),
    's5': ('Fimmfaldur rammi', 'Frame of five', 'Marco quíntuple', 'Ramka pięciokrotna'),
    'logo': ('Merki Snjallheimilisins', '', '', ''),
}
T = lambda k: TEXTS[k][0]
FIT_NAME = dict(FITS)


def cards():
    """One card per part of a line: (line, line's name, kind, the colours it is made in)."""
    return [(i, name, k, fits_of(i, [k])) for i, name in TABS for k in offered(i)]


def option(group, value, label, n, dot=''):
    sw = f'<span class="pv-dot" style="--c:{dot}"></span>' if dot else ''
    return f'<label><input type="checkbox" name="{group}" value="{value}">{sw}<span>{label}</span> <span class="pv-n" data-n>({n})</span></label>'


def group(name, title, body, open_=False):
    return f'      <details class="pv-group" data-group="{name}"{" open" if open_ else ""}><summary>{title}</summary><div class="pv-opts">{body}</div></details>'


def build():
    cs = cards()
    pbfits = ''.join(f'<button type="button" class="pb-fit" data-fit="{f}" style="--c:{DOT[f]}" aria-label="{n[0]}" title="{n[0]}" aria-pressed="false"></button>' for f, n in FITS)
    pbdata = json.dumps({'glyphs': {k: glyph(k, 0) for k in NAMES}, 'sizes': FRAMES}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    n_line = {i: sum(1 for c in cs if c[0] == i) for i, _n in TABS}
    n_fit = {f: sum(1 for c in cs if f in c[3]) for f, _n in FITS}
    n_cat = {c: sum(1 for x in cs if CAT_OF[x[2]] == c) for c, _n, _k in CATS}
    n_smart = sum(1 for c in cs if c[2] in SMART)
    alt = ''.join(f'<link rel="alternate" hreflang="{lang}" href="{HOST}{"" if lang == "is" else lang + "/"}vorur.html">\n' for lang in ('is', 'en', 'es', 'pl')) + f'<link rel="alternate" hreflang="x-default" href="{HOST}vorur.html">\n'
    out = [f'''<!doctype html>
<html lang="is">
<head>
<meta charset="utf-8">
{CSP}
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{T("title")}</title>
<meta name="description" content="{T("desc")}">
{alt}<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="img/apple-touch-icon.png">
<link rel="preload" href="fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="site.css">
</head>
<body>
<!-- written by tools/products.py, do not edit by hand -->
<header class="top">
  <div class="wrap bar">
    <a class="brand" href="index.html"><img src="favicon.svg" width="32" height="32" alt="">Snjallheimilið</a>
    <nav>
      <a href="index.html">{T("home")}</a>
      <a href="index.html#innlagnaefni">{T("fittings")}</a>
      <a href="index.html#samband">{T("contact")}</a>
    </nav>
    <nav class="lang" aria-label="{T("langs")}"><a href="./vorur.html" lang="is" title="Íslenska">IS</a><a href="en/vorur.html" lang="en" title="English">EN</a><a href="es/vorur.html" lang="es" title="Español">ES</a><a href="pl/vorur.html" lang="pl" title="Polski">PL</a></nav>
  </div>
</header>

<main>
<section class="pv">
  <div class="wrap">
    <h1>{T("h1")}</h1>
    <p class="lede">{T("lead")}</p>
    <!-- the frame builder (vorur.js): a frame of the line and colour of its first part, drawn from the same shapes as the lines view -->
    <div class="lv pb" id="pb" data-line="" data-fit="white" hidden>
      <h2 class="pb-h">{T("pb")}</h2>
      <p class="muted pb-help">{T("pbhelp")}</p>
      <div class="lv-wall pb-wall" id="pbWall"><svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><linearGradient id="lv-gloss" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".38"/><stop offset=".45" stop-color="#fff" stop-opacity=".04"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs></svg><div class="pb-frame" id="pbFrame"></div></div>
      <p class="pb-name" id="pbName"></p>
      <div class="pb-bar">
        <span class="pb-set"><button type="button" class="pb-b" id="pbLess" aria-label="{T("less")}" title="{T("less")}">−</button><button type="button" class="pb-b" id="pbMore" aria-label="{T("more")}" title="{T("more")}">+</button></span>
        <span class="pb-set" id="pbFits">{pbfits}</span>
        <span class="pb-set" id="pbSel" hidden><button type="button" class="pb-b" id="pbLeft" aria-label="{T("left")}" title="{T("left")}">←</button><button type="button" class="pb-b" id="pbRight" aria-label="{T("right")}" title="{T("right")}">→</button><button type="button" class="pb-b wide" id="pbOut">{T("out")}</button></span>
        <button type="button" class="pb-b wide pb-reset" id="pbReset">{T("reset")}</button>
      </div>
      <p class="pb-msg" id="pbMsg" role="status"></p>
      <div hidden id="pbText"><span data-t="add">{T("add")}</span><span data-t="slot">{T("slot")}</span><span data-t="full">{T("m_full")}</span><span data-t="line">{T("m_line")}</span><span data-t="fit">{T("m_fit")}</span><span data-t="s1">{T("s1")}</span><span data-t="s2">{T("s2")}</span><span data-t="s3">{T("s3")}</span><span data-t="s4">{T("s4")}</span><span data-t="s5">{T("s5")}</span></div>
      <script type="application/json" id="pbData">{pbdata}</script>
    </div>
    <div class="pv-head"><button type="button" class="btn pv-toggle" id="pvToggle" aria-expanded="false" aria-controls="pvFilters">{T("filters")}<span id="pvOn"></span></button><p class="pv-count">{T("count")} <b id="pvCount">{len(cs)}</b></p><button type="button" class="btn pv-clear" id="pvClear" hidden>{T("clear")}</button></div>
    <div class="pv-body">
    <form class="pv-filters" id="pvFilters">''',
           group('line', T('line'), ''.join(option('line', i, name, n_line[i]) for i, name in TABS), True),
           group('fit', T('fit'), ''.join(option('fit', f, n[0], n_fit[f], DOT[f]) for f, n in FITS), True),
           group('cat', T('kind'), ''.join(option('cat', c, n[0], n_cat[c]) for c, n, _k in CATS if n_cat[c]), True),
           group('smart', T('smartg'), option('smart', '1', T('smart'), n_smart) + option('smart', '0', T('plain'), len(cs) - n_smart)),
           '    </form>',
           '    <ul class="pv-grid" id="pvGrid">']
    for i, name, k, fits in cs:
        px = round((SIZES[i] + 2 * MARGIN) * 4)
        dots = ''.join(f'<span class="pv-dot" style="--c:{DOT[f]}" role="img" aria-label="{FIT_NAME[f][0]}" title="{FIT_NAME[f][0]}"></span>' for f in fits)
        out.append(f'      <li class="pv-card" data-line="{i}" data-cat="{CAT_OF[k]}" data-smart="{1 if k in SMART else 0}" data-fits="{" ".join(fits)}">'
                   f'<div class="pv-pic"><img src="img/lines3d/{i}-{fits[0]}-{k}.webp" data-file="{k}" width="{px}" height="{px}" alt="" loading="lazy" decoding="async"></div>'
                   f'<h3>{NAMES[k][0]}</h3><p class="pv-line">{name}</p><p class="pv-dots">{dots}</p></li>')
    out.append(f'''    </ul>
    </div>
    <p class="pv-none" id="pvNone" hidden>{T("none")}</p>
    <div class="cta"><a class="btn primary" data-aetlun href="https://aetlun.snjallheimilid.is/quick.html">{T("cta")}</a></div>
    <p class="muted small">{T("note")}</p>
  </div>
</section>
</main>

<footer>
  <div class="wrap">
    <div class="badge"><img src="img/logo-hringlaga.svg" width="88" height="88" alt="{T("logo")}"><span>© <span id="year"></span> Snjallheimilið · Akureyri</span></div>
    <a href="https://github.com/TheIcelandicguy" rel="noopener">GitHub</a>
  </div>
</footer>
<script src="vorur.js"></script>
''' + COUNTER + '''
</body>
</html>
''')
    return '\n'.join(out)


def main():
    io.open(os.path.join(ROOT, 'vorur.html'), 'w', encoding='utf-8', newline='\n').write(build())
    texts = [v for v in TEXTS.values() if v[1]] + [n for _c, n, _k in CATS]
    for col, lang in enumerate(('en', 'es', 'pl'), 1):
        f = os.path.join(ROOT, 'i18n', lang + '.json')
        raw = io.open(f, encoding='utf-8', newline='').read()
        have = json.loads(raw)
        add = list(dict((x[0], x[col]) for x in texts if x[0] not in have).items())
        if add:
            n2 = '\r\n' if '\r\n' in raw else '\n'
            end = raw.rstrip().rindex('}')
            io.open(f, 'w', encoding='utf-8', newline='').write(raw[:end].rstrip() + ''.join(',' + n2 + '  ' + json.dumps(k, ensure_ascii=False) + ': ' + json.dumps(v, ensure_ascii=False) for k, v in add) + n2 + '}' + n2)
        print(lang, len(add), 'texts added')
    print('vorur.html written,', len(cards()), 'parts')


if __name__ == '__main__':
    main()
