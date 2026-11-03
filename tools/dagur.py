"""Write the 'Einn dagur' scene player into index.html (the SVG between the dagur markers) and site.css (the block from
'/* Dagur:' to the end of the file). The same sample house as the intro; the scene state lives on the section's
data-scene attribute (site.js sets it), the CSS turns lights, glows and the per-scene extras on and off.
Run from the repo root: python tools/dagur.py [copy.html]  (the optional copy is the single-file artifact)."""
import re, sys, os

L = {'stofa': (140, 145), 'eldhus': (325, 145), 'herbergi': (485, 115), 'bad': (485, 305), 'forstofa': (215, 335)}
NAMES = [('Stofa', 140, 175), ('Eldhús', 325, 175), ('Herbergi', 485, 145), ('Baðherbergi', 485, 335), ('Forstofa', 215, 365)]
SCENES = 7

def house():
    s = ['<defs><radialGradient id="dglow"><stop offset="0" stop-color="var(--accent)" stop-opacity="1"/><stop offset="1" stop-color="var(--accent)" stop-opacity="0"/></radialGradient></defs>', '<g class="dh">']
    s.append('<path class="w" d="M30 30H570V410H30Z"/>')
    for d in ['M250 30V260', 'M30 260H400', 'M400 30V410', 'M400 200H570']:
        s.append(f'<path class="w i" d="{d}"/>')
    for cut, lines in [('M80 30H160', 'M80 26H160M80 34H160'), ('M300 30H370', 'M300 26H370M300 34H370'), ('M440 30H520', 'M440 26H520M440 34H520'),
                       ('M30 100V180', 'M26 100V180M34 100V180'), ('M570 260V340', 'M566 260V340M574 260V340')]:
        s.append(f'<path class="cut" d="{cut}"/><path class="thin" d="{lines}"/>')
    for cut, leaf, arc in [('M180 410H230', 'M180 410V360', 'M180 360A50 50 0 0 1 230 410'), ('M120 260H170', 'M120 260V210', 'M120 210A50 50 0 0 1 170 260'),
                           ('M300 260H350', 'M350 260V210', 'M350 210A50 50 0 0 0 300 260'), ('M400 80V130', 'M400 80H450', 'M450 80A50 50 0 0 1 400 130'),
                           ('M400 300V350', 'M400 350H450', 'M450 350A50 50 0 0 0 400 300')]:
        s.append(f'<path class="cut" d="{cut}"/><path class="thin" d="{leaf}"/><path class="thin" d="{arc}"/>')
    for n, x, y in NAMES:
        s.append(f'<text x="{x}" y="{y}">{n}</text>')
    s.append('<path class="e" d="M44 374H76V406H44ZM44 374L76 406M76 374L44 406"/><text class="lbl" x="60" y="420">T1</text>')
    for x, y, dx, dy in [(150, 410, 0, -1), (100, 260, 0, -1), (370, 260, 0, -1), (400, 150, 1, 0), (400, 370, 1, 0)]:
        cx, cy = x + dx * 7, y + dy * 7
        s.append(f'<path class="e" d="M{cx} {cy}m-5 0a5 5 0 1 0 10 0a5 5 0 1 0-10 0M{cx + dx * 5} {cy + dy * 5}l{dx * 12} {dy * 12}l{dy * 5} {-dx * 5}"/>')
    for x, y, dx, dy in [(60, 30, 0, 1), (200, 30, 0, 1), (250, 120, -1, 0), (570, 100, -1, 0), (520, 410, 0, -1), (320, 410, 0, -1)]:
        cx, cy = x + dx * 8, y + dy * 8
        s.append(f'<path class="e" d="M{cx - dy * 8} {cy - dx * 8}a8 8 0 0 {1 if (dx + dy) > 0 else 0} {dy * 16} {dx * 16}M{cx} {cy}l{dx * 10} {dy * 10}"/>')
    # lights: a glow and the X, driven by --lv (0..1) from the scene rules
    for k, (x, y) in L.items():
        s.append(f'<g class="lt" id="dl-{k}"><circle class="glow" cx="{x}" cy="{y}" r="60"/>'
                 f'<path class="e x" d="M{x - 9} {y - 9}L{x + 9} {y + 9}M{x + 9} {y - 9}L{x - 9} {y + 9}"/></g>')
    # under-cabinet strip in Eldhús, its own group
    s.append('<g class="lt" id="dl-strip"><rect class="glow" x="372" y="56" width="22" height="190" rx="10"/><path class="e x" stroke-dasharray="6 5" d="M384 60V240"/></g>')
    s.append('</g>')
    return '\n    '.join(s)

def bubble(x, y, w, text, cls=''):
    return f'<rect class="bub" x="{x}" y="{y}" width="{w}" height="30" rx="8"/><text class="mid {cls}" x="{x + w / 2:.0f}" y="{y + 21}">{text}</text>'

extras = {
    1: f'<circle class="e" cx="485" cy="90" r="13"/><path class="e" d="M485 90V81M485 90L491 94"/><path class="e ring" d="M470 74l-5-5M500 74l5-5"/>'
       f'{bubble(445, 36, 80, "04:50")}<text class="lbl" x="520" y="300">10 %</text><text class="lbl" x="355" y="150">10 %</text>',
    2: f'<circle class="e" cx="370" cy="253" r="14" stroke-dasharray="3 3"/><path class="e" d="M300 215h50M350 215l-6-5M350 215l-6 5"/>'
       f'<text class="lbl" x="325" y="130">60 %</text>{bubble(215, 190, 150, "haldið inni = dimmað")}',
    3: f'<circle class="e" cx="150" cy="403" r="14" stroke-dasharray="3 3"/><path class="e" d="M205 418v26M205 444l-6-6M205 444l6-6"/>'
       f'{bubble(230, 290, 110, "Allt af")}<text class="lbl" x="285" y="112">straujárn af</text>',
    4: '<path class="thin" d="M100 350H330M100 350V290"/>'
       + ''.join(f'<rect class="bar" style="--i:{i}" x="{106 + i * 15}" y="{350 - h * 1.6:.0f}" width="10" height="{h * 1.6:.0f}"/>'
                 for i, h in enumerate([3, 5, 4, 22, 12, 6, 5, 4, 4, 5, 9, 26, 34, 18, 8]))
       + '<text class="lbl" x="215" y="282">kWh í dag</text><text class="ax" x="106" y="368">00</text><text class="ax" x="215" y="368">12</text><text class="ax" x="324" y="368">24</text>'
         '<path class="e" d="M76 390Q90 390 100 350"/>',
    5: f'<path class="e curt" pathLength="1" d="M40 104v72M44 104v72M48 104v72"/><g class="sun"><circle class="e" cx="20" cy="140" r="8"/><path class="e" d="M20 128v-4M20 156v-4M8 140h-4M32 140h4"/></g>'
       f'<text class="lbl" x="140" y="130">kvöldstilling</text>{bubble(420, 230, 60, "21 °C")}',
    6: f'<text class="lbl" x="250" y="330">10 %</text><path class="e" d="M520 388l12 0l-6 -11z"/><text class="lbl" x="526" y="372">!</text>'
       f'<circle class="e ring1" cx="526" cy="382" r="18"/><circle class="e ring2" cx="526" cy="382" r="28"/>'
       f'<g class="note"><rect class="bub" x="300" y="42" width="110" height="60" rx="10"/><text class="mid sm" x="355" y="66">Snjallheimilið</text><text class="mid sb" x="355" y="88">Vatn í baðherbergi</text></g>',
    7: '<text class="big" x="300" y="200">Snjallheimilið</text><text class="mid" x="300" y="236">Allt á heimanetinu, engin áskrift.</text>'
       '<rect class="bub" x="200" y="262" width="200" height="40" rx="20"/><text class="mid sb" x="300" y="288">Fáðu verðbil á 2 mínútum</text>',
}
svg = ('<svg class="dsvg" viewBox="0 0 600 440" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">\n    '
       + house() + '\n' + '\n'.join(f'    <g class="sc" data-s="{i}">{extras[i]}</g>' for i in range(1, SCENES + 1)) + '\n  </svg>')

# light levels per scene (the storyboard's frames)
levels = {1: {'bad': .15, 'strip': .15}, 2: {'eldhus': .6, 'strip': 1, 'stofa': .5, 'bad': .5, 'forstofa': .5}, 3: {}, 4: {},
          5: {'stofa': .7, 'eldhus': .35, 'forstofa': .3}, 6: {'forstofa': .12}, 7: {k: .4 for k in L}}
rules = []
for i in range(1, SCENES + 1):
    vals = ' '.join(f'--{k}:{v};' for k, v in levels[i].items())
    rules.append(f'.dagur[data-scene="{i}"] {{ {vals} }}')
# scene 3: the lights go off one after another, Herbergi first, Forstofa last
for n, k in enumerate(['herbergi', 'bad', 'eldhus', 'strip', 'stofa', 'forstofa']):
    rules.append(f'.dagur[data-scene="3"] #dl-{k} * {{ transition-delay: {0.3 + n * 0.35:.2f}s; }}')

css = f'''/* Dagur: the 'Einn dagur í snjallheimili' scene player (owner 2026-11-03): the sample house again, seven scenes;
   site.js sets data-scene on the section (auto-advance while in view, the dots jump), the rules below set each light's
   level --lv through a per-light variable, show the scene's extras (.sc[data-s]) and run the small keyframes.
   Generated by tools/dagur.py; edit the script and rerun it. */
.dagur {{ display: grid; gap: 14px; margin-top: 16px; }}
.dsvg {{ width: 100%; height: auto; background: var(--card); border: 1px solid var(--line); border-radius: 14px; display: block; }}
.dsvg text {{ font: 15px system-ui, "Segoe UI", sans-serif; fill: var(--muted); text-anchor: middle; }}
.dsvg .w {{ stroke: var(--text); fill: none; stroke-width: 7; stroke-linejoin: round; }} .dsvg .i {{ stroke-width: 4; }}
.dsvg .cut {{ stroke: var(--card); stroke-width: 9; }}
.dsvg .thin {{ stroke: var(--text); fill: none; stroke-width: 1.5; }}
.dsvg .e {{ stroke: var(--accent); fill: none; stroke-width: 2; stroke-linecap: round; }}
.dsvg .glow {{ fill: url(#dglow); }}
.dsvg .lbl {{ font-size: 12px; font-weight: 600; fill: var(--accent); }}
.dsvg .ax {{ font-size: 11px; }}
.dsvg .big {{ font-size: 26px; font-weight: 700; fill: var(--text); }}
.dsvg .mid {{ font-size: 17px; fill: var(--text); }} .dsvg .sm {{ font-size: 12px; }} .dsvg .sb {{ font-size: 13px; font-weight: 600; }}
.dsvg .bub {{ fill: var(--card); stroke: var(--accent); stroke-width: 1.5; }}
.dsvg .bar {{ fill: var(--accent); opacity: .8; transform-box: fill-box; transform-origin: bottom; }}
.dsvg .dh {{ transition: opacity 1s; }} .dagur[data-scene="7"] .dh {{ opacity: .18; }}
.dsvg .lt .glow {{ opacity: min(.85, calc(min(1, calc(var(--lv, 0) * 10)) * calc(.25 + var(--lv, 0) * .9))); transition: opacity .8s; }}
.dsvg .lt .x {{ opacity: calc(.3 + .7 * min(1, calc(var(--lv, 0) * 4))); transition: opacity .8s; }}
#dl-stofa {{ --lv: var(--stofa, 0); }} #dl-eldhus {{ --lv: var(--eldhus, 0); }} #dl-herbergi {{ --lv: var(--herbergi, 0); }}
#dl-bad {{ --lv: var(--bad, 0); }} #dl-forstofa {{ --lv: var(--forstofa, 0); }} #dl-strip {{ --lv: var(--strip, 0); }}
{chr(10).join(rules)}
.dsvg .sc {{ opacity: 0; transition: opacity .6s; }}
{', '.join(f'.dagur[data-scene="{i}"] .sc[data-s="{i}"]' for i in range(1, SCENES + 1))} {{ opacity: 1; }}
.dagur[data-scene="1"] .ring {{ animation: dgShake .5s ease-in-out 3; transform-box: fill-box; transform-origin: center; }}
.dagur[data-scene="4"] .bar {{ animation: dgGrow .5s ease-out both; animation-delay: calc(.3s + var(--i) * .08s); }}
.dagur[data-scene="5"] .curt {{ stroke-dasharray: 1; stroke-dashoffset: 1; animation: dgDraw 1.2s ease-out .6s forwards; }}
.dagur[data-scene="5"] .sun {{ animation: dgSet 2.4s ease-in .3s forwards; }}
.dagur[data-scene="6"] .ring1 {{ animation: dgPulse 1.6s ease-out infinite; transform-box: fill-box; transform-origin: center; }}
.dagur[data-scene="6"] .ring2 {{ animation: dgPulse 1.6s ease-out .5s infinite; transform-box: fill-box; transform-origin: center; }}
.dagur[data-scene="6"] .note {{ animation: dgDrop .6s ease-out 1s both; }}
.dagur[data-scene="7"] .sc[data-s="7"] {{ transition-delay: .8s; }}
@keyframes dgShake {{ 0%, 100% {{ transform: rotate(0); }} 25% {{ transform: rotate(-12deg); }} 75% {{ transform: rotate(12deg); }} }}
@keyframes dgGrow {{ from {{ transform: scaleY(0); }} to {{ transform: scaleY(1); }} }}
@keyframes dgDraw {{ to {{ stroke-dashoffset: 0; }} }}
@keyframes dgSet {{ to {{ transform: translateY(70px); opacity: 0; }} }}
@keyframes dgPulse {{ from {{ transform: scale(.6); opacity: .8; }} to {{ transform: scale(1.4); opacity: 0; }} }}
@keyframes dgDrop {{ from {{ transform: translateY(-50px); opacity: 0; }} to {{ transform: none; opacity: 1; }} }}
.dcap {{ display: grid; }} .dcap > div {{ grid-area: 1 / 1; opacity: 0; transition: opacity .9s; }}
.dcap > div.on {{ opacity: 1; }}
.dcap .t {{ color: var(--accent); font-weight: 700; font-variant-numeric: tabular-nums; margin-right: 8px; }}
.dcap h3 {{ display: inline; font-size: 1.1rem; margin: 0; }} .dcap p {{ margin: 6px 0 0; }}
.dots {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
.dots button {{ width: 34px; height: 34px; border-radius: 50%; border: 1px solid var(--line); background: var(--card); color: var(--muted); font: inherit; font-size: .9rem; cursor: pointer; }}
.dots button[aria-current="true"] {{ background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }}
.dots .play {{ width: auto; border-radius: 17px; padding: 0 12px; margin-left: auto; }}
.d3 {{ position: relative; aspect-ratio: 600 / 440; max-width: 100%; border: 1px solid var(--line); border-radius: 14px; overflow: hidden; background: #0b1020; }}
.d3 canvas {{ display: block; width: 100% !important; height: 100% !important; }}
.dsvg.d3off {{ display: none; }}
.d3labels {{ position: absolute; inset: 0; pointer-events: none; }}
.d3time {{ position: absolute; left: 14px; top: 10px; pointer-events: none; color: #fff; font: 700 clamp(22px, 6vw, 38px) system-ui, "Segoe UI", sans-serif; font-variant-numeric: tabular-nums; letter-spacing: .02em; text-shadow: 0 0 18px rgba(245, 165, 36, .75), 0 1px 4px #000; transition: opacity .5s; }}
.d3 .lab {{ animation: none !important; position: absolute; transform: translate(-50%, -100%); opacity: 0; transition: opacity .6s; white-space: nowrap; font: 600 13px system-ui, "Segoe UI", sans-serif; }}
.d3 .lab.tag {{ color: #ffd28a; text-shadow: 0 1px 4px #000; }}
.d3 .lab.bub, .d3 .lab.note {{ background: rgba(20, 24, 32, .85); color: #fff; border: 1px solid #f5a524; border-radius: 8px; padding: 4px 9px; }}
.d3 .lab.note {{ border-radius: 10px; padding: 6px 12px; }} .d3 .lab.note::before {{ content: "Snjallheimilið"; display: block; font-weight: 400; font-size: 11px; color: #c9ced6; }}
.d3 .lab.end {{ left: 50%; top: 50%; transform: translate(-50%, -50%); text-align: center; white-space: normal; width: 80%; color: #fff; font-weight: 400; font-size: 15px; text-shadow: 0 1px 6px #000; }}
.d3 .lab.end b {{ display: block; font-size: 24px; margin-bottom: 4px; }} .d3 .lab.end span {{ display: inline-block; margin-top: 10px; background: #f5a524; color: #111; font-weight: 600; border-radius: 20px; padding: 8px 16px; }}
@media (prefers-reduced-motion: reduce) {{
  .dsvg *, .dcap > div {{ transition: none !important; animation: none !important; }}
  .dagur[data-scene="5"] .curt {{ stroke-dashoffset: 0; }}
}}
'''

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
def patch_html(path):
    s = open(path, encoding='utf-8').read()
    s2 = re.sub(r'<!-- dagur:svg -->.*?<!-- /dagur:svg -->', lambda m: '<!-- dagur:svg -->\n  ' + svg + '\n  <!-- /dagur:svg -->', s, count=1, flags=re.S)
    assert s2 != s or '<!-- dagur:svg -->' in s, 'no dagur markers in ' + path
    open(path, 'w', encoding='utf-8').write(s2)
patch_html('index.html')
c = open('site.css', encoding='utf-8').read()
i = c.find('/* Dagur:')
c = (c if i < 0 else c[:i]).rstrip('\n') + '\n\n' + css
open('site.css', 'w', encoding='utf-8').write(c)
if len(sys.argv) > 1:
    patch_html(sys.argv[1])
    a = open(sys.argv[1], encoding='utf-8').read()
    a = re.sub(r'<style>.*?</style>', lambda m: '<style>\n' + c + '\n</style>', a, count=1, flags=re.S)
    open(sys.argv[1], 'w', encoding='utf-8').write(a)
print('dagur written')
