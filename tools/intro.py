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
for i, (n, x, y) in enumerate([('Stofa', 170, 75), ('Eldhús', 130, 270), ('Svefnherbergi', 440, 70), ('Baðherbergi', 475, 290), ('Forstofa', 320, 300)]):
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
el('path', clock, 'e', {'d': 'M266 374H298V406H266ZM266 374L298 406M298 374L266 406'}, 0.4)
label(282, 424, 'T1', clock + 0.2)
clock += 0.5

# Gr.1 lights: board -> Forstofa -> Eldhús -> Stofa -> the light outside the bedroom door -> Svefnherbergi ->
# the light outside the bathroom door -> Baðherbergi, a drop to the switch at each light
label(282, 366, 'Gr.1', clock)
lights = [((320, 345), (355, 410, 0, -1), [(305, 365)]),                # Forstofa, switch by the front door
          ((150, 345), (261, 340, -1, 0), [(270, 330), (210, 360)]),    # Eldhús
          ((170, 125), (90, 220, 0, -1), [(110, 240), (120, 170)]),     # Stofa
          ((285, 205), (308, 150, -1, 0), [(235, 175)]),                # outside the bedroom door
          ((440, 130), (308, 170, 1, 0), [(340, 150)]),                 # Svefnherbergi
          ((352, 250), (350, 273, 0, 1), [(410, 210)]),                # outside the bathroom door
          ((475, 330), (377, 300, 1, 0), [(410, 270)])]                 # Baðherbergi
prev = (298, 380)
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
label(246, 394, 'Gr.2', clock)
socks = [((30, 340, 1, 0), [(270, 395), (120, 392), (56, 380)]), ((30, 120, 1, 0), [(50, 240)]), ((290, 30, 0, 1), [(100, 52), (220, 52)]),
         ((530, 30, 0, 1), [(330, 52), (470, 52)]), ((570, 150, -1, 0), [(545, 90)]), ((570, 340, -1, 0), [(548, 240)]), ((377, 370, -1, 0), [(420, 392), (392, 392), (372, 385), (368, 372)])]
prev = (298, 396)
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
