"""The drawn view of the fitting lines on a wall (owner 2026-11-24): python tools/lines_view.py

Writes the block between <!-- lines-view:start --> and <!-- lines-view:end --> in index.html: for each line a set of frames, one per kind of part the
line offers, plus a few frames of several positions, each an inline SVG with its name under it. The drawings are our own (flat shapes that show the kind
and the shape of a part, not a maker's picture); their colours come from CSS variables, so site.css paints the same drawing white, black, grey or gold,
and site.js only switches which set shows, the wall's colour and the fitting's colour, and lets a rocker be pressed. Without script every set shows.

What each line offers is LINES below, copied from the estimate's tables (smart-home-estimator: FIT_LINES in prices.js, quickKindsFor() in quick.js) on
2026-11-24: when a part is added there, add it here and run this again, then tools/i18n.py. New texts get their en / es / pl translation from NAMES and
UI here (written into i18n/<lang>.json where the key is missing; es / pl are Claude's, not read by a native speaker).
"""
import io
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
C = 60  # a position
PAD = 7  # the frame around the positions

# kind: (Icelandic, en, es, pl)
NAMES = {
    'sw1': ('Rofi', 'Switch', 'Interruptor', 'Łącznik'),
    'sw2': ('Tvöfaldur rofi', 'Double switch', 'Interruptor doble', 'Łącznik podwójny'),
    'sw3': ('Þrefaldur rofi', 'Triple switch', 'Interruptor triple', 'Łącznik potrójny'),
    'neon1': ('Rofi með gaumljósi', 'Switch with indicator lamp', 'Interruptor con piloto', 'Łącznik z podświetleniem'),
    'neon2': ('Tvöfaldur rofi með gaumljósi', 'Double switch with indicator lamps', 'Interruptor doble con piloto', 'Łącznik podwójny z podświetleniem'),
    'socket': ('Tengill', 'Socket', 'Enchufe', 'Gniazdko'),
    'socket_usb': ('Tengill með USB', 'Socket with USB', 'Enchufe con USB', 'Gniazdko z USB'),
    'socket_cover': ('Tengill með loki', 'Socket with cover', 'Enchufe con tapa', 'Gniazdko z klapką'),
    'socket_usb2': ('Tengill með tveimur USB', 'Socket with two USB ports', 'Enchufe con dos puertos USB', 'Gniazdko z dwoma portami USB'),
    'usb': ('USB-hleðsla', 'USB charger', 'Cargador USB', 'Ładowarka USB'),
    'charger65': ('65 W hleðsla', '65 W charger', 'Cargador de 65 W', 'Ładowarka 65 W'),
    'net': ('Nettengill', 'Network outlet', 'Toma de red', 'Gniazdo sieciowe'),
    'net2': ('Tvöfaldur nettengill', 'Double network outlet', 'Toma de red doble', 'Podwójne gniazdo sieciowe'),
    'tv': ('Sjónvarpstengill', 'TV outlet', 'Toma de TV', 'Gniazdo TV'),
    'sat': ('Gervihnattatengill', 'Satellite outlet', 'Toma de satélite', 'Gniazdo satelitarne'),
    'tel': ('Símatengill', 'Telephone outlet', 'Toma de teléfono', 'Gniazdo telefoniczne'),
    'hdmi': ('HDMI-tengill', 'HDMI outlet', 'Toma HDMI', 'Gniazdo HDMI'),
    'blind': ('Gluggatjaldarofi', 'Blind switch', 'Interruptor de persianas', 'Włącznik rolet'),
    'fan': ('Viftuhraðarofi', 'Fan speed switch', 'Regulador de ventilador', 'Regulator wentylatora'),
    'bell': ('Dyrabjöllurofi', 'Doorbell switch', 'Pulsador de timbre', 'Przycisk dzwonka'),
    'dimmer': ('Snúningsdimmer', 'Rotary dimmer', 'Regulador giratorio', 'Ściemniacz obrotowy'),
    'blank': ('Blindlok', 'Blank cover', 'Tapa ciega', 'Zaślepka'),
    'touch1': ('Snjallrofi', 'Smart switch', 'Interruptor inteligente', 'Włącznik smart'),
    'touch2': ('Snjallrofi, tvöfaldur', 'Smart switch, double', 'Interruptor inteligente doble', 'Włącznik smart podwójny'),
    'touch3': ('Snjallrofi, þrefaldur', 'Smart switch, triple', 'Interruptor inteligente triple', 'Włącznik smart potrójny'),
    'touch4': ('Snjallrofi, fjórfaldur', 'Smart switch, four gangs', 'Interruptor inteligente cuádruple', 'Włącznik smart poczwórny'),
    'tdim': ('Snjalldimmer', 'Smart dimmer', 'Regulador inteligente', 'Ściemniacz smart'),
    'ssocket': ('Snjalltengill', 'Smart socket', 'Enchufe inteligente', 'Gniazdko smart'),
    'sblind': ('Snjallrofi fyrir rúllugardínur', 'Smart blind switch', 'Interruptor inteligente de persianas', 'Włącznik smart do rolet'),
    'scurtain': ('Snjallrofi fyrir gardínur', 'Smart curtain switch', 'Interruptor inteligente de cortinas', 'Włącznik smart do zasłon'),
    'heatw': ('Hitastillir, vatnshiti', 'Thermostat, water heating', 'Termostato, calefacción por agua', 'Termostat, ogrzewanie wodne'),
    'heate': ('Hitastillir, rafhiti', 'Thermostat, electric heating', 'Termostato, calefacción eléctrica', 'Termostat, ogrzewanie elektryczne'),
}
UI = {
    'title': ('Sjáðu línurnar á vegg', 'See the lines on a wall', 'Mira las líneas en una pared', 'Zobacz linie na ścianie'),
    'help': ('Veldu línu, lit á vegg og lit á efninu. Hver mynd er einn hlutur sem línan býður; ýttu á rofa til að prófa hann.',
             'Pick a line, a wall colour and a colour for the fittings. Each picture is one part the line offers; press a switch to try it.',
             'Elige una línea, un color de pared y un color para el material. Cada dibujo es una pieza que ofrece la línea; pulsa un interruptor para probarlo.',
             'Wybierz linię, kolor ściany i kolor osprzętu. Każdy rysunek to jedna część, którą oferuje linia; naciśnij włącznik, aby go wypróbować.'),
    'line': ('Lína', 'Line', 'Línea', 'Linia'),
    'view': ('Sýn', 'View', 'Vista', 'Widok'),
    'draw': ('Teikning', 'Drawing', 'Dibujo', 'Rysunek'),
    'three': ('Þrívídd', '3D', '3D', '3D'),
    'wall': ('Veggur', 'Wall', 'Pared', 'Ściana'),
    'fit': ('Litur', 'Colour', 'Color', 'Kolor'),
    'combo': ('Saman í einum ramma', 'Together in one frame', 'Juntos en un marco', 'Razem w jednej ramce'),
    'units': ('Rammar taldir í einingum, fyrir ferkantaðar dósir', 'Frames counted in units, for square boxes', 'Marcos contados en módulos, para cajas cuadradas', 'Ramki liczone w modułach, do puszek prostokątnych'),
    'smart': ('Snjallhlutir', 'Smart parts', 'Piezas inteligentes', 'Części smart'),
    'note': ('Teikningar og tölvugerðar þrívíddarmyndir, ekki ljósmyndir: þær sýna gerð, stærð og lögun hlutanna, ekki nákvæmt útlit. Ekki fást allir hlutir í öllum litum.',
             'Drawings and computer-made 3D pictures, not photographs: they show the kind, the size and the shape of the parts, not their exact look. Not every part comes in every colour.',
             'Dibujos e imágenes 3D hechas por ordenador, no fotografías: muestran el tipo, el tamaño y la forma de las piezas, no su aspecto exacto. No todas las piezas existen en todos los colores.',
             'Rysunki i komputerowe obrazy 3D, nie zdjęcia: pokazują rodzaj, rozmiar i kształt części, a nie ich dokładny wygląd. Nie każda część jest dostępna w każdym kolorze.'),
}
# Mosaic's frames counted in units (FIT_LINES.mosaic.frames.square in the estimate: 3, 4, 5, 6 and 8 units in one row): three of them, filled
UNIT_FRAMES = [('u3', [('sw', 1), ('socket', 2)]), ('u4', [('sw1', 2), ('socket', 2)]), ('u6', [('socket', 2), ('socket', 2), ('sw', 1), ('sw', 1)])]
UNIT_NAMES = {
    'u3': ('Þrjár einingar: mjór rofi og tengill', 'Three units: a narrow switch and a socket', 'Tres módulos: un interruptor estrecho y un enchufe', 'Trzy moduły: wąski łącznik i gniazdko'),
    'u4': ('Fjórar einingar: rofi og tengill', 'Four units: a switch and a socket', 'Cuatro módulos: un interruptor y un enchufe', 'Cztery moduły: łącznik i gniazdko'),
    'u6': ('Sex einingar: tveir tenglar og tveir mjóir rofar', 'Six units: two sockets and two narrow switches', 'Seis módulos: dos enchufes y dos interruptores estrechos', 'Sześć modułów: dwa gniazdka i dwa wąskie łączniki'),
}
WALLS = [('white', '#f3f1ec', ('Hvítur veggur', 'White wall', 'Pared blanca', 'Biała ściana')),
         ('grey', '#cfd2d4', ('Ljósgrár veggur', 'Light grey wall', 'Pared gris claro', 'Jasnoszara ściana')),
         ('sand', '#d8c7a8', ('Sandlitaður veggur', 'Sand-coloured wall', 'Pared color arena', 'Piaskowa ściana')),
         ('green', '#8fa58c', ('Grænn veggur', 'Green wall', 'Pared verde', 'Zielona ściana')),
         ('blue', '#2f4a63', ('Blár veggur', 'Blue wall', 'Pared azul', 'Niebieska ściana')),
         ('dark', '#2b2e33', ('Dökkur veggur', 'Dark wall', 'Pared oscura', 'Ciemna ściana'))]
FITS = [('white', ('Hvítt', 'White', 'Blanco', 'Biały')), ('black', ('Svart', 'Black', 'Negro', 'Czarny')),
        ('grey', ('Grátt', 'Grey', 'Gris', 'Szary')), ('gold', ('Gyllt', 'Gold', 'Dorado', 'Złoty'))]
# line: (tab name, colours, the plain parts, the smart parts, frames of several positions)
LINES = [
    ('mosaic', 'Legrand Mosaic N', ['white'], ['sw1', 'sw2', 'socket', 'socket_usb', 'usb', 'net', 'net2', 'tv', 'blank'], [], [['sw2', 'socket'], ['socket', 'socket', 'socket']]),
    ('valena', 'Legrand Valena', ['white'], ['sw1', 'sw2', 'sw3', 'socket', 'socket_usb', 'usb', 'net', 'net2', 'tv', 'blind', 'blank'], [], [['sw3', 'socket'], ['sw1', 'sw2', 'socket']]),
    ('merten', 'Merten System M', ['white'], ['sw1', 'sw2', 'socket', 'socket_usb', 'net', 'hdmi', 'blind', 'blank'], [], [['sw2', 'socket'], ['socket', 'socket', 'net']]),
    ('bseed_glass', 'BSEED gler', ['white', 'black', 'grey', 'gold'], ['sw1', 'sw2', 'sw3', 'socket', 'socket_usb', 'socket_cover', 'socket_usb2', 'charger65', 'blind', 'bell', 'dimmer'],
     ['touch1', 'touch2', 'touch3', 'touch4', 'tdim', 'ssocket', 'sblind', 'scurtain'], [['touch2', 'socket'], ['touch3', 'tdim', 'socket_usb']]),
    ('bseed_plastic', 'BSEED plast', ['white', 'black', 'grey', 'gold'],
     ['sw1', 'sw2', 'neon1', 'neon2', 'socket', 'socket_usb', 'socket_cover', 'socket_usb2', 'charger65', 'net', 'net2', 'tv', 'sat', 'tel', 'hdmi', 'blind', 'fan', 'bell', 'dimmer', 'blank'],
     ['touch1', 'touch2', 'touch3', 'touch4', 'tdim', 'ssocket', 'sblind', 'scurtain', 'heatw', 'heate'], [['sw2', 'socket'], ['touch2', 'sblind', 'socket', 'net']]),
]


def word(cx, t, size=8, y=57):
    return f'<text class="f" x="{cx}" y="{y}" text-anchor="middle" font-size="{size}" font-weight="700">{t}</text>'


def socket(cx, cy=36, r=20):
    d = r * 0.4
    return (f'<circle class="d" cx="{cx}" cy="{cy}" r="{r}"/><circle class="f" cx="{cx - d}" cy="{cy}" r="2.6"/><circle class="f" cx="{cx + d}" cy="{cy}" r="2.6"/>'
            f'<rect class="f" x="{cx - 1.6}" y="{cy - r}" width="3.2" height="5" rx="1"/><rect class="f" x="{cx - 1.6}" y="{cy + r - 5}" width="3.2" height="5" rx="1"/>')


def jack(cx, cy=34, h=9):
    return f'<path class="d" d="M{cx - h} {cy - 7}h{2 * h}v13h-{h / 2}v4h-{h}v-4h-{h / 2}z"/>' + ''.join(f'<line class="i" x1="{cx + f * h}" y1="{cy - 7}" x2="{cx + f * h}" y2="{cy - 2}"/>' for f in (-0.5, 0, 0.5))


def rockers(x, g, lamp=False):
    """g rockers side by side in the position that starts at x: each can be pressed (site.js toggles .on, the style sheet tilts the shading)."""
    w = (C - 6) / g
    s = ''
    for n in range(g):
        x0 = x + 3 + n * w
        s += (f'<g class="rock"><rect class="k" x="{x0}" y="9" width="{w}" height="54" rx="2.5"/><rect class="sh a" x="{x0}" y="9" width="{w}" height="27" rx="2.5"/>'
              f'<rect class="sh b" x="{x0}" y="36" width="{w}" height="27" rx="2.5"/><line class="i" x1="{x0 + w / 2 - 4}" y1="17" x2="{x0 + w / 2 + 4}" y2="17"/>'
              + (f'<circle class="lamp" cx="{x0 + w / 2}" cy="54" r="2.4"/>' if lamp else '') + '</g>')
    return s


def touch(x, g, mark=''):
    """a glass or flat smart key with a ring per gang, which lights when pressed"""
    cx = x + C / 2
    spots = {1: [(0, 0)], 2: [(-12, 0), (12, 0)], 3: [(-15, 0), (0, 0), (15, 0)], 4: [(-12, -12), (12, -12), (-12, 12), (12, 12)]}[g]
    return f'<rect class="k" x="{x + 3}" y="9" width="{C - 6}" height="54" rx="2.5"/>' + ''.join(f'<g class="rock"><rect class="hit" x="{cx + a - 11}" y="{36 + b - 11}" width="22" height="22"/><circle class="led" cx="{cx + a}" cy="{36 + b}" r="5.5"/></g>' for a, b in spots) + mark


def key(x):
    return f'<rect class="k" x="{x + 3}" y="9" width="{C - 6}" height="54" rx="2.5"/>'


def glyph(k, x):
    cx = x + C / 2
    if k in ('sw1', 'sw2', 'sw3'):
        return rockers(x, int(k[2]))
    if k in ('neon1', 'neon2'):
        return rockers(x, int(k[4]), True)
    if k in ('touch1', 'touch2', 'touch3', 'touch4'):
        return touch(x, int(k[5]))
    if k == 'tdim':
        return key(x) + f'<g class="rock"><rect class="hit" x="{cx - 14}" y="22" width="28" height="28"/><circle class="led" cx="{cx}" cy="36" r="9"/></g><path class="i" d="M{cx - 16} 56h32"/><path class="f" d="M{cx - 16} 56l32 -5v5z"/>'
    if k == 'socket':
        return key(x) + socket(cx)
    if k == 'ssocket':
        return key(x) + socket(cx) + f'<circle class="led on" cx="{x + C - 11}" cy="16" r="2.6"/>'
    if k == 'socket_usb':
        return key(x) + socket(cx, 31, 17) + f'<rect class="d" x="{cx - 6}" y="53" width="12" height="5" rx="2.5"/>'
    if k == 'socket_usb2':
        return key(x) + socket(cx, 31, 17) + f'<rect class="d" x="{cx - 12}" y="53" width="10" height="5" rx="1"/><rect class="d" x="{cx + 2}" y="53" width="10" height="5" rx="1"/>'
    if k == 'socket_cover':
        return key(x) + socket(cx) + f'<path class="lid" d="M{cx - 21} 36a21 21 0 0 1 42 0z"/><line class="i" x1="{cx - 21}" y1="36" x2="{cx + 21}" y2="36"/>'
    if k == 'usb':
        return key(x) + f'<rect class="d" x="{cx - 8}" y="20" width="16" height="8" rx="1.5"/><rect class="d" x="{cx - 8}" y="34" width="16" height="8" rx="4"/>' + word(cx, 'USB')
    if k == 'charger65':
        return key(x) + f'<rect class="d" x="{cx - 8}" y="14" width="16" height="7" rx="1.5"/><rect class="d" x="{cx - 8}" y="25" width="16" height="7" rx="3.5"/><rect class="d" x="{cx - 8}" y="36" width="16" height="7" rx="3.5"/>' + word(cx, '65W')
    if k == 'net':
        return key(x) + jack(cx)
    if k == 'net2':
        return key(x) + jack(cx - 12, 34, 7) + jack(cx + 12, 34, 7)
    if k in ('tv', 'sat'):
        return key(x) + f'<circle class="d" cx="{cx}" cy="31" r="9"/><circle class="f" cx="{cx}" cy="31" r="2.6"/>' + (f'<circle class="i" cx="{cx}" cy="31" r="5.5"/>' if k == 'sat' else '') + word(cx, 'TV' if k == 'tv' else 'SAT')
    if k == 'tel':
        return key(x) + f'<path class="d" d="M{cx - 8} 22h16v12h-4.5v5h-7v-5h-4.5z"/>' + word(cx, 'TEL')
    if k == 'hdmi':
        return key(x) + f'<path class="d" d="M{cx - 12} 24h24v8l-4 6h-16l-4-6z"/>' + word(cx, 'HDMI', 7)
    if k == 'blind':
        w = (C - 6) / 2
        return ''.join(f'<g class="rock"><rect class="k" x="{x + 3 + n * w}" y="9" width="{w}" height="54" rx="2.5"/><rect class="sh a" x="{x + 3 + n * w}" y="9" width="{w}" height="27" rx="2.5"/><rect class="sh b" x="{x + 3 + n * w}" y="36" width="{w}" height="27" rx="2.5"/>'
                       f'<path class="f" d="M{x + 3 + (n + 0.5) * w - 5} {39 if n else 33}l5 {7 if n else -7}l5 {-7 if n else 7}z"/></g>' for n in (0, 1))
    if k in ('sblind', 'scurtain'):
        arrows = (f'<path class="f" d="M{cx - 5} 26l5-7l5 7z"/><path class="f" d="M{cx - 5} 46l5 7l5-7z"/>' if k == 'sblind' else f'<path class="f" d="M{cx - 9} 36l7-5v10z"/><path class="f" d="M{cx + 9} 36l-7-5v10z"/>')
        return key(x) + arrows + (f'<g class="rock"><rect class="hit" x="{cx - 8}" y="28" width="16" height="16"/><circle class="led" cx="{cx}" cy="36" r="4"/></g>' if k == 'sblind' else f'<g class="rock"><rect class="hit" x="{cx - 8}" y="46" width="16" height="12"/><circle class="led" cx="{cx}" cy="52" r="3.5"/></g>')
    if k == 'fan':
        return key(x) + f'<circle class="d" cx="{cx}" cy="38" r="14"/><line class="knob" x1="{cx}" y1="38" x2="{cx + 7}" y2="28"/>' + ''.join(f'<circle class="f" cx="{cx + a}" cy="{b}" r="1.4"/>' for a, b in ((-17, 30), (-9, 18), (9, 18), (17, 30)))
    if k == 'dimmer':
        return key(x) + f'<circle class="d" cx="{cx}" cy="36" r="17"/><circle class="k" cx="{cx}" cy="36" r="12"/><line class="knob" x1="{cx}" y1="36" x2="{cx + 6}" y2="27"/>'
    if k == 'bell':
        return f'<g class="rock">{key(x)}<rect class="sh a" x="{x + 3}" y="9" width="{C - 6}" height="27" rx="2.5"/><rect class="sh b" x="{x + 3}" y="36" width="{C - 6}" height="27" rx="2.5"/><path class="f" d="M{cx - 9} 42c3-3 3-6 3-10a6 6 0 0 1 12 0c0 4 0 7 3 10z"/><circle class="f" cx="{cx}" cy="46" r="2"/></g>'
    if k in ('heatw', 'heate'):
        wave = f'<path class="i" d="M{cx - 9} 55q4.5-4 9 0t9 0"/>' if k == 'heatw' else f'<path class="i" d="M{cx - 9} 56l4.5-3l4.5 3l4.5-3l4.5 3"/>'
        return key(x) + f'<rect class="d" x="{cx - 17}" y="15" width="34" height="26" rx="3"/><text class="f" x="{cx}" y="34" text-anchor="middle" font-size="14" font-weight="700">21°</text>' + wave
    return key(x)  # a blank cover


def plate(w, h, shaped):
    """the frame's own outline: a rounded rectangle whose radius the style sheet sets, or Mosaic's plate, whose lower corners are rounder than its upper"""
    if not shaped:
        return f'<rect class="plate" x="0.5" y="0.5" width="{w - 1}" height="{h - 1}"/><rect class="gloss" x="0.5" y="0.5" width="{w - 1}" height="{h - 1}"/>'
    a, b = 4, 11
    return (f'<path class="plate" d="M{a} .5H{w - a}A{a} {a} 0 0 1 {w - .5} {a}V{h - b}A{b} {b} 0 0 1 {w - b} {h - .5}H{b}A{b} {b} 0 0 1 .5 {h - b}V{a}A{a} {a} 0 0 1 {a} .5Z"/>'
            f'<path class="band" d="M{a + 2} 5H{w - a - 2}"/>')


# The 3D picture of a frame (tools/lines3d: lines3d.py --batch, then to_webp.py): img/lines3d/<line>-<fit>-<file>.webp, the frame with MARGIN mm of
# see-through wall round it for its shadow. The picture has no src here: site.js sets it when the 3D view is chosen, so nobody who keeps to the drawings
# downloads one. --k is how much wider the picture is than its frame, which the style sheet uses to lay the frame where the drawing's is
MARGIN = 12
SIZES = {'mosaic': 82, 'valena': 86, 'merten': 80.5, 'bseed_glass': 86, 'bseed_plastic': 86}


def pic(line, file, width_mm):
    k = (width_mm + 2 * MARGIN) / width_mm
    w, h = round((width_mm + 2 * MARGIN) * 4), round((SIZES[line] + 2 * MARGIN) * 4)
    return f'<img class="lv-pic" alt="" data-file="{file}" width="{w}" height="{h}" style="--k:{k:.3f}" decoding="async">'


U, UH = 24, 48  # a unit of a Mosaic frame counted in units (22.5 mm wide, 45 high), as drawn


def unit_frame(mods):
    """a Mosaic frame counted in units (owner 2026-11-25: the 3 and 4 unit frames): one plate with one long opening, its modules side by side, each one
    unit wide (a narrow switch, a narrow network outlet, a narrow blank cover) or two (everything else)"""
    n = sum(u for _k, u in mods)
    w, h = U * n + 36, 74
    body, x = '', 18
    for k, u in mods:
        if u == 2:
            sc = UH / 54
            body += f'<g transform="translate({x - 3 * sc:.2f} {13 - 9 * sc:.2f}) scale({sc:.4f})">{glyph(k, 0)}</g>'
        elif k == 'sw':
            body += (f'<g class="rock"><rect class="k" x="{x}" y="13" width="{U}" height="{UH}" rx="2"/><rect class="sh a" x="{x}" y="13" width="{U}" height="{UH / 2}" rx="2"/>'
                     f'<rect class="sh b" x="{x}" y="{13 + UH / 2}" width="{U}" height="{UH / 2}" rx="2"/><line class="i" x1="{x + U / 2 - 3.5}" y1="20" x2="{x + U / 2 + 3.5}" y2="20"/></g>')
        elif k == 'net':
            body += f'<rect class="k" x="{x}" y="13" width="{U}" height="{UH}" rx="2"/>' + jack(x + U / 2, 36, 7)
        else:
            body += f'<rect class="k" x="{x}" y="13" width="{U}" height="{UH}" rx="2"/>'
        x += U * u
    return f'<svg class="lv-svg" viewBox="0 0 {w} {h}" style="--n:{(w - 14) / C:.3f}" aria-hidden="true">{plate(w, h, True)}{body}</svg>'


def frame(kinds, shaped=False):
    n = len(kinds)
    w, h = C * n + 2 * PAD, 72 + 2 * PAD - 12
    # each part in a group of its own, so that the style sheet can draw it smaller in its frame where the line's centre part is (Mosaic's 45 mm module)
    body = ''.join(f'<g transform="translate({PAD + i * C} {PAD - 6})"><g class="cell">{glyph(k, 0)}</g></g>' for i, k in enumerate(kinds))
    return f'<svg class="lv-svg" viewBox="0 0 {w} {h}" style="--n:{n}" aria-hidden="true">{plate(w, h, shaped)}{body}</svg>'


def fig(kinds, shaped=False, line=''):
    cap = ' + '.join(NAMES[k][0] for k in kinds) if len(kinds) == 1 else None
    names = ' + '.join(NAMES[k][0] for k in kinds)
    inner = f'<figcaption>{NAMES[kinds[0]][0]}</figcaption>' if cap else ''.join(f'<span>{NAMES[k][0]}</span>' for k in kinds)
    photo = pic(line, '_'.join(kinds), SIZES[line] + 71 * (len(kinds) - 1)) if line else ''
    return f'<figure class="lv-fig{" wide" if len(kinds) > 1 else ""}" style="--n:{len(kinds)}">{frame(kinds, shaped)}{photo}' + (inner if cap else f'<figcaption>{inner}</figcaption>') + '</figure>'


def build():
    t = lambda k: UI[k][0]
    out = ['<!-- lines-view:start (written by tools/lines_view.py, do not edit by hand) -->',
           f'    <div class="lv" data-line="{LINES[0][0]}" data-fit="white">',
           f'      <h3>{t("title")}</h3><p class="muted">{t("help")}</p>',
           '      <div class="lv-bar"><span class="lv-lab">' + t('line') + '</span>' + ''.join(f'<button type="button" class="lv-tab" data-line="{i}" data-fits="{" ".join(f)}" aria-pressed="{"true" if n == 0 else "false"}">{name}</button>' for n, (i, name, f, *_r) in enumerate(LINES)) + '</div>',
           '      <div class="lv-bar"><span class="lv-lab">' + t('wall') + '</span>' + ''.join(f'<button type="button" class="lv-sw" data-wall="{c}" style="--c:{c}" aria-label="{n[0]}" title="{n[0]}" aria-pressed="{"true" if i == 0 else "false"}"></button>' for i, (_k, c, n) in enumerate(WALLS)) + '</div>',
           '      <div class="lv-bar lv-fits"><span class="lv-lab">' + t('fit') + '</span>' + ''.join(f'<button type="button" class="lv-fit" data-fit="{k}" aria-pressed="{"true" if i == 0 else "false"}">{n[0]}</button>' for i, (k, n) in enumerate(FITS)) + '</div>',
           '      <div class="lv-bar lv-modes"><span class="lv-lab">' + t('view') + '</span><button type="button" class="lv-mode" data-mode="draw" aria-pressed="true">' + t('draw') + '</button><button type="button" class="lv-mode" data-mode="3d" aria-pressed="false">' + t('three') + '</button></div>',
           '      <div class="lv-wall">']
    for i, name, _f, plain, smart, combos in LINES:
        sh = i == 'mosaic'
        out.append(f'        <div class="lv-set" data-set="{i}"><h4>{name}</h4><div class="lv-grid">' + ''.join(fig([k], sh, i) for k in plain) + '</div>'
                   + (f'<h5>{t("smart")}</h5><div class="lv-grid">' + ''.join(fig([k], False, i) for k in smart) + '</div>' if smart else '')
                   + f'<h5>{t("combo")}</h5><div class="lv-grid">' + ''.join(fig(c, sh, i) for c in combos) + '</div>'
                   + (f'<h5>{t("units")}</h5><div class="lv-grid">' + ''.join(f'<figure class="lv-fig wide" style="--n:{(U * sum(u for _k, u in m) + 22) / C:.3f}">{unit_frame(m)}{pic(i, k, sum(u for _k, u in m) * 22.5 + 36.5)}<figcaption>{UNIT_NAMES[k][0]}</figcaption></figure>' for k, m in UNIT_FRAMES) + '</div>' if sh else '')
                   + '</div>')
    out += ['      </div>', f'      <p class="muted small">{t("note")}</p>', '    </div>', '    <!-- lines-view:end -->']
    return '\n'.join(out)


def main():
    p = os.path.join(ROOT, 'index.html')
    s = io.open(p, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in s else '\n'
    block = build().replace('\n', nl)
    a, b = s.find('<!-- lines-view:start'), s.find('<!-- lines-view:end -->')
    if a >= 0 and b > a:
        s = s[:a] + block + s[b + len('<!-- lines-view:end -->'):]
    else:  # the first time: above the cards of the section
        sec = s.index('<section id="innlagnaefni"')
        at = s.index('<div class="systems">', sec)
        s = s[:at] + block + nl + '    ' + s[at:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    texts = list(NAMES.values()) + list(UI.values()) + list(UNIT_NAMES.values()) + [n for _k, _c, n in WALLS] + [n for _k, n in FITS] + [(name,) * 4 for _i, name, *_r in LINES]
    for col, lang in enumerate(('en', 'es', 'pl'), 1):
        f = os.path.join(ROOT, 'i18n', lang + '.json')
        raw = io.open(f, encoding='utf-8', newline='').read()
        have = json.loads(raw)
        add = [(x[0], x[col]) for x in texts if x[0] not in have]
        add = list(dict(add).items())
        if add:
            n2 = '\r\n' if '\r\n' in raw else '\n'
            end = raw.rstrip().rindex('}')
            io.open(f, 'w', encoding='utf-8', newline='').write(raw[:end].rstrip() + ''.join(',' + n2 + '  ' + json.dumps(k, ensure_ascii=False) + ': ' + json.dumps(v, ensure_ascii=False) for k, v in add) + n2 + '}' + n2)
        print(lang, len(add), 'texts added')


if __name__ == '__main__':
    main()
