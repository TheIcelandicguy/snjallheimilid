"""Regenerate the hero intro SVG (run from the repo root: python tools/intro.py [copy.html]): the house as before, then the electrical layer drawn like a wiring drawing,
the run travelling from the board circuit by circuit, symbols appearing as the line reaches them."""
import math, os, re, sys

SPEED = 820.0          # plan px per second the run travels
els = []

def el(tag, d, cls, attrs, t=None):
    a = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
    st = f'--d:{d:.2f}s' + (f';--t:{t:.2f}s' if t else '')
    els.append(f'<{tag} class="{cls}" style="{st}" pathLength="1" {a}/>')

# ---- the house of the film (tools/film/house.py), 14 x 10 m ----
el('path', 0.0, 'w o', {'d': 'M30 30H570V410H30Z'}, 1.3)
for i, d in enumerate(['M308 30V235', 'M308 235H570', 'M30 220H115', 'M261 410V273', 'M261 273H377', 'M377 410V235']):
    el('path', 1.3 + i * 0.2, 'w i', {'d': d}, 0.6)
wins = [('M80 30H265', 'M80 26H265M80 34H265'), ('M385 30H489', 'M385 26H489M385 34H489')]
for i, (cut, lines) in enumerate(wins):
    t = 2.5 + i * 0.1
    els.append(f'<path class="cut" style="--d:{t:.2f}s" d="{cut}"/>')
    el('path', t, 'win', {'d': lines}, 0.5)
doors = [('M300 410H342', 'M342 410V368', 'M342 368A42 42 0 0 0 300 410'), ('M300 273H335', 'M300 273V238', 'M300 238A35 35 0 0 1 335 273'),
         ('M308 188V222', 'M308 222H342', 'M342 222A34 34 0 0 0 308 188'), ('M377 239V271', 'M377 271H409', 'M409 271A32 32 0 0 0 377 239')]
for i, (cut, leaf, swing) in enumerate(doors):
    t = 3.0 + i * 0.1
    els.append(f'<path class="cut" style="--d:{t:.2f}s" d="{cut}"/>')
    el('path', t, 'door', {'d': leaf}, 0.3)
    el('path', t + 0.1, 'door', {'d': swing}, 0.5)
for i, (n, x, y) in enumerate([('Stofa', 170, 60), ('Eldhús', 105, 300), ('Svefnherbergi', 440, 70), ('Baðherbergi', 480, 245), ('Forstofa', 318, 275)]):
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
def at_wall(x, y, dx, dy, off):
    """Local coordinates of a wall symbol: u from the wall into the room, v along the wall."""
    return lambda u, v: (round(x + dx * (off + u) - dy * v, 1), round(y + dy * (off + u) + dx * v, 1))
SW_R = 9
def switch_tip(x, y, dx, dy):  # the end of the stem, where the drop lands
    return at_wall(x, y, dx, dy, 5)(1.9 * SW_R, -SW_R)
def switch(x, y, dx, dy, at):  # as in electrical.js: a small circle on the wall, a slanted stem, a flag at its end
    P, r = at_wall(x, y, dx, dy, 5), SW_R
    c, a, b, f = P(0, 0), P(0.4 * r, -0.2 * r), P(1.9 * r, -r), P(2.15 * r, -0.45 * r)
    el('path', at, 'e', {'d': f'M{c[0]} {c[1]}m-{0.45 * r} 0a{0.45 * r} {0.45 * r} 0 1 0 {0.9 * r} 0a{0.45 * r} {0.45 * r} 0 1 0 {-0.9 * r} 0M{a[0]} {a[1]}L{b[0]} {b[1]}L{f[0]} {f[1]}'}, 0.3)
SO_R = 7
def socket_tip(x, y, dx, dy):  # the middle of the bowl's open side, where the run lands
    return at_wall(x, y, dx, dy, 5)(1.2 * SO_R, 0)
def socket(x, y, dx, dy, at):  # as in electrical.js: a bowl on a base line opening into the room, the stem into the wall
    P, r = at_wall(x, y, dx, dy, 5), SO_R
    w, o, b1, b2, a1, a2 = P(-5, 0), P(0, 0), P(0, -1.3 * r), P(0, 1.3 * r), P(1.2 * r, -r), P(1.2 * r, r)
    el('path', at, 'e', {'d': f'M{w[0]} {w[1]}L{o[0]} {o[1]}M{b1[0]} {b1[1]}L{b2[0]} {b2[1]}M{a1[0]} {a1[1]}A{r} {r} 0 0 0 {a2[0]} {a2[1]}'}, 0.3)
def label(x, y, text, at, cls='gr'):
    els.append(f'<text class="{cls}" style="--d:{at:.2f}s" x="{x}" y="{y}">{text}</text>')

# the board (tafla) in Forstofa
el('path', clock, 'e', {'d': 'M266 374H298V406H266ZM266 374L298 406M298 374L266 406'}, 0.4)
label(282, 424, 'T1', clock + 0.2)
clock += 0.5

# Gr.1 lights: board -> Forstofa -> Eldhús -> Stofa -> the light outside the bedroom door, which feeds Svefnherbergi and
# the light outside the bathroom door -> Baðherbergi; a drop to the switch at each light, bowed to the given side
label(232, 354, 'Gr.1', clock)
FORSTOFA, ELDHUS, STOFA, HOL_SVEFN, SVEFN, HOL_BAD, BAD = (320, 345), (150, 345), (170, 125), (285, 205), (440, 130), (352, 250), (490, 345)
lights = [(FORSTOFA, (355, 410, 0, -1), (298, 380), [(306, 366)], -14),   # switch by the front door
          (ELDHUS, (70, 220, 0, 1), FORSTOFA, [(240, 385)], 22),          # on the short wall, the kitchen side
          (STOFA, (95, 220, 0, -1), ELDHUS, [(168, 235)], 16),            # the same wall, the living-room side
          (HOL_SVEFN, (308, 150, -1, 0), STOFA, [(235, 150)], 0),
          (SVEFN, (308, 100, 1, 0), HOL_SVEFN, [(335, 178), (395, 150)], -14),
          (HOL_BAD, (362, 273, 0, 1), HOL_SVEFN, [(325, 245)], 0),        # in the forstofa, by its inner door
          (BAD, (377, 350, 1, 0), HOL_BAD, [(430, 300)], 18)]
for (lx, ly), (sx, sy, dx, dy), prev, via, bow in lights:
    run([prev] + via + [(lx, ly)])
    light(lx, ly, clock - 0.1)
    tip = tuple(int(v) for v in switch_tip(sx, sy, dx, dy))
    if bow:
        n = math.hypot(tip[0] - lx, tip[1] - ly)
        mid = ((lx + tip[0]) / 2 - (tip[1] - ly) / n * bow, (ly + tip[1]) / 2 + (tip[0] - lx) / n * bow)
        run([(lx, ly), (int(mid[0]), int(mid[1])), tip], 'run s')
    else:
        run([(lx, ly), tip], 'run s')
    switch(sx, sy, dx, dy, clock - 0.15)

# Gr.2 sockets: a separate run from the board round the walls
clock += 0.2
label(246, 394, 'Gr.2', clock)
socks = [((30, 340, 1, 0), [(120, 396), (54, 392)]), ((30, 120, 1, 0), [(52, 240)]), ((290, 30, 0, 1), [(70, 54), (200, 54)]),
         ((530, 30, 0, 1), [(330, 56), (470, 56)]), ((570, 150, -1, 0), [(548, 80)]), ((570, 340, -1, 0), [(546, 240)]), ((470, 410, 0, -1), [(540, 386), (490, 384)])]
prev = (266, 396)
for (x, y, dx, dy), via in socks:
    tip = tuple(int(v) for v in socket_tip(x, y, dx, dy))
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
start, stop = css.index('/* Intro:'), css.index('/* Dagur:')
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
.intro .rn {{ stroke: none; fill: var(--muted); font: 15px Inter, system-ui, sans-serif; text-anchor: middle; opacity: 0; animation: introShow .4s ease-out var(--d) forwards; }}
.intro .gr {{ stroke: none; fill: var(--accent); font: 600 11px Inter, system-ui, sans-serif; text-anchor: middle; opacity: 0; animation: introShow .3s ease-out var(--d) forwards; }}
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
open('site.css', 'w', encoding='utf-8').write(css[:start] + new + css[stop:])
# the artifact copy carries the CSS inline
if len(sys.argv) > 1:
    a = open(sys.argv[1], encoding='utf-8').read()
    a = re.sub(r'<style>.*?</style>', lambda m: '<style>\n' + open('site.css', encoding='utf-8').read() + '\n</style>', a, count=1, flags=re.S)
    open(sys.argv[1], 'w', encoding='utf-8').write(a)
print(f'{len(els)} elements, electrical ends at {END:.1f}s')
