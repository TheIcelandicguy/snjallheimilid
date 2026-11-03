"""The house for the "Einn dagur" film, built in Blender from the owner's reference picture (2026-11-03).
Run windowless:  blender -b --factory-startup --python house.py -- --out still.png [--samples 128] [--view overview|bedroom] [--save house.blend]

Metres: x to the right, y towards the big window, z up, origin at the outer front-left corner.
  Stofa      x 0-7.2, y 5-10   big window in the back wall, TV on the left wall
  Eldhús     x 0-6,   y 0-5    open to the stofa; a stub wall on the left marks the line
  Svefnherb. x 7.2-14, y 4.6-10  door in its left wall near the front, looking towards the kitchen
  Forstofa   x 6-9,   y 0-3.6  outer door in the front wall, inner door in the back wall, the wall display beside the door
  Hol        x 6-9,   y 3.6-4.6  no hallway as such: one light outside the bathroom door, one outside the bedroom door
  Baðherb.   x 9-14,  y 0-4.4  door from the hol
Every light belongs to a named group (LIGHT_GROUPS) so the film can switch them.
"""
import math
import pathlib
import random
import sys

import bmesh
import bpy
from mathutils import Vector

ASSETS = pathlib.Path("E:/motion-tools/assets")
H = 2.6          # wall height
T_OUT, T_IN = 0.22, 0.12
LOW = 0.6        # the dollhouse cut on the walls that face the overview camera
WARM = (1.0, 0.72, 0.45)
LIGHT_GROUPS = {}


def arg(name, default=None):
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return a[a.index("--" + name) + 1] if "--" + name in a else default


# ---- materials ----------------------------------------------------------------------------------
def principled(name, color=(0.8, 0.8, 0.8), rough=0.6, metal=0.0, transmission=0.0, ior=1.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["IOR"].default_value = ior
    return m


def textured(name, folder, scale=1.0, tint=(1, 1, 1), rough_mul=1.0, bump=0.3, plain=False):
    """A PBR texture mapped in metres through object coordinates, so no UVs are needed."""
    m = principled(name)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc, mp = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    d = ASSETS / "textures" / folder

    def tex(file, color=False):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(str(d / file))
        if not color:
            n.image.colorspace_settings.name = "Non-Color"
        n.projection = "BOX"
        n.projection_blend = 0.2
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        return n

    mix = nt.nodes.new("ShaderNodeRGB")
    mix.outputs[0].default_value = (*tint, 1)
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = "MULTIPLY"
    if plain:
        nt.links.new(mix.outputs[0], b.inputs["Base Color"])
    else:
        nt.links.new(tex("diff.jpg", True).outputs["Color"], mul.inputs[0])
        nt.links.new(mix.outputs[0], mul.inputs[1])
        nt.links.new(mul.outputs[0], b.inputs["Base Color"])
    if (d / "rough.jpg").exists():
        mr = nt.nodes.new("ShaderNodeMath")
        mr.operation = "MULTIPLY"
        mr.inputs[1].default_value = rough_mul
        nt.links.new(tex("rough.jpg").outputs["Color"], mr.inputs[0])
        nt.links.new(mr.outputs[0], b.inputs["Roughness"])
    if (d / "nor.jpg").exists():
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = bump
        nt.links.new(tex("nor.jpg").outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def shade(name, strength=7.0):
    """A lamp shade: pale cloth when off, glowing when on. Keeps a node called Emission for the film to key."""
    m = emissive(name, WARM, strength)
    nt = m.node_tree
    out, e = nt.nodes["Material Output"], nt.nodes["Emission"]
    add, dif = nt.nodes.new("ShaderNodeAddShader"), nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.inputs["Color"].default_value = (0.72, 0.66, 0.56, 1)
    nt.links.new(dif.outputs[0], add.inputs[0])
    nt.links.new(e.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs[0])
    return m


def emissive(name, color=WARM, strength=8.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out, e = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs[0])
    return m


# ---- geometry -----------------------------------------------------------------------------------
def box(name, cx, cy, cz, sx, sy, sz, mat, bevel=0.0, coll=None):
    """A box given centre and full size, with real vertex coordinates (no object scale)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = (cx, cy, cz)
    me.materials.append(mat)
    (coll or bpy.context.scene.collection).objects.link(ob)
    if bevel:
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, 3, "ANGLE"
    return ob


def soft(name, cx, cy, cz, sx, sy, sz, mat, rz=0.0, rx=0.0):
    """A cushion: a subdivided box, rounded."""
    ob = box(name, cx, cy, cz, sx, sy, sz, mat)
    ob.rotation_euler = (rx, 0, rz)
    mod = ob.modifiers.new("round", "BEVEL")
    mod.width, mod.segments = min(sx, sy, sz) * 0.42, 6
    mod.harden_normals = False
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def wall(name, a, b, h, t, mat, openings=()):
    """A wall along x or y from a to b, cut by openings (start, end, bottom, top) in metres along the wall from a."""
    (x1, y1), (x2, y2) = a, b
    along_x = abs(x2 - x1) > abs(y2 - y1)
    length = abs(x2 - x1) if along_x else abs(y2 - y1)
    sign = 1 if (x2 - x1 if along_x else y2 - y1) > 0 else -1

    def piece(s, e, z0, z1, tag):
        if e - s < 0.001 or z1 - z0 < 0.001:
            return
        mid = (s + e) / 2 * sign
        if along_x:
            box(f"{name}.{tag}", x1 + mid, y1, (z0 + z1) / 2, e - s, t, z1 - z0, mat)
        else:
            box(f"{name}.{tag}", x1, y1 + mid, (z0 + z1) / 2, t, e - s, z1 - z0, mat)

    pos = 0.0
    for i, (s, e, z0, z1) in enumerate(sorted(openings)):
        piece(pos, s, 0, h, f"p{i}")
        piece(s, e, 0, z0, f"sill{i}")
        piece(s, e, min(z1, h), h, f"head{i}")
        pos = e
    piece(pos, length, 0, h, "end")


def pleated(name, x0, x1, y, z0, z1, mat, pleat=0.14, depth=0.045):
    """A pleated curtain hanging in a line along x, grown as a mesh so it can be scaled from the top."""
    nx, nz = max(8, int((x1 - x0) / pleat * 8)), 2
    verts, faces = [], []
    for j in range(nz):
        z = z1 + (z0 - z1) * j / (nz - 1)
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            verts.append((x - x0, depth * math.sin(2 * math.pi * (x - x0) / pleat), z - z1))
    for j in range(nz - 1):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = (x0, y, z1)       # origin at the top: scale z to bring it down
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = 0.012
    return ob


def place(asset, x, y, z=0.0, rz=0.0, scale=1.0, name=None):
    """Import a Poly Haven model and put it down; returns its root empty."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ASSETS / "models" / asset / f"{asset}.gltf"))
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name or asset, None)
    bpy.context.scene.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    root.location = (x, y, z)
    root.rotation_euler = (0, 0, math.radians(rz))
    root.scale = (scale, scale, scale)
    return root


def lamp(group, x, y, z, power, radius=0.08, color=WARM, kind="POINT", aim_down=False, angle=2.0):
    li = bpy.data.lights.new(f"{group}.{len(LIGHT_GROUPS.get(group, []))}", kind)
    li.color = color
    li.energy = power
    li.shadow_soft_size = radius
    if kind == "SPOT":
        li.spot_size, li.spot_blend = angle, 0.8
    ob = bpy.data.objects.new(li.name, li)
    ob.location = (x, y, z)
    bpy.context.scene.collection.objects.link(ob)
    LIGHT_GROUPS.setdefault(group, []).append(ob)
    return ob


def downlight(group, x, y, power=26, z=2.45):
    power *= 3.2
    """A ceiling spot: the pool of light on the floor is what reads from above."""
    return lamp(group, x, y, z, power, radius=0.05, kind="SPOT", angle=2.1)


def cylinder(name, x, y, z, r, h, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r, depth=h, location=(x, y, z))
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(mat)
    for f in ob.data.polygons:
        f.use_smooth = len(f.vertices) == 4
    return ob


def ground_mat():
    """The ground under the house: a soft evening haze, warmer towards the far side, like the picture."""
    m = principled("ground", (0.8, 0.66, 0.58), 0.95)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc, sep, rp = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeMapRange")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.80, 0.68, 0.60, 1)
    ramp.color_ramp.elements[1].color = (0.88, 0.52, 0.32, 1)
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], rp.inputs["Value"])
    rp.inputs["From Min"].default_value, rp.inputs["From Max"].default_value = 3.0, 22.0
    nt.links.new(rp.outputs[0], ramp.inputs["Fac"])
    tint, mul, snow = nt.nodes.new("ShaderNodeRGB"), nt.nodes.new("ShaderNodeMixRGB"), nt.nodes.new("ShaderNodeMixRGB")
    tint.name, snow.name = "g_tint", "g_snow"
    tint.outputs[0].default_value = (1, 1, 1, 1)
    mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = 1.0
    nt.links.new(ramp.outputs[0], mul.inputs[1])
    nt.links.new(tint.outputs[0], mul.inputs[2])
    nt.links.new(mul.outputs[0], snow.inputs[1])
    snow.inputs[2].default_value = (0.82, 0.86, 0.92, 1)
    snow.inputs[0].default_value = 0.0
    nt.links.new(snow.outputs[0], b.inputs["Base Color"])
    return m


def sky_panel():
    """An emitter behind the windows that shows the sky picture along the viewing ray, tilted up so a camera looking down still sees sky."""
    m = bpy.data.materials.new("skypanel")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out, e, geo, env = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(ASSETS / "hdri" / "belfast_sunset.hdr"))
    neg, add = nt.nodes.new("ShaderNodeVectorMath"), nt.nodes.new("ShaderNodeVectorMath")
    neg.operation, add.operation = "SCALE", "ADD"
    neg.inputs["Scale"].default_value = -1.0
    add.inputs[1].default_value = (0, 0, 0.62)
    nt.links.new(geo.outputs["Incoming"], neg.inputs[0])
    nt.links.new(neg.outputs[0], add.inputs[0])
    nt.links.new(add.outputs[0], env.inputs["Vector"])
    nt.links.new(env.outputs[0], e.inputs["Color"])
    e.inputs["Strength"].default_value = float(arg("skypanel", 0.55))
    nt.links.new(e.outputs[0], out.inputs[0])
    return m


def ceiling():
    """One quad facing down: opaque seen from inside a room, transparent from the overview above it."""
    m = bpy.data.materials.new("ceiling")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out, mix, geo = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeNewGeometry")
    dif, tr = nt.nodes.new("ShaderNodeBsdfDiffuse"), nt.nodes.new("ShaderNodeBsdfTransparent")
    dif.inputs["Color"].default_value = (0.70, 0.66, 0.62, 1)
    nt.links.new(geo.outputs["Backfacing"], mix.inputs[0])
    nt.links.new(dif.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    me = bpy.data.meshes.new("ceiling")
    me.from_pydata([(-0.2, -0.2, H), (-0.2, 10.2, H), (14.2, 10.2, H), (14.2, -0.2, H)], [], [(0, 1, 2, 3)])
    me.materials.append(m)
    ob = bpy.data.objects.new("ceiling", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def sofa(M):
    """The pale L-shaped sofa of the picture, its back to the window."""
    sf, cu = M["sofa"], M["cushion"]
    for i, x in enumerate((2.6, 3.6, 4.6)):
        soft("sofa.seat", x, 8.45, 0.3, 0.98, 0.92, 0.36, sf)
        soft("sofa.back", x, 8.92, 0.62, 0.98, 0.28, 0.6, sf)
    soft("sofa.chaise", 5.5, 7.95, 0.3, 0.95, 1.9, 0.36, sf)
    soft("sofa.backR", 5.5, 8.92, 0.62, 0.95, 0.28, 0.6, sf)
    soft("sofa.arm", 2.0, 8.5, 0.46, 0.26, 1.15, 0.6, sf)
    soft("sofa.arm", 6.0, 8.0, 0.46, 0.22, 2.0, 0.55, sf)
    soft("cushion", 2.55, 8.62, 0.66, 0.5, 0.2, 0.42, cu, rz=0.15, rx=-0.3)
    soft("cushion", 3.5, 8.62, 0.66, 0.5, 0.2, 0.42, sf, rz=-0.1, rx=-0.3)
    soft("cushion", 5.3, 8.62, 0.66, 0.5, 0.2, 0.42, cu, rz=0.1, rx=-0.3)
    soft("throw.sofa", 2.5, 8.2, 0.5, 0.65, 0.95, 0.05, M["throw"])


def candles(name, x, y, z, M):
    for i, (dx, dy, h) in enumerate(((-0.12, 0, 0.14), (0, 0.06, 0.2), (0.12, -0.02, 0.1))):
        cylinder(f"candle.{name}{i}", x + dx, y + dy, z + h / 2, 0.028, h, M["ceramic"])
        soft(f"flame.{name}{i}", x + dx, y + dy, z + h + 0.025, 0.018, 0.018, 0.04, M["shade"])
    lamp("stofa", x, y, z + 0.28, 2.5, 0.04)


# ---- the house ----------------------------------------------------------------------------------
def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def build():
    M = {
        "wall": principled("wall", (0.66, 0.60, 0.54), 0.8),
        "cap": principled("cap", (0.74, 0.70, 0.66), 0.6),
        "floor": textured("floor", "herringbone_parquet", 0.38, (0.80, 0.80, 0.80), 1.5, 0.4),
        "tile": textured("tile", "concrete_floor", 0.5, (0.20, 0.20, 0.20), 0.8, 0.25, True),
        "marble": textured("marble", "marble_01", 0.7, (1.0, 0.98, 0.95), 0.5, 0.05),
        "linen": textured("linen", "rough_linen", 2.2, (0.62, 0.50, 0.36), 1.0, 0.4, True),
        "sofa": textured("sofa", "rough_linen", 3.0, (0.70, 0.62, 0.52), 1.0, 0.4, True),
        "cushion": textured("cushion", "rough_linen", 3.0, (0.42, 0.26, 0.13), 1.0, 0.4, True),
        "bedlinen": textured("bedlinen", "rough_linen", 2.5, (0.78, 0.72, 0.64), 1.0, 0.3, True),
        "throw": textured("throw", "rough_linen", 3.0, (0.20, 0.11, 0.06), 1.0, 0.6, True),
        "rug": textured("rug", "rough_linen", 4.0, (0.46, 0.35, 0.24), 1.0, 0.9, True),
        "cab": principled("cab", (0.56, 0.50, 0.44), 0.45),
        "cabdark": principled("cabdark", (0.20, 0.17, 0.15), 0.4),
        "wood": principled("wood", (0.33, 0.19, 0.10), 0.45),
        "door": principled("door", (0.28, 0.17, 0.10), 0.4),
        "frame": principled("frame", (0.05, 0.05, 0.05), 0.35, 0.5),
        "black": principled("black", (0.012, 0.012, 0.012), 0.38),
        "steel": principled("steel", (0.75, 0.75, 0.72), 0.25, 1.0),
        "brass": principled("brass", (0.72, 0.50, 0.22), 0.3, 1.0),
        "ceramic": principled("ceramic", (0.92, 0.91, 0.89), 0.12),
        "glass": principled("glass", (1, 1, 1), 0.02, 0, 1.0, 1.45),
        "mirror": principled("mirror", (0.95, 0.95, 0.95), 0.02, 1.0),
        "shade": shade("shade"),
        "shade_svefn": shade("shade_svefn"),
        "led_eldhus": emissive("led_eldhus", WARM, 18.0),
        "led_bad": emissive("led_bad", WARM, 18.0),
        "led_forstofa": emissive("led_forstofa", WARM, 18.0),
        "clock_screen": emissive("clock_screen", (1.0, 0.42, 0.08), 1.2),
        "display_screen": emissive("display_screen", (0.05, 0.09, 0.16), 1.0),
        "ground": ground_mat(),
        "tree": principled("tree", (0.012, 0.012, 0.008), 0.9),
    }
    W, D = 14.0, 10.0
    # ground and floors
    box("ground", W / 2, D / 2, -0.32, 300, 300, 0.5, M["ground"])
    box("slab", W / 2, D / 2, -0.14, W + 0.5, D + 0.5, 0.22, M["cap"])
    fl = box("floor", W / 2, D / 2, -0.005, W, D, 0.01, M["floor"])
    fl.location = (0, 0, -0.005)
    for v in fl.data.vertices:
        v.co.x += W / 2
        v.co.y += D / 2
    bt = box("floor.bath", 11.5, 2.2, 0.003, 5.0, 4.4, 0.006, M["tile"])

    w = M["wall"]
    # outer walls: back and left full height, front and right cut down for the view
    wall("w.back", (0, D), (W, D), H, T_OUT, w, [(1.3, 6.1, 0.05, 2.45), (9.2, 11.9, 0.8, 2.3)])
    wall("w.left", (0, 0), (0, D), H, T_OUT, w, [])
    wall("w.front", (0, 0), (W, 0), LOW, T_OUT, w, [(7.0, 8.1, 0.0, 2.2)])
    wall("w.right", (W, 0), (W, D), H * 0.62, T_OUT, w, [])
    # partitions
    wall("w.stub", (0, 5), (2.2, 5), H * 0.85, T_IN, w)
    wall("w.bed.left", (7.2, 4.6), (7.2, D), H, T_IN, w, [(0.35, 1.25, 0.0, 2.1)])
    wall("w.bed.front", (7.2, 4.6), (W, 4.6), H * 0.8, T_IN, w)
    wall("w.ent.left", (6, 0), (6, 3.6), H * 0.8, T_IN, w)
    wall("w.ent.back", (6, 3.6), (9, 3.6), H * 0.8, T_IN, w, [(1.0, 1.9, 0.0, 2.05)])
    wall("w.bath.left", (9, 0), (9, 4.6), H * 0.8, T_IN, w, [(3.65, 4.5, 0.0, 2.05)])

    # big window: dark frames and glass
    for x in (1.3, 2.9, 4.5, 6.1):
        box("win.mull", x, D, 1.25, 0.05, 0.08, 2.4, M["frame"])
    box("win.top", 3.7, D, 2.43, 4.85, 0.08, 0.05, M["frame"])
    box("win.bot", 3.7, D, 0.07, 4.85, 0.08, 0.05, M["frame"])
    box("win.glass", 3.7, D, 1.25, 4.8, 0.01, 2.4, M["glass"])
    box("win2.top", 10.55, D, 2.28, 2.75, 0.08, 0.05, M["frame"])
    box("win2.bot", 10.55, D, 0.82, 2.75, 0.08, 0.05, M["frame"])
    for x in (9.2, 10.55, 11.9):
        box("win2.mull", x, D, 1.55, 0.05, 0.08, 1.5, M["frame"])
    box("win2.glass", 10.55, D, 1.55, 2.7, 0.01, 1.5, M["glass"])

    bd = sky_panel()
    box("sky.panel", W / 2, D + 0.3, 1.2, W, 0.01, 2.4, bd)
    # curtains: the stay-open panels beside the window; the one that comes down in the evening is its own object
    pleated("curtain.left", 0.45, 1.5, D - 0.2, 0.02, 2.5, M["linen"])
    pleated("curtain.right", 5.75, 7.0, D - 0.2, 0.02, 2.5, M["linen"])
    pleated("curtain.bed", 11.8, 12.7, D - 0.2, 0.02, 2.5, M["linen"])
    c = pleated("curtain.drop", 1.45, 5.8, D - 0.26, 0.02, 2.5, M["linen"])
    c.scale.z = 0.001       # the evening scene brings it down from the top
    c.hide_render = True

    # stofa
    box("rug.living", 3.9, 7.1, 0.008, 4.2, 3.0, 0.014, M["rug"])
    sofa(M)
    place("mid_century_lounge_chair", 6.0, 6.5, rz=-115, name="chair")
    cylinder("coffee.top", 3.9, 6.75, 0.36, 0.55, 0.03, M["marble"])
    cylinder("coffee.leg", 3.9, 6.75, 0.17, 0.32, 0.34, M["cabdark"])
    place("ceramic_vase_01", 3.75, 6.75, 0.375, scale=0.7, name="vase")
    for i in range(3):
        box(f"book{i}", 4.15, 6.65, 0.39 + i * 0.03, 0.26 - i * .02, 0.2 - i * .015, 0.028, M["black"] if i == 1 else M["cabdark"], 0.003)
    # floor lamp
    box("flamp.base", 6.6, 8.7, 0.015, 0.28, 0.28, 0.03, M["black"], 0.01)
    box("flamp.pole", 6.6, 8.7, 0.8, 0.025, 0.025, 1.55, M["black"])
    soft("flamp.shade", 6.6, 8.7, 1.62, 0.42, 0.42, 0.26, M["shade"])
    lamp("stofa", 6.6, 8.7, 1.62, 45, 0.15)
    # TV wall
    box("tv", 0.16, 7.5, 1.3, 0.05, 1.5, 0.86, M["black"], 0.005)
    box("tv.console", 0.32, 7.5, 0.28, 0.42, 2.3, 0.34, M["wood"], 0.01)
    place("potted_plant_01", 0.65, 9.35, name="plant.living")
    candles("tv", 0.32, 6.6, 0.45, M)
    for x, y in ((1.6, 7.0), (5.6, 8.9), (3.9, 6.0)):
        downlight("stofa", x, y, 24)

    # eldhús: counter on the left wall, island, dining
    box("k.counter", 0.42, 2.7, 0.44, 0.62, 3.6, 0.88, M["cab"], 0.006)
    box("k.top", 0.44, 2.7, 0.9, 0.66, 3.64, 0.04, M["marble"], 0.004)
    box("k.tall", 0.42, 0.55, 1.1, 0.62, 0.9, 2.2, M["cab"], 0.006)
    box("k.oven", 0.74, 0.55, 1.15, 0.02, 0.6, 0.6, M["black"], 0.003)
    box("k.sink", 0.44, 2.9, 0.92, 0.4, 0.6, 0.012, M["steel"])
    box("k.tap", 0.2, 2.9, 1.08, 0.025, 0.025, 0.3, M["steel"])
    box("k.led", 0.75, 2.7, 0.87, 0.02, 3.5, 0.015, M["led_eldhus"])
    place("potted_plant_02", 0.42, 4.2, 0.92, scale=0.5, name="plant.kitchen")
    box("island", 3.5, 3.15, 0.44, 2.5, 1.0, 0.88, M["cab"], 0.006)
    box("island.top", 3.5, 3.15, 0.91, 2.62, 1.12, 0.05, M["marble"], 0.005)
    box("island.hob", 3.5, 3.25, 0.937, 0.7, 0.5, 0.006, M["black"])
    box("island.led", 3.5, 2.58, 0.05, 2.5, 0.02, 0.02, M["led_eldhus"])
    for x in (2.6, 3.5, 4.4):
        place("bar_chair_round_01", x, 2.25, rz=180, name="stool")
    place("ceramic_vase_03", 3.9, 2.95, 0.935, scale=0.6, name="vase.island")
    box("dining.top", 3.3, 1.0, 0.74, 2.2, 0.95, 0.05, M["wood"], 0.006)
    for lx, ly in ((2.35, 0.65), (4.25, 0.65), (2.35, 1.35), (4.25, 1.35)):
        box("dining.leg", lx, ly, 0.36, 0.06, 0.06, 0.72, M["wood"])
    box("dining.runner", 3.3, 1.0, 0.768, 2.3, 0.34, 0.006, M["rug"])
    for x, ry in ((2.6, 180), (4.0, 180)):
        place("dining_chair_02", x, 1.75, rz=0, name="dining.chair")
    candles("table", 3.3, 1.0, 0.771, M)
    for x, y in ((3.5, 3.15), (1.7, 3.0), (3.3, 1.0), (5.0, 4.2)):
        downlight("eldhus", x, y, 24)
    lamp("eldhus", 0.8, 2.7, 0.8, 8, 0.2)

    # small wall lights that wash the walls, as in the picture
    for g, x, y in (("stofa", 0.3, 8.9), ("stofa", 0.3, 5.9), ("forstofa", 6.2, 2.4), ("bad", 9.2, 1.4)):
        lamp(g, x, y, 1.75, 7, 0.04)
    # hol: the two lights the owner asked for instead of a hallway
    downlight("hol_bad", 8.3, 4.1, 20)
    downlight("hol_svefn", 6.6, 5.4, 20)

    # svefnherbergi
    box("rug.bed", 11.2, 7.3, 0.008, 2.6, 3.4, 0.014, M["rug"])
    box("bed.head", 13.78, 7.5, 0.6, 0.1, 2.0, 1.2, M["cabdark"], 0.02)
    box("bed.base", 12.75, 7.5, 0.2, 2.0, 1.8, 0.28, M["wood"], 0.02)
    soft("bed.mattress", 12.75, 7.5, 0.47, 2.0, 1.8, 0.28, M["bedlinen"])
    soft("bed.throw", 12.1, 7.5, 0.63, 0.72, 1.86, 0.06, M["throw"])
    for y, m in ((7.0, "bedlinen"), (8.0, "bedlinen"), (7.05, "throw"), (7.95, "throw")):
        soft("bed.pillow", 13.38 if m == "bedlinen" else 13.2, y, 0.74 if m == "bedlinen" else 0.72, 0.16, 0.62, 0.42, M[m], rx=0)
    for y in (6.25, 8.75):
        box("bed.table", 13.55, y, 0.27, 0.46, 0.46, 0.54, M["wood"], 0.01)
        ly = 6.4 if y < 7 else y
        box("blamp.stem", 13.62, ly, 0.66, 0.03, 0.03, 0.24, M["brass"])
        soft("blamp.shade", 13.62, ly, 0.86, 0.26, 0.26, 0.2, M["shade_svefn"])
        lamp("svefn", 13.55, ly, 0.88, 14, 0.1)
    # the alarm clock
    box("clock", 13.5, 6.12, 0.585, 0.14, 0.13, 0.09, M["black"], 0.012)
    box("clock.face", 13.426, 6.12, 0.585, 0.004, 0.11, 0.06, M["black"])
    box("art", 13.85, 9.4, 1.5, 0.03, 0.55, 0.75, M["cabdark"], 0.004)
    place("potted_plant_04", 13.3, 9.5, name="plant.bed")
    for x, y in ((9.0, 8.5), (10.5, 5.8)):
        downlight("svefn", x, y, 20)

    # baðherbergi
    g = M["glass"]
    box("sh.glass.a", 10.0, 3.45, 1.05, 0.012, 1.7, 2.1, g)
    box("sh.glass.b", 10.9, 2.6, 1.05, 1.8, 0.012, 2.1, g)
    box("sh.frame.a", 10.0, 2.6, 1.05, 0.03, 0.03, 2.1, M["frame"])
    box("sh.frame.top", 10.9, 2.6, 2.1, 1.8, 0.03, 0.03, M["frame"])
    box("sh.frame.side", 10.0, 3.45, 2.1, 0.03, 1.7, 0.03, M["frame"])
    box("sh.tray", 10.9, 3.5, 0.015, 1.8, 1.7, 0.03, M["tile"])
    box("sh.head", 10.9, 4.2, 2.0, 0.22, 0.22, 0.02, M["steel"])
    box("sh.pipe", 10.9, 4.32, 1.5, 0.025, 0.025, 1.0, M["steel"])
    box("sh.niche", 10.3, 4.32, 1.3, 0.5, 0.05, 0.3, M["brass"])
    box("wc.tank", 13.75, 2.9, 0.55, 0.2, 0.45, 0.5, M["ceramic"], 0.03)
    soft("wc.bowl", 13.4, 2.9, 0.34, 0.6, 0.38, 0.32, M["ceramic"])
    box("van", 13.6, 1.05, 0.55, 0.5, 1.4, 0.42, M["wood"], 0.008)
    box("van.top", 13.58, 1.05, 0.78, 0.56, 1.46, 0.04, M["ceramic"], 0.008)
    box("van.mirror", 13.86, 1.05, 1.5, 0.02, 0.75, 1.0, M["mirror"], 0.008)
    box("van.ledA", 13.84, 1.05, 2.03, 0.02, 0.8, 0.02, M["led_bad"])
    box("van.ledB", 13.84, 1.05, 0.98, 0.02, 0.8, 0.02, M["led_bad"])
    place("potted_plant_02", 13.55, 0.45, 0.8, scale=0.45, name="plant.bath")
    box("towel", 13.86, 3.8, 1.15, 0.04, 0.5, 0.75, M["bedlinen"], 0.01)
    for x, y in ((10.9, 3.4), (12.3, 1.3)):
        downlight("bad", x, y, 22)
    lamp("bad", 13.7, 1.05, 1.5, 6, 0.3)

    # forstofa
    d = box("door.outer", 8.08, 0.02, 1.09, 1.08, 0.05, 2.18, M["door"], 0.006)
    for o in d.data.vertices:
        o.co.x -= 0.54
    d.name = "door.outer"       # hinged on its right edge: a negative z turn opens it into the forstofa
    box("threshold", 7.55, 0.0, 0.012, 1.08, 0.2, 0.02, M["led_forstofa"])
    box("door.inner", 7.45, 3.6, 1.02, 0.88, 0.05, 2.03, M["door"], 0.006)
    box("door.inner.h", 7.8, 3.54, 1.0, 0.1, 0.02, 0.02, M["steel"])
    box("door.bed", 7.2, 5.4, 1.02, 0.05, 0.88, 2.03, M["door"], 0.006).hide_render = True      # open in every shot so far
    box("door.bath", 9.0, 4.07, 1.02, 0.05, 0.83, 2.03, M["door"], 0.006)
    for i in range(14):                 # the slatted wall
        box("slat", 8.86, 0.75 + i * 0.1, 1.2, 0.04, 0.06, 2.4, M["wood"])
    box("bench", 8.62, 1.4, 0.24, 0.44, 1.2, 0.08, M["wood"], 0.01)
    box("bench.led", 8.82, 1.4, 0.16, 0.02, 1.2, 0.02, M["led_forstofa"])
    box("coat", 8.76, 1.4, 1.35, 0.12, 0.38, 0.85, M["cabdark"], 0.03)
    box("mat", 7.5, 1.05, 0.008, 0.95, 0.6, 0.014, M["rug"])
    place("potted_plant_01", 6.45, 3.15, scale=0.75, name="plant.entry")
    # Shelly Wall Display XL beside the outer door: 10 inch, on the left wall at eye level
    box("display", 6.08, 1.0, 1.45, 0.018, 0.25, 0.17, M["black"], 0.003)
    box("display.screen", 6.09, 1.0, 1.45, 0.002, 0.225, 0.145, M["display_screen"])
    for x, y in ((7.5, 1.1), (7.5, 2.7)):
        downlight("forstofa", x, y, 22)

    # outside: a dark line of trees past the back wall and on the left, against the evening
    rnd = random.Random(7)
    for (cx, cy, r) in []:
        for k in range(46):
            a, h, d = rnd.uniform(0, 6.28), rnd.uniform(0.6, 2.4) * r, rnd.uniform(0, r)
            rr = rnd.uniform(0.5, 1.05)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=rr, location=(cx + d * math.cos(a), cy + d * math.sin(a), h))
            bpy.context.object.data.materials.append(M["tree"])
            for f in bpy.context.object.data.polygons:
                f.use_smooth = True
    return M


def world(hdri, strength=0.9, rotate=0.0):
    wd = bpy.data.worlds.new("sky")
    wd.use_nodes = True
    bpy.context.scene.world = wd
    nt = wd.node_tree
    bg = nt.nodes["Background"]
    env, tc, mp = nt.nodes.new("ShaderNodeTexEnvironment"), nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeMapping")
    env.image = bpy.data.images.load(str(ASSETS / "hdri" / f"{hdri}.hdr"))
    mp.inputs["Rotation"].default_value = (0, 0, rotate)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength


def evening():
    """Low warm sun from behind the house and a broad warm fill, the mood of the owner's picture."""
    sun = bpy.data.lights.new("sun", "SUN")
    sun.color, sun.energy, sun.angle = (1.0, 0.6, 0.38), 1.1, math.radians(32)
    ob = bpy.data.objects.new("sun", sun)
    ob.rotation_euler = (math.radians(50), 0, math.radians(-35))
    bpy.context.scene.collection.objects.link(ob)
    fill = bpy.data.lights.new("fill", "AREA")
    fill.shape, fill.size, fill.size_y, fill.color, fill.energy = "RECTANGLE", 16, 12, (1.0, 0.78, 0.6), 260
    ob = bpy.data.objects.new("fill", fill)
    ob.location = (7, 5, 7)
    bpy.context.scene.collection.objects.link(ob)


def camera(loc, target, lens=35):
    cam = bpy.data.cameras.new("cam")
    cam.lens = lens
    ob = bpy.data.objects.new("cam", cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = ob
    return ob


def setup_render(samples, w=1448, h=1086):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    s.cycles.device = "GPU"
    s.cycles.samples = samples
    s.cycles.use_denoising = True
    s.cycles.denoiser = "OPTIX"
    s.cycles.max_bounces = 6
    s.cycles.caustics_reflective = s.cycles.caustics_refractive = False
    s.render.resolution_x, s.render.resolution_y = w, h
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = float(arg("exposure", 0.0))


VIEWS = {
    "overview": ((7.0, -7.6, 10.9), (7.0, 5.1, 0.2), 28),
    "bedroom": ((10.0, 6.2, 1.5), (4.0, 3.9, 1.0), 24),
}


def main():
    clear()
    build()
    world("belfast_sunset", float(arg("sky", 0.22)), math.radians(arg("skyrot") and float(arg("skyrot")) or 0))
    evening()
    v = VIEWS[arg("view", "overview")]
    ceiling()
    bpy.data.objects["door.outer"].hide_render = True
    camera(*v)
    setup_render(int(arg("samples", 128)), int(arg("w", 1448)), int(arg("h", 1086)))
    if arg("save"):
        bpy.ops.wm.save_as_mainfile(filepath=arg("save"))
    if arg("out"):
        bpy.context.scene.render.filepath = arg("out")
        bpy.ops.render.render(write_still=True)
    print("LIGHT GROUPS", {k: len(x) for k, x in LIGHT_GROUPS.items()}, flush=True)


if __name__ == "__main__":
    main()
