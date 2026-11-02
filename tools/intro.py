"""Regenerate the hero intro SVG (run from the repo root: python tools/intro.py [copy.html]): the house as before, then the electrical layer drawn like a wiring drawing,
the run travelling from the board circuit by circuit, symbols appearing as the line reaches them."""
import math, os, re, sys

SPEED = 820.0          # plan px per second the run travels
els = []

def el(tag, d, cls, attrs, t=None):
    a = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
    st = f'--d:{d:.2f}s' + (f';--t:{t:.2f}s' if t else '')
    els.append(f'<{tag} class="{cls}" style="{st}" pathLength="1" {a}/>')

# ---- the house (as before) ----
el('path', 0.0, 'w o', {'d': 'M30 30H570V410H30Z'}, 1.3)
for i, d in enumerate(['M250 30V260', 'M30 260H400', 'M400 30V410', 'M400 200H570']):
    el('path', 1.3 + i * 0.3, 'w i', {'d': d}, 0.6)
wins = [('M80 30H160', 'M80 26H160M80 34H160'), ('M300 30H370', 'M300 26H370M300 34H370'), ('M440 30H520', 'M440 26H520M440 34H520'),
        ('M30 100V180', 'M26 100V180M34 100V180'), ('M570 260V340', 'M566 260V340M574 260V340')]
for i, (cut, lines) in enumerate(wins):
    t = 2.5 + i * 0.1
    els.append(f'<path class="cut" style="--d:{t:.2f}s" d="{cut}"/>')
    el('path', t, 'win', {'d': lines}, 0.5)
doors = [('M180 410H230', 'M180 410V360', 'M180 360A50 50 0 0 1 230 410'), ('M120 260H170', 'M120 260V210', 'M120 210A50 50 0 0 1 170 260'),
         ('M300 260H350', 'M350 260V210', 'M350 210A50 50 0 0 0 300 260'), ('M400 80V130', 'M400 80H450', 'M450 80A50 50 0 0 1 400 130'),
         ('M400 300V350', 'M400 350H450', 'M450 350A50 50 0 0 0 400 300')]
for i, (cut, leaf, swing) in enumerate(doors):
    t = 3.0 + i * 0.1
    els.append(f'<path class="cut" style="--d:{t:.2f}s" d="{cut}"/>')
    el('path', t, 'door', {'d': leaf}, 0.3)
    el('path', t + 0.1, 'door', {'d': swing}, 0.5)
for i, (n, x, y) in enumerate([('Stofa', 140, 145), ('Eldhús', 325, 145), ('Herbergi', 485, 115), ('Baðherbergi', 485, 305), ('Forstofa', 215, 335)]):
    els.append(f'<text class="rn" style="--d:{2.0 + i * 0.1:.2f}s" x="{x}" y="{y + 30}">{n}</text>')

# ---- the electrical layer: a pen that travels ----
clock = 3.6
def run(pts, cls='run'):
    """A smooth run through the points (quadratic curves through midpoints, the archive drawings' bowed lines);
    starts at the current clock, lasts length / SPEED, and advances the clock."""
    global clock
    L = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)) * 1.04
    if len(pts) == 2:
        d = f'M{pts[0][0]} {pts[0][1]}L{pts[1][0]} {pts[1][1]}'
    else:
        d = f'M{pts[0][0]} {pts[0][1]}'
        for i in range(1, len(pts) - 1):
            mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
            d += f'Q{pts[i][0]} {pts[i][1]} {mx:.0f} {my:.0f}'
        d += f'L{pts[-1][0]} {pts[-1][1]}'
    t = L / SPEED
    el('path', clock, cls, {'d': d}, t)
    clock += t
    return clock

def light(x, y, at):          # ceiling light: the X of the owner's symbol set
    el('path', at, 'e', {'d': f'M{x - 9} {y - 9}L{x + 9} {y + 9}M{x + 9} {y - 9}L{x - 9} {y + 9}'}, 0.25)
def switch(x, y, dx, dy, at):  # circle on the wall, stem into the room with the switch flag
    cx, cy = x + dx * 7, y + dy * 7
    el('path', at, 'e', {'d': f'M{cx} {cy}m-5 0a5 5 0 1 0 10 0a5 5 0 1 0-10 0M{cx + dx * 5} {cy + dy * 5}l{dx * 12} {dy * 12}l{dy * 5} {-dx * 5}'}, 0.3)
    return (cx + dx * 5, cy + dy * 5)
def socket(x, y, dx, dy, at):  # bowl on the wall, stem into the room
    cx, cy = x + dx * 8, y + dy * 8
    el('path', at, 'e', {'d': f'M{cx - dy * 8} {cy - dx * 8}a8 8 0 0 {1 if (dx + dy) > 0 else 0} {dy * 16} {dx * 16}M{cx} {cy}l{dx * 10} {dy * 10}'}, 0.3)
    return (cx + dx * 10, cy + dy * 10)
def label(x, y, text, at, cls='gr'):
    els.append(f'<text class="{cls}" style="--d:{at:.2f}s" x="{x}" y="{y}">{text}</text>')

# the board (tafla) in Forstofa
el('path', clock, 'e', {'d': 'M44 374H76V406H44ZM44 374L76 406M76 374L44 406'}, 0.4)
label(60, 420, 'T1', clock + 0.2)
clock += 0.5

# Gr.1 lights: board -> Forstofa light -> Stofa -> Eldhús -> Herbergi -> Baðherbergi, a drop to the switch at each light
label(84, 372, 'Gr.1', clock)
lights = [((215, 335), (150, 410, 0, -1), [(140, 345)]),           # Forstofa, switch by the front door
          ((140, 145), (100, 260, 0, -1), [(200, 300), (175, 215)]),           # Stofa, switch by its door
          ((325, 145), (370, 260, 0, -1), [(200, 120), (260, 100)]),           # Eldhús
          ((485, 115), (400, 150, 1, 0), [(380, 110), (420, 85)]),             # Herbergi
          ((485, 305), (400, 370, 1, 0), [(520, 180), (520, 250)])]            # Baðherbergi
prev = (76, 380)
for (lx, ly), (sx, sy, dx, dy), via in lights:
    run([prev] + via + [(lx, ly)])
    light(lx, ly, clock - 0.1)
    # the drop from the light to the switch, bowed into the room
    tip = (sx + dx * 7 + dx * 17, sy + dy * 7 + dy * 17)
    mid = ((lx + tip[0]) / 2 + dy * 18, (ly + tip[1]) / 2 + dx * 18)
    run([(lx, ly), (int(mid[0]), int(mid[1])), tip], 'run s')
    switch(sx, sy, dx, dy, clock - 0.15)
    prev = (lx, ly)

# Gr.2 sockets: a separate run from the board round the walls
clock += 0.2
label(84, 400, 'Gr.2', clock)
socks = [((60, 30, 0, 1), [(76, 396), (48, 300), (48, 60)]), ((200, 30, 0, 1), [(120, 48)]), ((250, 120, -1, 0), [(235, 60)]),
         ((570, 100, -1, 0), [(300, 80), (420, 60), (545, 60)]), ((520, 410, 0, -1), [(550, 240), (550, 390)]), ((320, 410, 0, -1), [(430, 392), (360, 392)])]
prev = (76, 396)
for (x, y, dx, dy), via in socks:
    tip = (x + dx * 18, y + dy * 18)
    run([prev] + via + [tip], 'run k')
    socket(x, y, dx, dy, clock - 0.15)
    prev = tip

END = clock + 0.3
svg = ('<svg class="intro" viewBox="0 0 600 440" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">\n  '
       + '\n  '.join(els) + '\n</svg>')

def patch_html(path):
    s = open(path, encoding='utf-8').read()
    s2 = re.sub(r'<svg class="intro".*?</svg>', lambda m: svg.replace('\n', '\n  '), s, count=1, flags=re.S)
    pass
    open(path, 'w', encoding='utf-8').write(s2)

os.chdir(r'E:\snjallheimilid')
patch_html('index.html')
if len(sys.argv) > 1: patch_html(sys.argv[1])

css = open('site.css', encoding='utf-8').read()
start = css.index('/* Intro:')
new = f'''/* Intro: a sample plan draws itself behind the hero: outer wall, inner walls and room names, openings, then the
   electrical layer as a wiring drawing: the run travels from the board (T1) circuit by circuit, Gr.1 lights with a
   drop to each switch, Gr.2 sockets round the walls, the symbols appearing as the line reaches them (generated by a
   script, the start --d and duration --t sit on every stroke, pathLength="1"); then it fades to a watermark and the
   text comes up. ~{END + 1.2:.0f} s, once. */
.hero {{ position: relative; overflow: hidden; min-height: 420px; display: grid; align-items: center; }}
.hero .wrap {{ position: relative; z-index: 1; width: 100%; }}
.intro {{ position: absolute; inset: 0; width: 100%; height: 100%; opacity: 1; animation: introFade 1.2s ease-out {END:.1f}s forwards; }}
.intro path, .intro text {{ fill: none; stroke: var(--text); stroke-linecap: round; stroke-linejoin: round; }}
.intro .w {{ stroke-width: 7; }} .intro .w.i {{ stroke-width: 4; }}
.intro .win {{ stroke-width: 1.5; }} .intro .door {{ stroke-width: 1.5; }}
.intro .cut {{ stroke: var(--bg); stroke-width: 9; stroke-linecap: butt; opacity: 0; animation: introShow 1ms linear var(--d) forwards; }}
.intro .e {{ stroke: var(--accent); stroke-width: 2; }}
.intro .run {{ stroke: var(--accent); stroke-width: 1.4; opacity: .9; }}
.intro .run.s {{ stroke-width: 1; }} .intro .run.k {{ stroke-width: 1.2; }}
.intro .rn {{ stroke: none; fill: var(--muted); font: 15px system-ui, "Segoe UI", sans-serif; text-anchor: middle; opacity: 0; animation: introShow .4s ease-out var(--d) forwards; }}
.intro .gr {{ stroke: none; fill: var(--accent); font: 600 11px system-ui, "Segoe UI", sans-serif; text-anchor: middle; opacity: 0; animation: introShow .3s ease-out var(--d) forwards; }}
.intro [pathLength] {{ stroke-dasharray: 1; stroke-dashoffset: 1; animation: introDraw var(--t, .9s) linear var(--d) forwards; }}
.hero .wrap > * {{ opacity: 0; animation: introText .8s ease-out {END + 0.2:.1f}s forwards; }}
@keyframes introDraw {{ to {{ stroke-dashoffset: 0; }} }}
@keyframes introShow {{ to {{ opacity: 1; }} }}
@keyframes introFade {{ to {{ opacity: .18; }} }}
@keyframes introText {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
@media (prefers-reduced-motion: reduce) {{
  .intro, .intro [pathLength], .intro .cut, .intro .rn, .intro .gr, .hero .wrap > * {{ animation: none; }}
  .intro {{ opacity: .18; }} .intro [pathLength] {{ stroke-dashoffset: 0; }} .intro .cut, .intro .rn, .intro .gr, .hero .wrap > * {{ opacity: 1; }}
}}
'''
open('site.css', 'w', encoding='utf-8').write(css[:start] + new)
# the artifact copy carries the CSS inline
if len(sys.argv) > 1:
    a = open(sys.argv[1], encoding='utf-8').read()
    a = re.sub(r'<style>.*?</style>', lambda m: '<style>\n' + open('site.css', encoding='utf-8').read() + '\n</style>', a, count=1, flags=re.S)
    open(sys.argv[1], 'w', encoding='utf-8').write(a)
print(f'{len(els)} elements, electrical ends at {END:.1f}s')
