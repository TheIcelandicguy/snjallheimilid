"""Turns the text of the logo sources into outlines, in Inter, so the logo looks the same on every machine.
Usage: python tools/logo/outline.py        (needs fonttools and brotli; PYTHONPATH=E:/motion-tools/pylib here)
Reads tools/logo/src/*.svg and fonts/inter.woff2, writes img/logo-*.svg. With --ttf DIR also writes Inter-400/600/800.ttf
there, for what cannot read a variable woff2 (the film's hud.py).
"""
import html
import pathlib
import re
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parents[2]
FONT = ROOT / "fonts" / "inter.woff2"
TEXT = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
SPAN = re.compile(r"<tspan\b([^>]*)>(.*?)</tspan>", re.S)
ATTR = re.compile(r'([\w-]+)="([^"]*)"')
# the wordmark on the horizontal logo keeps the width the source gave it, whatever the font's own width is
FIT = {"SNJALLHEIMILIÐ": 860.0}

_cache = {}


def inter(weight):
    if weight not in _cache:
        _cache[weight] = instancer.instantiateVariableFont(TTFont(FONT), {"wght": weight})
    return _cache[weight]


def advance(font, ch):
    return font["hmtx"][font.getBestCmap()[ord(ch)]][0]


def outline(tag):
    a = dict(ATTR.findall(tag.group(1)))
    body = tag.group(2)
    spans = [(dict(ATTR.findall(s[0])).get("fill", a.get("fill")), html.unescape(s[1])) for s in SPAN.findall(body)] or [(a.get("fill"), html.unescape(body))]
    spans = [(fill, " ".join(t.split())) for fill, t in spans]  # SVG collapses runs of spaces, and so does this
    weight = int(a.get("font-weight", 400))
    font = inter(weight)
    upm, size, spacing = font["head"].unitsPerEm, float(a["font-size"]), float(a.get("letter-spacing", 0))
    whole = "".join(t for _, t in spans)
    if whole in FIT:
        width = sum(advance(font, c) for c in whole) / upm
        size = (FIT[whole] - spacing * len(whole)) / width
    scale = size / upm
    total = sum(advance(font, c) * scale + spacing for c in whole)
    x = float(a["x"])
    if a.get("text-anchor") == "middle":
        x -= total / 2
    y = float(a["y"])
    if a.get("dominant-baseline") == "middle":
        y += font["OS/2"].sCapHeight * scale / 2
    glyphs, cmap, out = font.getGlyphSet(), font.getBestCmap(), []
    extra = f' transform="{a["transform"]}"' if "transform" in a else ""
    for fill, text in spans:
        pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        for ch in text:
            glyphs[cmap[ord(ch)]].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
            x += advance(font, ch) * scale + spacing
        out.append(f'<path fill="{fill}"{extra} d="{pen.getCommands()}"/>')
    return "".join(out)


def main():
    src = ROOT / "tools" / "logo" / "src"
    for name, dest in (("snjallheimilid-larett.svg", "logo-larett.svg"), ("snjallheimilid-hringlaga.svg", "logo-hringlaga.svg")):
        s = (src / name).read_text(encoding="utf-8")
        s, n = TEXT.subn(outline, s)
        assert "<text" not in s
        (ROOT / "img" / dest).write_text(s, encoding="utf-8")
        print(dest, n, "texts", len(s), "bytes")
    if "--ttf" in sys.argv:
        out = pathlib.Path(sys.argv[sys.argv.index("--ttf") + 1])
        out.mkdir(parents=True, exist_ok=True)
        for w in (400, 600, 800):
            f = inter(w)
            f.flavor = None
            f.save(out / f"Inter-{w}.ttf")
            print("wrote", out / f"Inter-{w}.ttf")


if __name__ == "__main__":
    main()
