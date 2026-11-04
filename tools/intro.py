"""Regenerate the hero's plan drawing (run from anywhere: python tools/intro.py): the film's house with its wiring, a still watermark behind the text.
Writes the SVG into index.html and its CSS into site.css, between the /* Intro: and /* Dagur: markers."""
import math, os, re

els = []

def path(cls, d):
    els.append(f'<path class="{cls}" d="{d}"/>')

def text(cls, x, y, s):
    els.append(f'<text class="{cls}" x="{x}" y="{y}">{s}</text>')

# ---- the house of the film (tools/film/house.py), 14 x 10 m ----
path('w o', 'M30 30H570V410H30Z')
for d in ['M308 30V235', 'M308 235H570', 'M30 220H115', 'M261 410V273', 'M261 273H377', 'M377 410V235']:
    path('w i', d)
for cut, lines in [('M80 30H265', 'M80 26H265M80 34H265'), ('M385 30H489', 'M385 26H489M385 34H489')]:
    path('cut', cut)
    path('win', lines)
for cut, leaf, swing in [('M300 410H342', 'M342 410V368', 'M342 368A42 42 0 0 0 300 410'), ('M300 273H335', 'M300 273V238', 'M300 238A35 35 0 0 1 335 273'),
                         ('M308 188V222', 'M308 222H342', 'M342 222A34 34 0 0 0 308 188'), ('M377 239V271', 'M377 271H409', 'M409 271A32 32 0 0 0 377 239')]:
    path('cut', cut)
    path('door', leaf)
    path('door', swing)
for n, x, y in [('Stofa', 170, 90), ('Eldhús', 105, 330), ('Svefnherbergi', 440, 100), ('Baðherbergi', 480, 275), ('Forstofa', 318, 305)]:
    text('rn', x, y, n)

# ---- the electrical layer ----
def run(pts, cls='run'):
    """A smooth run through the points (quadratic curves through midpoints, the archive drawings' bowed lines)."""
    d = f'M{pts[0][0]} {pts[0][1]}'
    for i in range(1, len(pts) - 1):
        mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
        d += f'Q{pts[i][0]} {pts[i][1]} {mx:.0f} {my:.0f}'
    path(cls, d + f'L{pts[-1][0]} {pts[-1][1]}')

def light(x, y):          # ceiling light: the X of the owner's symbol set
    path('e', f'M{x - 9} {y - 9}L{x + 9} {y + 9}M{x + 9} {y - 9}L{x - 9} {y + 9}')

def at_wall(x, y, dx, dy, off):
    """Local coordinates of a wall symbol: u from the wall into the room, v along the wall."""
    return lambda u, v: (round(x + dx * (off + u) - dy * v, 1), round(y + dy * (off + u) + dx * v, 1))

SW_R = 9
def switch_tip(x, y, dx, dy):  # the end of the stem, where the drop lands
    return at_wall(x, y, dx, dy, 5)(1.9 * SW_R, -SW_R)

def switch(x, y, dx, dy):  # as in electrical.js: a small circle on the wall, a slanted stem, a flag at its end
    P, r = at_wall(x, y, dx, dy, 5), SW_R
    c, a, b, f = P(0, 0), P(0.4 * r, -0.2 * r), P(1.9 * r, -r), P(2.15 * r, -0.45 * r)
    path('e', f'M{c[0]} {c[1]}m-{0.45 * r} 0a{0.45 * r} {0.45 * r} 0 1 0 {0.9 * r} 0a{0.45 * r} {0.45 * r} 0 1 0 {-0.9 * r} 0M{a[0]} {a[1]}L{b[0]} {b[1]}L{f[0]} {f[1]}')

SO_R = 7
def socket_tip(x, y, dx, dy):  # the middle of the bowl's open side, where the run lands
    return at_wall(x, y, dx, dy, 5)(1.2 * SO_R, 0)

def socket(x, y, dx, dy):  # as in electrical.js: a bowl on a base line opening into the room, the stem into the wall
    P, r = at_wall(x, y, dx, dy, 5), SO_R
    w, o, b1, b2, a1, a2 = P(-5, 0), P(0, 0), P(0, -1.3 * r), P(0, 1.3 * r), P(1.2 * r, -r), P(1.2 * r, r)
    path('e', f'M{w[0]} {w[1]}L{o[0]} {o[1]}M{b1[0]} {b1[1]}L{b2[0]} {b2[1]}M{a1[0]} {a1[1]}A{r} {r} 0 0 0 {a2[0]} {a2[1]}')

# the board (tafla) in Forstofa
path('e', 'M266 374H298V406H266ZM266 374L298 406M298 374L266 406')
text('gr', 282, 424, 'T1')

# Gr.1 lights: board -> Forstofa -> Eldhús -> Stofa -> the light outside the bedroom door, which feeds Svefnherbergi and
# the light outside the bathroom door -> Baðherbergi; a drop to the switch at each light, bowed to the given side
text('gr', 232, 354, 'Gr.1')
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
    light(lx, ly)
    tip = tuple(int(v) for v in switch_tip(sx, sy, dx, dy))
    if bow:
        n = math.hypot(tip[0] - lx, tip[1] - ly)
        mid = ((lx + tip[0]) / 2 - (tip[1] - ly) / n * bow, (ly + tip[1]) / 2 + (tip[0] - lx) / n * bow)
        run([(lx, ly), (int(mid[0]), int(mid[1])), tip], 'run s')
    else:
        run([(lx, ly), tip], 'run s')
    switch(sx, sy, dx, dy)

# Gr.2 sockets: a separate run from the board round the walls
text('gr', 246, 394, 'Gr.2')
socks = [((30, 340, 1, 0), [(120, 396), (54, 392)]), ((30, 120, 1, 0), [(52, 240)]), ((290, 30, 0, 1), [(70, 54), (200, 54)]),
         ((530, 30, 0, 1), [(330, 56), (470, 56)]), ((570, 150, -1, 0), [(548, 80)]), ((570, 340, -1, 0), [(546, 240)]), ((470, 410, 0, -1), [(540, 386), (490, 384)])]
prev = (266, 396)
for (x, y, dx, dy), via in socks:
    tip = tuple(int(v) for v in socket_tip(x, y, dx, dy))
    run([prev] + via + [tip], 'run k')
    socket(x, y, dx, dy)
    prev = tip

svg = ('<svg class="intro" viewBox="0 0 600 440" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">\n    '
       + '\n    '.join(els) + '\n  </svg>')

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
s = open('index.html', encoding='utf-8').read()
open('index.html', 'w', encoding='utf-8').write(re.sub(r'<svg class="intro".*?</svg>', lambda m: svg, s, count=1, flags=re.S))

css = open('site.css', encoding='utf-8').read()
start, stop = css.index('/* Intro:'), css.index('/* Dagur:')
new = '''/* Intro: the plan of the film's house with its wiring, a still watermark behind the hero's text (generated by tools/intro.py). */
.hero { position: relative; overflow: hidden; min-height: 420px; display: grid; align-items: center; }
.hero .wrap { position: relative; z-index: 1; width: 100%; }
.intro { position: absolute; inset: 0; width: 100%; height: 100%; opacity: .18; }
.intro path, .intro text { fill: none; stroke: var(--text); stroke-linecap: round; stroke-linejoin: round; }
.intro .w { stroke-width: 7; } .intro .w.i { stroke-width: 4; }
.intro .win { stroke-width: 1.5; } .intro .door { stroke-width: 1.5; }
.intro .cut { stroke: var(--bg); stroke-width: 9; stroke-linecap: butt; }
.intro .e { stroke: var(--accent); stroke-width: 2; }
.intro .run { stroke: var(--accent); stroke-width: 1.4; opacity: .9; }
.intro .run.s { stroke-width: 1; } .intro .run.k { stroke-width: 1.2; }
.intro .rn { stroke: none; fill: var(--muted); font: 15px Inter, system-ui, sans-serif; text-anchor: middle; }
.intro .gr { stroke: none; fill: var(--accent); font: 600 11px Inter, system-ui, sans-serif; text-anchor: middle; }
'''
open('site.css', 'w', encoding='utf-8').write(css[:start] + new + css[stop:])
print(f'{len(els)} elements')
