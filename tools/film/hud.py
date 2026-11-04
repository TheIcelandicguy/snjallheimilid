"""Draws the clock, caption, energy meter and end card over the rendered frames and writes the MP4.
Usage: python hud.py FRAMES_DIR OUT.mp4 [--crf 20] [--lang en]   (--lang reads timeline.<lang>.json: the same film in another language)
Frame numbers give the film time (30 per second), so a preview with every third frame works the same.
"""
import json
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent
LANG = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "is"
TL = json.loads((HERE / ("timeline.json" if LANG == "is" else f"timeline.{LANG}.json")).read_text(encoding="utf-8"))
L = TL["labels"]
FONTS = "E:/motion-tools/assets/fonts"  # from tools/logo/outline.py --ttf
SANS, BOLD, SERIF = f"{FONTS}/Inter-400.ttf", f"{FONTS}/Inter-600.ttf", f"{FONTS}/Inter-800.ttf"
INK, MUTED, ACCENT, CARD = (46, 30, 22), (120, 100, 88), (176, 112, 38), (248, 240, 232)


def lerp_table(table, x):
    if x <= table[0][0]:
        return table[0][1]
    for (a, va), (b, vb) in zip(table, table[1:]):
        if x <= b:
            return va + (vb - va) * (x - a) / (b - a)
    return table[-1][1]


def clock_at(t):
    return lerp_table(TL["clock"], t)


def kwh_rate(hour):
    return lerp_table(TL["kwh_per_hour"], hour)


def kwh_total(hour):
    n, total, h, step = 0, 0.0, 0.0, 0.02
    while h < hour:
        total += kwh_rate(h) * step
        h += step
    return total


def fmt(v, d=2):
    return f"{v:.{d}f}".replace(".", L["decimal"])


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def scene_at(t):
    cur = TL["scenes"][0]
    for s in TL["scenes"]:
        if t >= s["t"]:
            cur = s
    return cur


def line_at(scene, t):
    """The line of the story showing at film time t, and when it began."""
    cur = scene["lines"][0]
    for line in scene["lines"]:
        if t >= line[0]:
            cur = line
    return cur


class Hud:
    def __init__(self, w, h):
        self.w, self.h, self.u = w, h, w / 1280
        u = self.u
        self.f = lambda path, size: ImageFont.truetype(path, max(8, round(size * u)))
        self.fonts = dict(clock=self.f(BOLD, 62), title=self.f(BOLD, 31), body=self.f(SANS, 25), small=self.f(SANS, 19), num=self.f(BOLD, 34), end=self.f(SERIF, 62), endb=self.f(SANS, 25), btn=self.f(BOLD, 25), alert=self.f(BOLD, 26))
        self.graph = [(h / 24.0, kwh_rate(h)) for h in [i * 0.1 for i in range(241)]]

    def panel(self, d, box, alpha=232, r=16):
        d.rounded_rectangle([round(v * self.u) for v in box], radius=round(r * self.u), fill=(*CARD, alpha))

    def draw(self, t):
        w, h, u = self.w, self.h, self.u
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im, "RGBA")
        f = self.fonts
        H = h / u
        hour = clock_at(t)
        hh, mm = int(hour), int((hour - int(hour)) * 60)
        endf = smooth((t - TL["end_card"]) / 0.9)
        hudf = 1 - endf

        def xy(x, y):
            return (round(x * u), round(y * u))

        def alpha(a):
            return int(a * hudf)

        if hudf > 0:
            # the clock
            d.text(xy(30, 18), f"{hh:02d}:{mm:02d}", font=f["clock"], fill=(255, 255, 255, alpha(255)), stroke_width=max(1, round(2 * u)), stroke_fill=(30, 18, 10, alpha(150)))
            # the caption, fading across each scene change
            s = scene_at(t)
            fade = smooth((t - s["t"]) / 0.6)
            line_t, line = line_at(s, t)
            line_fade = smooth((t - line_t) / 0.45)
            self.panel(d, (24, H - 112, 1256, H - 18), alpha(232))
            ca = alpha(255 * fade)
            d.text(xy(46, H - 108), s["title"], font=f["title"], fill=(*INK, ca))
            d.text(xy(46, H - 66), line, font=f["body"], fill=(*MUTED, alpha(255 * line_fade)))
            # dots for the scenes
            n = len(TL["scenes"])
            idx = TL["scenes"].index(s)
            for i in range(n):
                cx, cy = 1236 - (n - 1 - i) * 24, H - 88
                r = 7 if i == idx else 5
                d.ellipse([round((cx - r) * u), round((cy - r) * u), round((cx + r) * u), round((cy + r) * u)], fill=(*(ACCENT if i == idx else (205, 192, 180)), alpha(255)))
            # the energy meter
            x0, y0, x1, y1 = 900, 18, 1256, 214
            self.panel(d, (x0, y0, x1, y1), alpha(232))
            d.text(xy(x0 + 16, y0 + 8), L["energy"], font=f["small"], fill=(*MUTED, alpha(255)))
            d.text(xy(x0 + 16, y0 + 32), f"{fmt(kwh_rate(hour))} {L['per_hour']}", font=f["num"], fill=(*INK, alpha(255)))
            d.text(xy(x0 + 16, y0 + 76), L["today"].replace("{kwh}", fmt(kwh_total(hour), 1)), font=f["small"], fill=(*MUTED, alpha(255)))
            gx0, gy0, gx1, gy1 = x0 + 16, y0 + 108, x1 - 16, y1 - 36
            top = 1.7
            pts = [(gx0 + (gx1 - gx0) * a, gy1 - (gy1 - gy0) * min(b, top) / top) for a, b in self.graph]
            d.line([xy(*p) for p in pts], fill=(205, 192, 180, alpha(255)), width=max(1, round(1.5 * u)))
            done = [p for (p, (a, b)) in zip(pts, self.graph) if a * 24 <= hour]
            if len(done) > 1:
                poly = [xy(done[0][0], gy1)] + [xy(*p) for p in done] + [xy(done[-1][0], gy1)]
                d.polygon(poly, fill=(*ACCENT, alpha(70)))
                d.line([xy(*p) for p in done], fill=(*ACCENT, alpha(255)), width=max(2, round(2.5 * u)))
                ex, ey = xy(*done[-1])
                rr = round(4 * u)
                d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=(*ACCENT, alpha(255)))
            d.text(xy(x0 + 16, y1 - 30), TL["energy_note"], font=f["small"], fill=(*MUTED, alpha(210)))
            # inside and outside in the cold scene
            ta = smooth((t - 26.5) / 0.8) * (1 - smooth((t - 37) / 0.8))
            if ta > 0:
                a = int(255 * ta * hudf)
                self.panel(d, (900, 224, 1256, 304), int(232 * ta * hudf))
                out = lerp_table(TL["temps"]["outside"], t)
                sign = "\u2212" if out < 0 else ""
                d.text(xy(916, 230), L["outside"], font=f["small"], fill=(*MUTED, a))
                d.text(xy(916, 250), f"{sign}{abs(out):.0f} °C", font=f["num"], fill=(58, 96, 150, a))
                d.text(xy(1080, 230), L["inside"], font=f["small"], fill=(*MUTED, a))
                d.text(xy(1080, 250), f"{fmt(TL['temps']['inside'], 1)} °C", font=f["num"], fill=(*ACCENT, a))
            # the water alert
            a0, a1 = TL["water_alert"]
            wa = smooth((t - a0) / 0.4) * (1 - smooth((t - a1 + 0.5) / 0.5))
            if wa > 0:
                a = int(255 * wa * hudf)
                self.panel(d, (24, 104, 470, 186), int(240 * wa * hudf))
                d.text(xy(42, 110), L["brand"], font=f["small"], fill=(*MUTED, a))
                d.text(xy(42, 136), L["water"], font=f["alert"], fill=(40, 90, 170, a))
        if endf > 0:
            ov = Image.new("RGBA", (w, h), (24, 16, 12, int(125 * endf)))
            im = Image.alpha_composite(im, ov)
            d = ImageDraw.Draw(im, "RGBA")
            a = int(255 * endf)
            cx = w // 2

            def centre(y, s, font, fill):
                d.text((cx, round(y * u)), s, font=font, fill=fill, anchor="mm")

            centre(H * 0.36, "Snjallheimilið", f["end"], (255, 255, 255, a))
            centre(H * 0.36 + 62, L["end_sub"], f["endb"], (240, 228, 216, a))
            bw, bh, by = 380, 64, H * 0.36 + 130
            d.rounded_rectangle([round((640 - bw / 2) * u), round((by - bh / 2) * u), round((640 + bw / 2) * u), round((by + bh / 2) * u)], radius=round(bh / 2 * u), fill=(*ACCENT, a))
            centre(by, L["end_btn"], f["btn"], (255, 255, 255, a))
        return im


def main():
    frames_dir = pathlib.Path(sys.argv[1])
    out = sys.argv[2]
    frames = sorted(frames_dir.glob("f_*.jpg"))
    nums = [int(p.stem[2:]) for p in frames]
    step = min((b - a for a, b in zip(nums, nums[1:])), default=1)
    fps = 30 / step
    crf = sys.argv[sys.argv.index("--crf") + 1] if "--crf" in sys.argv else "20"
    w, h = Image.open(frames[0]).size
    hud = Hud(w, h)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", f"{fps}", "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", crf, "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for p, n in zip(frames, nums):
        base = Image.open(p).convert("RGBA")
        over = hud.draw((n - 1) / 30)
        ff.stdin.write(Image.alpha_composite(base, over).convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    print("done", out, len(frames), "frames at", fps, "fps")


if __name__ == "__main__":
    main()
