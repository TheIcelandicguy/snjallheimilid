"""The fitting lines in 3D on a wall (owner 2026-11-24: "first drawn and interactive, then the 3D").
Run windowless:  blender -b --factory-startup --python lines3d.py -- --out FILE.png [--line valena] [--fit white] [--wall d8c7a8]
                 [--boxes "sw2+socket;sw1;socket"] [--w 1400 --h 900 --samples 96]

Everything is built by this script from boxes and cylinders: a wall, and on it frames of one or more positions with a rocker switch, a socket and the
other parts in them. The shapes are generic (an 86 mm frame, 71 mm between positions, a 55 mm insert); a line differs by the corner radius, the width
of its frame edge, how glossy it is and its colour. They are not models of a maker's product and must not be presented as such.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

MM = 0.001
PITCH, FRAME, INSERT = 71 * MM, 86 * MM, 55 * MM

# line: corner radius of the frame, its thickness, how far the insert stands out, roughness, clear coat (glass)
LINES = {
    'mosaic': dict(r=2.5, t=9, edge=2, rough=0.38, coat=0.0),
    'valena': dict(r=9, t=10, edge=3, rough=0.32, coat=0.1),
    'merten': dict(r=1.5, t=10, edge=2, rough=0.12, coat=0.6),
    'bseed_glass': dict(r=4, t=8, edge=1, rough=0.04, coat=1.0, glass=True),
    'bseed_plastic': dict(r=6, t=9, edge=2, rough=0.3, coat=0.1),
}
FITS = {'white': (0.90, 0.90, 0.88), 'black': (0.012, 0.012, 0.014), 'grey': (0.28, 0.29, 0.31), 'gold': (0.62, 0.47, 0.20)}


def arg(name, default):
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    return a[a.index('--' + name) + 1] if '--' + name in a else default


def mat(name, color, rough=0.4, coat=0.0, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.03
    return m


def obj(name, bm, material, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location, o.rotation_euler = loc, rot
    o.data.materials.append(material)
    if bevel:
        b = o.modifiers.new('bevel', 'BEVEL')
        b.width, b.segments, b.limit_method, b.angle_limit = bevel, 4, 'ANGLE', math.radians(40)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
        try:
            o.modifiers.new('wn', 'WEIGHTED_NORMAL')
        except Exception:
            pass
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


def cyl(r, d, seg=64):
    """a cylinder of radius r whose axis runs into the wall (Y), d deep"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d)
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
    def __init__(self, line, fit):
        L = LINES[line]
        self.L, self.glass = L, L.get('glass', False)
        c = FITS[fit]
        key = tuple(min(1, x * 1.06 + 0.005) for x in c)
        self.frame = mat('frame', c, L['rough'], L['coat'])
        self.key = mat('key', key, max(0.18, L['rough']), L['coat'] * 0.5)
        self.dark = mat('recess', tuple(x * 0.7 for x in key), 0.5)
        self.hole = mat('hole', (0.01, 0.01, 0.01), 0.6)
        self.metal = mat('metal', (0.75, 0.74, 0.70), 0.25, metal=1.0)
        self.led = bpy.data.materials.new('led')
        self.led.use_nodes = True
        b = next(n for n in self.led.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs['Emission Color'].default_value = (0.25, 0.65, 1, 1)
        b.inputs['Emission Strength'].default_value = 6
        b.inputs['Base Color'].default_value = (0.1, 0.3, 0.6, 1)

    # every part is built around (x, z) on the wall, standing out from y = 0 towards -Y
    def plate(self, x, z, n):
        L = self.L
        w = FRAME + PITCH * (n - 1)
        self.plate_obj = obj('frame', slab(w, L['t'] * MM, FRAME, L['r'] * MM), self.frame, (x, -L['t'] * MM / 2, z), bevel=0.9 * MM)
        return [x - PITCH * (n - 1) / 2 + PITCH * i for i in range(n)]

    def front(self):
        return -(self.L['t'] + self.L['edge']) * MM

    def insert(self, x, z, material=None, extra=0.0):
        d = (self.L['t'] + self.L['edge']) * MM + extra
        return obj('insert', slab(INSERT, d, INSERT, 1.2 * MM), material or self.key, (x, -d / 2, z), bevel=0.5 * MM)

    def sw(self, x, z, g=1, on=()):
        gap, d = 0.6 * MM, (self.L['t'] + self.L['edge']) * MM
        w = (INSERT - gap * (g - 1)) / g
        for i in range(g):
            cx = x - INSERT / 2 + w / 2 + i * (w + gap)
            tilt = math.radians(-3.2 if i in on else 3.2)
            if self.glass:  # a flat glass key with a lit ring
                obj('key', slab(w, d, INSERT, 1.0 * MM), self.key, (cx, -d / 2, z), bevel=0.4 * MM)
                bm = bmesh.new()
                bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=4.6 * MM, radius2=4.6 * MM, depth=0.3 * MM)
                bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
                ring = obj('led', bm, self.led, (cx, -d - 0.05 * MM, z), smooth=False)
                s = ring.modifiers.new('s', 'SOLIDIFY')
                s.thickness = 0.9 * MM
            else:
                obj('rocker', slab(w, 3.2 * MM, INSERT, 1.0 * MM), self.key, (cx, -d - 0.8 * MM, z), rot=(tilt, 0, 0), bevel=0.5 * MM)
                obj('under', slab(w, d, INSERT - 2 * MM, 1.0 * MM), self.dark, (cx, -d / 2, z))

    def socket(self, x, z):
        d = (self.L['t'] + self.L['edge']) * MM
        body = self.insert(x, z)
        depth = d - 1.5 * MM  # as deep as the part stands out of the wall: the wall itself is not cut
        cutter = obj('cutter', cyl(19.5 * MM, depth * 2), self.dark, (x, -d, z), smooth=False)
        cut(body, cutter)
        cut(self.plate_obj, cutter)  # the frame is solid behind the insert: the recess goes through it too
        obj('floor', cyl(19.4 * MM, 1 * MM), self.dark, (x, -d + depth - 0.5 * MM, z))
        for sx in (-9.5, 9.5):
            obj('pin', cyl(2.4 * MM, 3 * MM, 24), self.hole, (x + sx * MM, -d + depth - 1.2 * MM, z))
        for sz in (-1, 1):
            obj('earth', slab(4 * MM, depth - 3 * MM, 1.2 * MM), self.metal, (x, -d + depth / 2 + 1 * MM, z + sz * 18.6 * MM), bevel=0.2 * MM)

    def part(self, kind, x, z):
        if kind.startswith('sw'):
            self.sw(x, z, int(kind[2:] or 1), on=(0,) if kind != 'sw1' else ())
        elif kind == 'socket':
            self.socket(x, z)
        else:
            self.insert(x, z)  # a blank cover until the kind is modelled

    def box(self, kinds, x, z):
        for cx, k in zip(self.plate(x, z, len(kinds)), kinds):
            self.part(k, cx, z)


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
    s.render.film_transparent = False
    try:
        s.view_settings.view_transform = 'AgX'
        s.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    c = tuple(int(wall_hex[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
    wall = mat('wall', lin, 0.85)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    obj('wall', bm, wall, smooth=False)
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
    light('fill', (0.8, -1.0, -0.2), 4, 1.2, (0.9, 0.95, 1))
    cam = bpy.data.cameras.new('cam')
    cam.lens = float(arg('lens', 70))
    co = bpy.data.objects.new('cam', cam)
    s.collection.objects.link(co)
    co.location = (0.16, -0.95, 0.07)
    co.rotation_euler = (Vector((0, 0, 0)) - Vector(co.location)).to_track_quat('-Z', 'Y').to_euler()
    s.camera = co


def main():
    line, fit = arg('line', 'valena'), arg('fit', 'white')
    scene(arg('wall', 'd8c7a8'), int(arg('w', 1400)), int(arg('h', 900)), int(arg('samples', 96)))
    kit = Kit(line, fit)
    boxes = [b.split('+') for b in arg('boxes', 'sw1;sw2+socket;socket').split(';')]
    widths = [FRAME + PITCH * (len(b) - 1) for b in boxes]
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
