"""The fitting lines in 3D on a wall (owner 2026-11-24: "first drawn and interactive, then the 3D", and of the first test: "closer to the real product").
Run windowless:  blender -b --factory-startup --python lines3d.py -- --out FILE.png [--line valena] [--fit white] [--wall d8c7a8]
                 [--boxes "sw2+socket;sw1;socket"] [--w 1400 --h 900 --samples 96] [--lens 70]

Everything is built by this script from boxes and cylinders: a wall, and on it frames of one or more positions with the parts in them. Each line is built
to its own measurements (LINES below): the size of its frame, how far it stands out from the wall, its opening, the size of the centre part and how far
that stands proud of the frame. Where the makers' sheets give a figure it is used, and the comment says which sheet; a figure marked "est." was scaled
off a drawing or a picture, or assumed. The models are look-alikes for an illustration: no maker's drawing or model is copied, no logo is shown, and the
page must say that they are drawings.

A box is its parts joined by +, boxes are separated by ; (sw1, sw2, sw3 = a rocker switch of that many gangs; touch1..touch4 = a smart touch key;
socket; blank).
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

MM = 0.001
PITCH = 71 * MM  # centre to centre, every line (153 - 82 on Legrand's sheet, 157 - 86 on Valena's and BSEED's, 151.7 - 80.5 on Merten's)
WELL_R, WELL_D = 19.5 * MM, 17.5 * MM  # the round well of a Schuko socket (CEE 7/3: about 39 mm across, 17.5 mm deep; no maker's sheet states it)

LINES = {
    # Legrand F02902EN/02 (plate 0 788 02L: 82 x 82 x 8.5, opening 45.5) and F02937EN/01 (rocker 45 x 45, 12.5 in front of the support: 4 proud);
    # the socket 0 772 11 is flush with the plate (F00754FR/09). Wide chamfer on the outer edge (Legrand: "larges chanfreins"); corner radius est.
    'mosaic': dict(size=82, t=8.5, r=5, open=45.5, centre=45, proud_sw=4, proud_so=0.3, soft=(3.0, 1), rough=0.16, coat=0.35, halves=True),
    # Legrand F01994EN/00 (plate 7540 01: 86 x 86 x 9.8), F02081EN/01 (switch 14 in front of the support: 4.2 proud), F01949EN/01 (socket 11: 1.2 proud).
    # Opening and visible rocker about 55 (est. from the plate drawing); the plate is slightly domed; corner radius est. from the catalogue picture
    'valena': dict(size=86, t=9.8, r=6.5, open=55.5, centre=55, proud_sw=4.2, proud_so=1.2, soft=(2.6, 6), rough=0.14, coat=0.4),
    # Merten M-Smart glossy: 80.5 x 80.5 x 10.1 (retailer's figures; Schneider's sheet gives none), rocker 55 x 55 visible (Schneider's sheet of 432119).
    # The stepped inner edge, the corner radius and how far the rocker stands proud are est. from the catalogue picture
    'merten': dict(size=80.5, t=10.1, r=2, open=55.5, centre=55, proud_sw=1.5, proud_so=1.0, soft=(0.8, 3), lip=(4.5, 1.6), rough=0.06, coat=0.8),
    # BSEED Melody (bseed.com, figures read off its product pictures): glass panel 86 x 86, opening 47 x 47, insert body 50; in front of the mounting
    # flange a touch key stands 5, a rocker 15 and a socket 10, so with glass taken as 5 thick (est.) the touch key is flush, the rocker 10 proud
    'bseed_glass': dict(size=86, t=5, r=1.5, open=47.5, centre=47, proud_sw=10, proud_so=5, proud_touch=0.2, soft=(0.7, 3), rough=0.03, coat=1.0, touch=True),
    # BSEED Echo plastic panel: 86 wide, opening 52 (from the drawing of the Echo glass panel; the plastic one has none). Thickness and how far the
    # parts stand proud are est.
    'bseed_plastic': dict(size=86, t=8, r=2, open=52.5, centre=52, proud_sw=4, proud_so=2, proud_touch=1, soft=(1.0, 3), rough=0.28, coat=0.15, touch=True),
}
FITS = {'white': (0.90, 0.90, 0.88), 'black': (0.012, 0.012, 0.014), 'grey': (0.28, 0.29, 0.31), 'gold': (0.62, 0.47, 0.20)}


def arg(name, default):
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    return a[a.index('--' + name) + 1] if '--' + name in a else default


def mat(name, color, rough=0.4, coat=0.0, metal=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.03
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = 7
    return m


def obj(name, bm, material, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, segs=3, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location, o.rotation_euler = loc, rot
    o.data.materials.append(material)
    if bevel:
        b = o.modifiers.new('bevel', 'BEVEL')
        b.width, b.segments, b.limit_method, b.angle_limit = bevel, segs, 'ANGLE', math.radians(40)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
        o.modifiers.new('wn', 'WEIGHTED_NORMAL')
    return o


def slab(w, d, h, radius=0.0):
    """a box w wide (X), d deep (Y, out of the wall towards the camera at -Y), h high (Z), its four edges that run into the wall rounded by `radius`"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts)
    if radius:
        edges = [e for e in bm.edges if abs(e.verts[0].co.x - e.verts[1].co.x) < 1e-9 and abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-9]
        bmesh.ops.bevel(bm, geom=edges, offset=min(radius, w / 2.2, h / 2.2), segments=10, profile=0.5, affect='EDGES')
    return bm


def cyl(r, d, seg=64, caps=True):
    """a cylinder of radius r whose axis runs into the wall (Y), d deep"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, segments=seg, radius1=r, radius2=r, depth=d)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    return bm


def cut(o, cutter):
    m = o.modifiers.new('cut', 'BOOLEAN')
    m.operation, m.object = 'DIFFERENCE', cutter
    try:
        m.solver = 'EXACT'
    except Exception:
        pass
    cutter.hide_render = True
    cutter.hide_viewport = True
    o.modifiers.move(len(o.modifiers) - 1, 0)  # cut first, bevel after


class Kit:
    def __init__(self, line, fit, wall):
        L = LINES[line]
        self.L, self.wall = L, wall
        c = FITS[fit]
        key = tuple(min(1, x * 1.05 + 0.004) for x in c)
        self.frame = mat('frame', c, L['rough'], L['coat'])
        self.key = mat('key', key, max(0.1, L['rough']), L['coat'] * 0.6)
        self.dark = mat('recess', tuple(x * 0.72 for x in key), 0.5)
        self.shadow = mat('shadow', (0.015, 0.015, 0.015), 0.8)
        self.hole = mat('hole', (0.008, 0.008, 0.008), 0.6)
        self.metal = mat('metal', (0.75, 0.74, 0.70), 0.25, metal=1.0)
        self.led = mat('led', (0.1, 0.3, 0.6), 0.3, emit=(0.25, 0.65, 1))

    # every part is built around (x, z) on the wall, standing out from y = 0 towards -Y
    def plate(self, x, z, n):
        L = self.L
        s, t = L['size'] * MM, L['t'] * MM
        w = s + PITCH * (n - 1)
        bev, segs = L['soft']
        self.plate_obj = obj('frame', slab(w, t, s, L['r'] * MM), self.frame, (x, -t / 2, z), bevel=bev * MM, segs=segs)
        xs = [x - PITCH * (n - 1) / 2 + PITCH * i for i in range(n)]
        self.backs = {}
        for cx in xs:
            cut(self.plate_obj, obj('opening', slab(L['open'] * MM, t * 3, L['open'] * MM, 1.0 * MM), self.dark, (cx, -t / 2, z), smooth=False))
            if L.get('lip'):  # a stepped inner edge: a shallow, wider step around the opening
                lw, ld = L['lip']
                cut(self.plate_obj, obj('lip', slab((L['open'] + 2 * lw) * MM, ld * 2 * MM, (L['open'] + 2 * lw) * MM, 1.5 * MM), self.dark, (cx, -t, z), smooth=False))
            self.backs[round(cx, 5)] = obj('back', slab(L['open'] * MM, 1 * MM, L['open'] * MM), self.shadow, (cx, -0.5 * MM, z), smooth=False)  # what shows in the gap round the centre part
        return xs

    def rockers(self, x, z, g=1, on=()):
        """g rockers side by side: each a plate that fills its share of the opening, tipped a few degrees, the first one pressed the other way"""
        L = self.L
        c, d = L['centre'] * MM, (L['t'] + L['proud_sw']) * MM
        gap = 0.5 * MM
        w = (c - gap * (g - 1)) / g
        body = min(d - 1 * MM, 6 * MM)
        for i in range(g):
            cx = x - c / 2 + w / 2 + i * (w + gap)
            tilt = math.radians(-2.6 if i in on else 2.6)
            obj('rocker', slab(w, body, c, 1.0 * MM), self.key, (cx, -d + body / 2, z), rot=(tilt, 0, 0), bevel=0.5 * MM)

    def touch(self, x, z, g=1):
        """a smart key: one flat face with a lit ring for each gang"""
        L = self.L
        c, d = L['centre'] * MM, (L['t'] + L.get('proud_touch', 0.5)) * MM
        obj('touch', slab(c, d, c, 1.2 * MM), self.key, (x, -d / 2, z), bevel=0.3 * MM)
        spots = {1: [(0, 0)], 2: [(-11, 0), (11, 0)], 3: [(-14, 0), (0, 0), (14, 0)], 4: [(-10, 10), (10, 10), (-10, -10), (10, -10)]}[g]
        for a, b in spots:
            ring = obj('ring', cyl(3.6 * MM, 0.3 * MM, 48, caps=False), self.led, (x + a * MM, -d - 0.02 * MM, z + b * MM), smooth=False)
            s = ring.modifiers.new('s', 'SOLIDIFY')
            s.thickness = 0.8 * MM

    def socket(self, x, z):
        L = self.L
        c, d = L['centre'] * MM, (L['t'] + L['proud_so']) * MM
        body = obj('socket', slab(c, d, c, 1.2 * MM), self.key, (x, -d / 2, z), bevel=0.5 * MM)
        r = min(WELL_R, c / 2 - 2.2 * MM)
        cutter = obj('cutter', cyl(r, WELL_D * 2), self.dark, (x, -d, z), smooth=False)
        for o in (body, self.wall, self.backs[round(x, 5)]):  # the well is deeper than the part stands out: it goes into the wall, as it does into the wall box
            cut(o, cutter)
        obj('well', cyl(r - 0.15 * MM, WELL_D, 64, caps=False), self.key, (x, -d + WELL_D / 2, z))
        obj('floor', cyl(r - 0.1 * MM, 1 * MM), self.key, (x, -d + WELL_D - 0.6 * MM, z))
        for sx in (-9.5, 9.5):
            obj('pin', cyl(2.4 * MM, 2 * MM, 24), self.hole, (x + sx * MM, -d + WELL_D - 1.6 * MM, z))
        for sz in (-1, 1):  # the earth clips, standing in notches at the top and the bottom of the well
            obj('earth', slab(4.2 * MM, WELL_D - 4 * MM, 1.4 * MM), self.metal, (x, -d + WELL_D / 2 + 1.5 * MM, z + sz * (r - 0.9 * MM)), bevel=0.2 * MM)

    def blank(self, x, z):
        L = self.L
        c, d = L['centre'] * MM, (L['t'] + L['proud_so']) * MM
        obj('blank', slab(c, d, c, 1.2 * MM), self.key, (x, -d / 2, z), bevel=0.5 * MM)

    def part(self, kind, x, z):
        if kind.startswith('sw'):
            g = int(kind[2:] or 1)
            self.rockers(x, z, g, on=(0,) if g > 1 else ())
        elif kind.startswith('touch') and self.L.get('touch'):
            self.touch(x, z, int(kind[5:] or 1))
        elif kind == 'socket':
            self.socket(x, z)
        else:
            self.blank(x, z)  # a blank cover, also for a kind that is not modelled yet

    def box(self, kinds, x, z):
        for cx, k in zip(self.plate(x, z, len(kinds)), kinds):
            self.part(k, cx, z)

    def width(self, kinds):
        return self.L['size'] * MM + PITCH * (len(kinds) - 1)


def scene(wall_hex, w, h, samples):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for kind in ('OPTIX', 'CUDA'):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                for d in prefs.devices:
                    d.use = True
                s.cycles.device = 'GPU'
                break
            except Exception:
                continue
    except Exception:
        pass
    s.cycles.samples = samples
    s.cycles.use_denoising = True
    s.render.resolution_x, s.render.resolution_y = w, h
    try:
        s.view_settings.view_transform = 'AgX'
        s.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    c = tuple(int(wall_hex[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(4, 0.1, 4), verts=bm.verts)
    wall = obj('wall', bm, mat('wall', lin, 0.85), (0, 0.05, 0), smooth=False)  # a thick wall, its face at y = 0, so that a socket's well can go into it
    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.9, 0.92, 1, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = 0.16
    s.world = world

    def light(name, loc, energy, size, color=(1, 0.96, 0.9)):
        d = bpy.data.lights.new(name, 'AREA')
        d.energy, d.size, d.color = energy, size, color
        o = bpy.data.objects.new(name, d)
        s.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    light('key', (-0.75, -0.55, 0.85), 26, 0.35)
    light('fill', (0.8, -1.0, -0.9), 5, 1.2, (0.9, 0.95, 1))
    light('front', (0.16, -1.0, 0.95), 12, 0.5)  # from above the camera, into the well of a socket; high, like the others, so that no glossy frame mirrors a lamp into the camera
    cam = bpy.data.cameras.new('cam')
    cam.lens = float(arg('lens', 70))
    co = bpy.data.objects.new('cam', cam)
    s.collection.objects.link(co)
    co.location = (0.16, -0.95, 0.07)
    co.rotation_euler = (Vector((0, 0, 0)) - Vector(co.location)).to_track_quat('-Z', 'Y').to_euler()
    s.camera = co
    return wall


def main():
    line, fit = arg('line', 'valena'), arg('fit', 'white')
    wall = scene(arg('wall', 'd8c7a8'), int(arg('w', 1400)), int(arg('h', 900)), int(arg('samples', 96)))
    kit = Kit(line, fit, wall)
    boxes = [b.split('+') for b in arg('boxes', 'sw1;sw2+socket;socket').split(';')]
    widths = [kit.width(b) for b in boxes]
    gap = 45 * MM
    x = -(sum(widths) + gap * (len(boxes) - 1)) / 2
    for b, wd in zip(boxes, widths):
        kit.box(b, x + wd / 2, 0)
        x += wd + gap
    out = arg('out', 'lines3d.png')
    bpy.context.scene.render.filepath = os.path.abspath(out)
    bpy.ops.render.render(write_still=True)
    print('wrote', out)


main()
