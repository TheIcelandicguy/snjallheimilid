"""The fitting lines in 3D on a wall (owner 2026-11-24: "first drawn and interactive, then the 3D"; of the first test: "closer to the real product";
2026-11-25: "go for more details", then "now do the rest").

One picture:    blender -b --factory-startup --python lines3d.py -- --out FILE.png [--line valena] [--fit white] [--wall d8c7a8]
                [--boxes "sw2+socket;sw1;socket"] [--w 1400 --h 900 --samples 96] [--lens 70]
                [--hero 1 --hdri FILE.hdr --cam x,y,z --aim x,y,z --fstop 5.6]   a close-up with a room's light, wall grain and depth of field
Every part:     blender -b --factory-startup --python lines3d.py -- --batch DIR [--only LINE] [--fits white,black] [--hdri FILE.hdr]
                writes DIR/<line>-<fit>-<part>.png for every part of PARTS, each frame alone on a see-through wall that keeps only its shadow,
                so the page can lay it over a wall of any colour (tools/lines_view.py names the same files).

Everything is built by this script from boxes and cylinders: a wall, and on it frames of one or more positions with the parts in them. Each line is built
to its own measurements (LINES below): the size of its frame, how far it stands out from the wall, its opening, the size of the centre part and how far
that stands proud of the frame. Where the makers' sheets give a figure it is used, and the comment says which sheet; a figure marked "est." was scaled
off a drawing or a picture, or assumed. The models are look-alikes for an illustration: no maker's drawing or model is copied, no logo is shown, and the
page must say that they are drawings.

A box is its parts joined by +, boxes are separated by ; and a Mosaic frame counted in units is u: followed by its modules, a narrow one written n-
(u:n-sw+socket = three units). The kinds are the keys of Kit.part().
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
UNIT = 22.5 * MM  # a unit of a Mosaic frame counted in units; a module is one or two wide and 45 high

LINES = {
    # Legrand F02902EN/02 (plate 0 788 02L: 82 x 82 x 8.5, opening 45.5) and F02937EN/01 (rocker 45 x 45, 12.5 in front of the support: 4 proud);
    # the socket 0 772 11 is flush with the plate (F00754FR/09). The lower corners are rounder than the upper (the retailer's pictures); radii est.
    'mosaic': dict(size=82, t=8.5, r=3.5, r_low=10, open=45.5, centre=45, proud_sw=4, proud_so=0.3, soft=(1.4, 2), rough=0.16, coat=0.35),
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

# what the batch renders: line -> (its colours, its boxes). The same list as LINES and UNIT_FRAMES of tools/lines_view.py, which names the files
PARTS = {
    'mosaic': (['white'], ['sw1', 'sw2', 'socket', 'socket_usb', 'usb', 'net', 'net2', 'tv', 'blank', 'sw2+socket', 'socket+socket+socket',
                           'u:n-sw+socket', 'u:sw1+socket', 'u:socket+socket+n-sw+n-sw']),
    'valena': (['white'], ['sw1', 'sw2', 'sw3', 'socket', 'socket_usb', 'usb', 'net', 'net2', 'tv', 'blind', 'blank', 'sw3+socket', 'sw1+sw2+socket']),
    'merten': (['white'], ['sw1', 'sw2', 'socket', 'socket_usb', 'net', 'hdmi', 'blind', 'blank', 'sw2+socket', 'socket+socket+net']),
    'bseed_glass': (['white', 'black', 'grey', 'gold'], ['sw1', 'sw2', 'sw3', 'socket', 'socket_usb', 'socket_cover', 'socket_usb2', 'charger65', 'blind', 'bell', 'dimmer',
                                                         'touch1', 'touch2', 'touch3', 'touch4', 'tdim', 'ssocket', 'sblind', 'scurtain', 'touch2+socket', 'touch3+tdim+socket_usb']),
    'bseed_plastic': (['white', 'black', 'grey', 'gold'], ['sw1', 'sw2', 'neon1', 'neon2', 'socket', 'socket_usb', 'socket_cover', 'socket_usb2', 'charger65', 'net', 'net2', 'tv', 'sat',
                                                           'tel', 'hdmi', 'blind', 'fan', 'bell', 'dimmer', 'blank', 'touch1', 'touch2', 'touch3', 'touch4', 'tdim', 'ssocket', 'sblind',
                                                           'scurtain', 'heatw', 'heate', 'sw2+socket', 'touch2+sblind+socket+net']),
}


def arg(name, default):
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    return a[a.index('--' + name) + 1] if '--' + name in a else default


def box_file(box):
    """the name a box has in a file name: u3 / u4 / u6 for a frame counted in units, its parts joined by _ otherwise"""
    if box.startswith('u:'):
        return 'u' + str(sum(1 if m.startswith('n-') else 2 for m in box[2:].split('+')))
    return box.replace('+', '_')


def mat(name, color, rough=0.4, coat=0.0, metal=0.0, emit=None, sss=0.0, strength=7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.03
    if sss:  # the plastic's surface is never perfectly even: a faint variation in how glossy it is, and a little light under its skin
        nt = m.node_tree
        noise, ramp = nt.nodes.new('ShaderNodeTexNoise'), nt.nodes.new('ShaderNodeMapRange')
        noise.inputs['Scale'].default_value = 260
        noise.inputs['Detail'].default_value = 3
        ramp.inputs['To Min'].default_value = max(0.02, rough - 0.035)
        ramp.inputs['To Max'].default_value = rough + 0.05
        nt.links.new(noise.outputs['Fac'], ramp.inputs['Value'])
        nt.links.new(ramp.outputs['Result'], b.inputs['Roughness'])
        if 'Subsurface Weight' in b.inputs:
            b.inputs['Subsurface Weight'].default_value = sss
            b.inputs['Subsurface Radius'].default_value = (0.002, 0.002, 0.002)
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
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


def slab(w, d, h, radius=0.0, low=None):
    """a box w wide (X), d deep (Y, out of the wall towards the camera at -Y), h high (Z), its four edges that run into the wall rounded by `radius`;
    with `low` the two lower ones by that radius instead"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts)
    into = lambda e: abs(e.verts[0].co.x - e.verts[1].co.x) < 1e-9 and abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-9
    lim = min(w, h) / 2.2
    if radius and low is None:
        bmesh.ops.bevel(bm, geom=[e for e in bm.edges if into(e)], offset=min(radius, lim), segments=10, profile=0.5, affect='EDGES')
    elif low is not None:
        for sign, r in ((1, radius), (-1, low)):
            edges = [e for e in bm.edges if into(e) and e.verts[0].co.z * sign > 0 and abs(abs(e.verts[0].co.x) - w / 2) < 1e-9 and abs(abs(e.verts[0].co.z) - h / 2) < 1e-9]
            if r and edges:
                bmesh.ops.bevel(bm, geom=edges, offset=min(r, lim), segments=10, profile=0.5, affect='EDGES')
    return bm


def cyl(r, d, seg=64, caps=True):
    """a cylinder of radius r whose axis runs into the wall (Y), d deep"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, segments=seg, radius1=r, radius2=r, depth=d)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    return bm


def prism(points, d):
    """a flat shape given by its corners (x, z), d deep"""
    bm = bmesh.new()
    front = [bm.verts.new((x, -d / 2, z)) for x, z in points]
    back = [bm.verts.new((x, d / 2, z)) for x, z in points]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(points)
    for i in range(n):
        bm.faces.new([front[i], back[i], back[(i + 1) % n], front[(i + 1) % n]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def cut(o, cutter, first=True):
    m = o.modifiers.new('cut', 'BOOLEAN')
    m.operation, m.object = 'DIFFERENCE', cutter
    try:
        m.solver = 'EXACT'
    except Exception:
        pass
    cutter.hide_render = True
    cutter.hide_viewport = True
    if first:
        o.modifiers.move(len(o.modifiers) - 1, 0)  # cut first, bevel after


class Kit:
    def __init__(self, line, fit, wall, soft=0.0):
        L = LINES[line]
        self.L, self.wall = L, wall
        c = FITS[fit]
        key = tuple(min(1, x * 1.05 + 0.004) for x in c)
        soft = soft if not L.get('touch') else 0.0
        light = sum(c) / 3 > 0.2
        self.frame = mat('frame', c, L['rough'], L['coat'], sss=soft)
        self.key = mat('key', key, max(0.1, L['rough']), L['coat'] * 0.6, sss=soft)
        self.dark = mat('recess', tuple(x * 0.72 for x in key), 0.5)
        self.shadow = mat('shadow', (0.015, 0.015, 0.015), 0.8)
        self.hole = mat('hole', (0.008, 0.008, 0.008), 0.6)
        self.shut = mat('shutter', (0.035, 0.035, 0.04), 0.35)
        self.metal = mat('metal', (0.75, 0.74, 0.70), 0.25, metal=1.0)
        self.ink = mat('ink', (0.16, 0.16, 0.17) if light else (0.62, 0.62, 0.62), 0.5)  # what is printed on a part: arrows, a label
        self.led = mat('led', (0.1, 0.3, 0.6), 0.3, emit=(0.25, 0.65, 1))
        self.lit = mat('lit', (0.8, 0.85, 0.9), 0.3, emit=(0.75, 0.88, 1), strength=3)  # a symbol lit from behind on a touch key
        self.lamp = mat('lamp', (0.9, 0.3, 0.1), 0.3, emit=(1, 0.35, 0.08), strength=2.5)
        self.screen = mat('screen', (0.01, 0.012, 0.015), 0.05, coat=1.0)
        self.digits = mat('digits', (0.9, 0.95, 1), 0.3, emit=(0.85, 0.95, 1), strength=4)

    # ---- the frame. Every part is built around (x, z) on the wall, standing out from y = 0 towards -Y
    def plate(self, x, z, n, long_open=0.0):
        """a frame of n positions, or with `long_open` (a width) Mosaic's frame counted in units: one plate with one long opening"""
        L = self.L
        s, t = L['size'] * MM, L['t'] * MM
        w = (long_open + (L['size'] - L['open']) * MM) if long_open else s + PITCH * (n - 1)
        bev, segs = L['soft']
        self.plate_obj = obj('frame', slab(w, t, s, L['r'] * MM, L['r_low'] * MM if L.get('r_low') else None), self.frame, (x, -t / 2, z), bevel=bev * MM, segs=segs)
        xs = [x] if long_open else [x - PITCH * (n - 1) / 2 + PITCH * i for i in range(n)]
        self.backs = []
        for cx in xs:
            ow = long_open or L['open'] * MM
            cut(self.plate_obj, obj('opening', slab(ow, t * 3, L['open'] * MM, 1.0 * MM), self.dark, (cx, -t / 2, z), smooth=False))
            if L.get('lip'):  # a stepped inner edge: a shallow, wider step around the opening
                lw, ld = L['lip']
                cut(self.plate_obj, obj('lip', slab((L['open'] + 2 * lw) * MM, ld * 2 * MM, (L['open'] + 2 * lw) * MM, 1.5 * MM), self.dark, (cx, -t, z), smooth=False))
            self.backs.append((cx, ow, obj('back', slab(ow, 1 * MM, L['open'] * MM), self.shadow, (cx, -0.5 * MM, z), smooth=False)))  # what shows in the gap round a part
        return xs

    def back_at(self, x):
        return next(o for cx, w, o in self.backs if abs(x - cx) <= w / 2 + 1e-6)

    def width(self, kinds):
        return self.L['size'] * MM + PITCH * (len(kinds) - 1)

    # ---- the pieces parts are made of
    def centre(self, x, z, proud='proud_so', w=None):
        """the centre plate of a part; returns it and how far its face stands from the wall"""
        L = self.L
        c, d = L['centre'] * MM, (L['t'] + L.get(proud, L['proud_so'])) * MM
        return obj('centre', slab(w or c, d, c, 1.2 * MM), self.key, (x, -d / 2, z), bevel=0.5 * MM), d

    def on(self, name, bm, material, x, z, d, lift=0.05, **kw):
        """something lying on a part's face (d from the wall)"""
        return obj(name, bm, material, (x, -d - lift * MM, z), **kw)

    def label(self, text, x, z, d, size=4.2, material=None):
        cu = bpy.data.curves.new('label', 'FONT')
        cu.body, cu.size, cu.align_x, cu.align_y, cu.extrude = text, size * MM, 'CENTER', 'CENTER', 0.05 * MM
        o = bpy.data.objects.new('label', cu)
        bpy.context.scene.collection.objects.link(o)
        o.location, o.rotation_euler = (x, -d - 0.06 * MM, z), (math.radians(90), 0, 0)
        o.data.materials.append(material or self.ink)
        return o

    def arrow(self, x, z, d, way, size=3.6, material=None):
        """a printed triangle pointing up, down, left or right"""
        s = size * MM
        pts = {'up': [(-s, -s * 0.6), (s, -s * 0.6), (0, s * 0.8)], 'down': [(-s, s * 0.6), (0, -s * 0.8), (s, s * 0.6)],
               'left': [(s * 0.6, -s), (s * 0.6, s), (-s * 0.8, 0)], 'right': [(-s * 0.6, -s), (s * 0.8, 0), (-s * 0.6, s)]}[way]
        return self.on('arrow', prism(pts, 0.1 * MM), material or self.ink, x, z, d, smooth=False)

    def ring(self, x, z, d, r=3.6):
        o = self.on('ring', cyl(r * MM, 0.3 * MM, 48, caps=False), self.led, x, z, d, lift=0.02, smooth=False)
        o.modifiers.new('s', 'SOLIDIFY').thickness = 0.8 * MM

    def port(self, x, z, d, w, h, r=0.6):
        """a dark opening in a face: a USB port, a network jack"""
        return self.on('port', slab(w * MM, 0.2 * MM, h * MM, r * MM), self.hole, x, z, d, smooth=False)

    def jack(self, x, z, d, w=11.5):
        self.port(x, z + 0.8 * MM, d, w, w * 0.72, 0.8)
        self.port(x, z - w * 0.36 * MM - 0.6 * MM, d, w * 0.42, 2.2, 0.4)  # the notch of the plug's latch
        self.on('pins', slab(w * 0.62 * MM, 0.2 * MM, 1.1 * MM), self.metal, x, z + w * 0.22 * MM, d, lift=0.12, smooth=False)

    def coax(self, x, z, d, thread=False):
        h = (6 if thread else 3) * MM
        obj('coax', cyl(4.6 * MM, h, 48), self.metal, (x, -d - h / 2 + 0.2 * MM, z))
        obj('bore', cyl(3.3 * MM, 0.3 * MM, 32), self.hole, (x, -d - h + 0.1 * MM, z), smooth=False)
        obj('pin', cyl(0.8 * MM, 0.5 * MM, 16), self.metal, (x, -d - h, z), smooth=False)

    def knob(self, x, z, d, r):
        h = 11 * MM
        obj('knob', cyl(r * MM, h, 64), self.key, (x, -d - h / 2, z), bevel=1.2 * MM)
        obj('mark', slab(1.2 * MM, 0.3 * MM, r * 0.55 * MM), self.ink, (x + r * 0.33 * MM, -d - h - 0.02 * MM, z + r * 0.33 * MM), rot=(0, math.radians(-45), 0), smooth=False)

    def rockers(self, x, z, g=1, on=(), lamp=False, width=None):
        """g rockers side by side: each a plate that fills its share of the opening, tipped a few degrees, the first one pressed the other way.
        Returns the centre of each and how far its face stands from the wall"""
        L = self.L
        c, d = L['centre'] * MM, (L['t'] + L['proud_sw']) * MM
        full = width or c
        gap = 0.5 * MM
        w = (full - gap * (g - 1)) / g
        body = min(d - 1 * MM, 6 * MM)
        xs = []
        for i in range(g):
            cx = x - full / 2 + w / 2 + i * (w + gap)
            tilt = math.radians(-2.6 if i in on else 2.6)
            obj('rocker', slab(w, body, c, 1.0 * MM), self.key, (cx, -d + body / 2, z), rot=(tilt, 0, 0), bevel=0.5 * MM)
            if lamp:
                self.on('lamp', slab(2.2 * MM, 0.4 * MM, 5.5 * MM, 0.8 * MM), self.lamp, cx, z - c * 0.3, d, lift=0.9, smooth=False)
            xs.append(cx)
        return xs, d

    def socket(self, x, z, up=0.0, r=None):
        """a Schuko socket; `up` lifts the well in its plate and `r` narrows it, to leave room for a port under it"""
        L = self.L
        c = L['centre'] * MM
        body, d = self.centre(x, z)
        r = min(r or WELL_R, c / 2 - 2.2 * MM - abs(up))
        wz = z + up
        cutter = obj('cutter', cyl(r, WELL_D * 2), self.dark, (x, -d, wz), smooth=False)
        cut(body, cutter, first=False)  # after its bevel: bevelling the cut face leaves a crease across the plate
        for o in (self.wall, self.back_at(x)):  # the well is deeper than the part stands out: it goes into the wall, as it does into the wall box
            cut(o, cutter)
        obj('well', cyl(r - 0.15 * MM, WELL_D, 64, caps=False), self.key, (x, -d + WELL_D / 2, wz))
        obj('floor', cyl(r - 0.1 * MM, 1 * MM), self.key, (x, -d + WELL_D - 0.6 * MM, wz))
        top = -d + WELL_D - 1.1 * MM  # the face of the well's floor
        k = r / WELL_R
        obj('boss', slab(27 * MM * k, 1.2 * MM, 10.5 * MM * k, 5.2 * MM * k), self.key, (x, top - 0.6 * MM, wz), bevel=0.3 * MM)  # the raised pad the two pin holes sit in
        for sx in (-9.5, 9.5):
            obj('pin', cyl(2.6 * MM * k, 0.5 * MM, 32), self.hole, (x + sx * MM * k, top - 1.2 * MM - 0.02 * MM, wz), smooth=False)
            obj('shutter', cyl(1.9 * MM * k, 0.5 * MM, 32), self.shut, (x + sx * MM * k, top - 1.2 * MM - 0.06 * MM, wz), smooth=False)  # the child shutter behind each hole
        for sz in (-1, 1):  # the earth clips: sprung metal strips in notches at the top and the bottom of the well, standing in from its wall
            obj('earth', slab(4.4 * MM, WELL_D - 2.5 * MM, 2.6 * MM), self.metal, (x, -d + (WELL_D - 2.5 * MM) / 2 + 0.9 * MM, wz + sz * (r - 1.1 * MM)), bevel=0.35 * MM)
        return d

    def touch(self, x, z, g=1, big=False):
        """a smart key: one flat face with a lit ring for each gang"""
        _o, d = self.centre(x, z, 'proud_touch')
        spots = {1: [(0, 0)], 2: [(-11, 0), (11, 0)], 3: [(-14, 0), (0, 0), (14, 0)], 4: [(-10, 10), (10, 10), (-10, -10), (10, -10)]}[g]
        for a, b in spots:
            self.ring(x + a * MM, z + b * MM, d, 6.5 if big else 3.6)
        return d

    # ---- the parts
    def part(self, kind, x, z):
        L, c = self.L, self.L['centre'] * MM
        if kind in ('sw1', 'sw2', 'sw3'):
            g = int(kind[2])
            self.rockers(x, z, g, on=(0,) if g > 1 else ())
        elif kind in ('neon1', 'neon2'):
            self.rockers(x, z, int(kind[4]), on=(), lamp=True)
        elif kind == 'blind':  # two rockers, up and down
            xs, d = self.rockers(x, z, 2, on=())
            self.arrow(xs[0], z + c * 0.2, d + 0.0009, 'up', 3.2)  # lifted clear of the rocker, which is tipped
            self.arrow(xs[1], z - c * 0.2, d + 0.0009, 'down', 3.2)
        elif kind == 'bell':
            xs, d = self.rockers(x, z, 1)
            self.on('bell', cyl(4.4 * MM, 0.1 * MM, 32), self.ink, x, z + 2.2 * MM, d + 0.0008, smooth=False)
            self.on('bell', slab(11.5 * MM, 0.1 * MM, 1.7 * MM, 0.8 * MM), self.ink, x, z - 2.4 * MM, d + 0.0008, smooth=False)
            self.on('bell', cyl(1.3 * MM, 0.1 * MM, 16), self.ink, x, z - 5 * MM, d + 0.0008, smooth=False)
        elif kind in ('touch1', 'touch2', 'touch3', 'touch4') and L.get('touch'):
            self.touch(x, z, int(kind[5]))
        elif kind == 'tdim' and L.get('touch'):
            d = self.touch(x, z, 1, big=True)
            self.on('bar', prism([(-10 * MM, -15 * MM), (10 * MM, -15 * MM), (10 * MM, -11.5 * MM)], 0.1 * MM), self.lit, x, z, d, smooth=False)
        elif kind in ('sblind', 'scurtain') and L.get('touch'):
            _o, d = self.centre(x, z, 'proud_touch')
            if kind == 'sblind':
                self.arrow(x, z + 13 * MM, d, 'up', 3.2, self.lit)
                self.arrow(x, z - 13 * MM, d, 'down', 3.2, self.lit)
            else:
                self.arrow(x - 13 * MM, z, d, 'left', 3.2, self.lit)
                self.arrow(x + 13 * MM, z, d, 'right', 3.2, self.lit)
            self.ring(x, z, d, 3.2)
        elif kind in ('heatw', 'heate') and L.get('touch'):
            _o, d = self.centre(x, z, 'proud_touch')
            self.on('screen', slab(34 * MM, 0.4 * MM, 24 * MM, 2 * MM), self.screen, x, z + 6 * MM, d, lift=0.2, smooth=False)
            self.label('21°', x, z + 6 * MM, d + 0.0005, 9, self.digits)
            self.label('−', x - 11 * MM, z - 16 * MM, d, 6, self.lit)
            self.label('+', x + 11 * MM, z - 16 * MM, d, 6, self.lit)
            self.ring(x, z - 16 * MM, d, 2.4)
        elif kind == 'socket':
            self.socket(x, z)
        elif kind == 'ssocket':
            d = self.socket(x, z)
            self.on('led', cyl(1.2 * MM, 0.2 * MM, 16), self.led, x + c / 2 - 4.5 * MM, z + c / 2 - 4.5 * MM, d, smooth=False)
        elif kind in ('socket_usb', 'socket_usb2'):
            room = c / 2 - WELL_R  # what is left under a full well
            lift, r = (0, None) if room >= 7.5 * MM else (3.0 * MM, c / 2 - 8.8 * MM)
            d = self.socket(x, z, up=lift, r=r)
            pz = z - c / 2 + (3.9 * MM if room >= 7.5 * MM else 3.6 * MM)
            if kind == 'socket_usb':
                self.port(x, pz, d, 8.6, 3.2, 1.5)
            else:
                self.port(x - 8 * MM, pz, d, 7.4, 3.2, 0.5)
                self.port(x + 8 * MM, pz, d, 7.4, 3.2, 0.5)
        elif kind == 'socket_cover':  # the socket with its sprung lid shut
            _o, d = self.centre(x, z)
            r = min(WELL_R, c / 2 - 2.2 * MM) + 1.2 * MM
            obj('lid', cyl(r, 2.6 * MM, 64), self.key, (x, -d - 1.3 * MM, z), bevel=0.8 * MM)
            obj('hinge', slab(15 * MM, 3.2 * MM, 3 * MM, 1.2 * MM), self.key, (x, -d - 1.6 * MM, z + r - 0.6 * MM), bevel=0.4 * MM)
            obj('lip', slab(9 * MM, 3.4 * MM, 1.8 * MM, 0.8 * MM), self.key, (x, -d - 1.7 * MM, z - r + 0.2 * MM), bevel=0.3 * MM)
        elif kind == 'usb':
            _o, d = self.centre(x, z)
            self.port(x, z + 7 * MM, d, 12.4, 5.2, 0.6)
            self.on('tongue', slab(10.4 * MM, 0.2 * MM, 1.7 * MM), self.key, x, z + 7.9 * MM, d, lift=0.12, smooth=False)
            self.port(x, z - 6 * MM, d, 8.6, 3.2, 1.5)
        elif kind == 'charger65':
            _o, d = self.centre(x, z)
            self.port(x, z + 13 * MM, d, 12.4, 5.2, 0.6)
            self.on('tongue', slab(10.4 * MM, 0.2 * MM, 1.7 * MM), self.key, x, z + 13.9 * MM, d, lift=0.12, smooth=False)
            self.port(x, z + 3 * MM, d, 8.6, 3.2, 1.5)
            self.port(x, z - 5.5 * MM, d, 8.6, 3.2, 1.5)
            self.label('65W', x, z - 15 * MM, d, 4.4)
        elif kind == 'net':
            _o, d = self.centre(x, z)
            self.jack(x, z, d)
        elif kind == 'net2':
            _o, d = self.centre(x, z)
            self.jack(x - c * 0.22, z, d, 10)
            self.jack(x + c * 0.22, z, d, 10)
        elif kind in ('tv', 'sat'):
            _o, d = self.centre(x, z)
            self.coax(x, z + 3 * MM, d, thread=kind == 'sat')
            self.label('TV' if kind == 'tv' else 'SAT', x, z - 13 * MM, d, 4.4)
        elif kind == 'tel':
            _o, d = self.centre(x, z)
            self.jack(x, z + 3 * MM, d, 9)
            self.label('TEL', x, z - 13 * MM, d, 4.4)
        elif kind == 'hdmi':
            _o, d = self.centre(x, z)
            self.on('port', prism([(-7.5 * MM, 2.8 * MM), (7.5 * MM, 2.8 * MM), (7.5 * MM, -0.6 * MM), (5.4 * MM, -2.8 * MM), (-5.4 * MM, -2.8 * MM), (-7.5 * MM, -0.6 * MM)], 0.2 * MM), self.hole, x, z + 3 * MM, d, smooth=False)
            self.label('HDMI', x, z - 13 * MM, d, 4.0)
        elif kind == 'fan':
            _o, d = self.centre(x, z)
            self.knob(x, z - 2 * MM, d, 12.5)
            for a in (150, 110, 70, 30):
                self.on('dot', cyl(1.0 * MM, 0.1 * MM, 16), self.ink, x + math.cos(math.radians(a)) * 18.5 * MM, z - 2 * MM + math.sin(math.radians(a)) * 18.5 * MM, d, smooth=False)
        elif kind == 'dimmer':
            _o, d = self.centre(x, z)
            self.knob(x, z, d, 16)
        else:
            self.centre(x, z)  # a blank cover, also for a kind this line has no part for

    def box(self, kinds, x, z):
        for cx, k in zip(self.plate(x, z, len(kinds)), kinds):
            self.part(k, cx, z)

    def unit_box(self, mods, x, z):
        """Mosaic's frame counted in units: one long opening, its modules side by side; a module written n-sw is one unit wide"""
        units = [1 if m.startswith('n-') else 2 for m in mods]
        w = sum(units) * UNIT
        self.plate(x, z, 1, long_open=w + 0.5 * MM)
        cx = x - w / 2
        for m, u in zip(mods, units):
            mid = cx + u * UNIT / 2
            if u == 1:
                self.rockers(mid, z, 1, width=UNIT - 0.4 * MM)
            else:
                self.part(m, mid, z)
            cx += u * UNIT
        return w + (self.L['size'] - self.L['open']) * MM

    def any_box(self, box, x, z):
        if box.startswith('u:'):
            return self.unit_box(box[2:].split('+'), x, z)
        kinds = box.split('+')
        self.box(kinds, x, z)
        return self.width(kinds)

    def any_width(self, box):
        if box.startswith('u:'):
            return sum(1 if m.startswith('n-') else 2 for m in box[2:].split('+')) * UNIT + (self.L['size'] - self.L['open']) * MM
        return self.width(box.split('+'))


def finalize():
    """bake every object's modifiers and shade by angle, so that a flat face cut by a boolean is flat and a round one is round"""
    dg = bpy.context.evaluated_depsgraph_get()
    done = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render or not o.modifiers:
            continue
        done.append((o, bpy.data.meshes.new_from_object(o.evaluated_get(dg))))
    for o, me in done:
        o.modifiers.clear()
        o.data = me
        for p in me.polygons:
            p.use_smooth = True
        try:
            me.set_sharp_from_angle(angle=math.radians(32))
        except Exception:
            pass


def reset():
    for group in (bpy.data.objects, bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
        for item in list(group):
            group.remove(item)


def engine(samples):
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
    try:
        s.view_settings.view_transform = 'AgX'
        s.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass


def scene(wall_hex, w, h, hero=False, catcher=False):
    """the wall, the lamps and the room's light; returns the wall. With `catcher` the wall shows only the shadows that fall on it"""
    reset()
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = w, h
    s.render.film_transparent = catcher
    c = tuple(int(wall_hex[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(4, 0.1, 4), verts=bm.verts)
    wm = mat('wall', lin, 0.85)
    if hero:  # painted plaster with the fine grain a roller leaves
        nt = wm.node_tree
        b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        noise, bump = nt.nodes.new('ShaderNodeTexNoise'), nt.nodes.new('ShaderNodeBump')
        noise.inputs['Scale'].default_value = 900
        noise.inputs['Detail'].default_value = 6
        bump.inputs['Strength'].default_value = 0.22
        bump.inputs['Distance'].default_value = 0.0006
        nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    wall = obj('wall', bm, wm, (0, 0.05, 0), smooth=False)  # a thick wall, its face at y = 0, so that a socket's well can go into it
    wall.is_shadow_catcher = catcher
    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.9, 0.92, 1, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = 0.16
    hdri = arg('hdri', '')
    if hdri and os.path.exists(hdri):  # a real room's light in place of the plain sky
        nt = world.node_tree
        env, mp, tc = nt.nodes.new('ShaderNodeTexEnvironment'), nt.nodes.new('ShaderNodeMapping'), nt.nodes.new('ShaderNodeTexCoord')
        env.image = bpy.data.images.load(hdri, check_existing=True)
        mp.inputs['Rotation'].default_value = (0, 0, math.radians(float(arg('hdri_rot', 200))))
        nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
        nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
        nt.links.new(env.outputs['Color'], nt.nodes['Background'].inputs[0])
        nt.nodes['Background'].inputs[1].default_value = float(arg('hdri_strength', 0.5))
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
    return wall


def camera(loc, aim=(0, 0, 0), lens=70, ortho=0.0, fstop=0.0):
    s = bpy.context.scene
    cam = bpy.data.cameras.new('cam')
    if ortho:
        cam.type, cam.ortho_scale = 'ORTHO', ortho
    else:
        cam.lens = lens
    co = bpy.data.objects.new('cam', cam)
    s.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if fstop:  # a shallow depth of field, as a camera this close has
        cam.dof.use_dof = True
        cam.dof.focus_distance = (Vector(aim) - Vector(loc)).length
        cam.dof.aperture_fstop = fstop
    s.camera = co


def render(path):
    bpy.context.view_layer.update()
    finalize()
    bpy.context.scene.render.filepath = os.path.abspath(path)
    bpy.ops.render.render(write_still=True)


def batch(folder):
    """every part of every line and colour, each frame alone: a square picture for one position, wider for more, 4 px to the millimetre, on a wall that
    is see-through but for the shadow"""
    os.makedirs(folder, exist_ok=True)
    engine(int(arg('samples', 72)))
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'
    only, fits = arg('only', ''), arg('fits', '')
    px, margin, n = 4, 44 * MM, 0
    for line, (colours, boxes) in PARTS.items():
        if only and line != only:
            continue
        for fit in colours:
            if fits and fit not in fits.split(','):
                continue
            for box in boxes:
                out = os.path.join(folder, f'{line}-{fit}-{box_file(box)}.png')
                if os.path.exists(out) and not arg('again', ''):
                    continue
                probe = Kit.__new__(Kit)
                probe.L = LINES[line]
                wide, high = probe.any_width(box) + margin, LINES[line]['size'] * MM + margin
                wall = scene('808080', round(wide / MM * px), round(high / MM * px), catcher=True)
                Kit(line, fit, wall, soft=0.12).any_box(box, 0, 0)
                camera((0.2, -1.0, 0.1), ortho=max(wide, high))
                render(out)
                n += 1
                print('wrote', out, flush=True)
    print(n, 'pictures')


def main():
    if arg('batch', ''):
        return batch(arg('batch', ''))
    hero = bool(arg('hero', ''))
    engine(int(arg('samples', 96)))
    wall = scene(arg('wall', 'd8c7a8'), int(arg('w', 1400)), int(arg('h', 900)), hero=hero)
    kit = Kit(arg('line', 'valena'), arg('fit', 'white'), wall, soft=0.12 if hero else 0.0)
    boxes = arg('boxes', 'sw1;sw2+socket;socket').split(';')
    widths = [kit.any_width(b) for b in boxes]
    gap = 45 * MM
    x = -(sum(widths) + gap * (len(boxes) - 1)) / 2
    for b, wd in zip(boxes, widths):
        kit.any_box(b, x + wd / 2, 0)
        x += wd + gap
    camera(tuple(float(v) for v in arg('cam', '0.16,-0.95,0.07').split(',')), tuple(float(v) for v in arg('aim', '0,0,0').split(',')), float(arg('lens', 70)), fstop=float(arg('fstop', 0)))
    render(arg('out', 'lines3d.png'))
    print('wrote', arg('out', 'lines3d.png'))


main()
