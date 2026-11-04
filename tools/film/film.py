"""The "Einn dagur" film: keys the six scenes onto the house from house.py and renders the frames.
Run windowless:  blender -b --factory-startup --python film.py -- --frames DIR [--preview] [--w 1280 --h 960 --samples 48 --step 1]
                 [--start SECONDS --end SECONDS]  renders only that stretch, handy for trying one moment
Frames are skipped when they already exist, so a stopped render picks up where it left off.
Scenes, clock and energy live in timeline.json; hud.py draws the clock, captions and meter over the frames.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "E:/snjallheimilid/tools/film")
sys.path.insert(0, "E:/snjallheimilid/tools/film")
import house as H  # noqa: E402

FPS = 30
DUR = 66


def F(t):
    return int(round(t * FPS)) + 1


def ease_linear(owner, path):
    """Straight-line interpolation for the keys of one property."""
    ad = owner.id_data.animation_data if hasattr(owner, "id_data") else None
    if ad and ad.action:
        for layer in getattr(ad.action, "layers", []):
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for c in bag.fcurves:
                        if path in c.data_path:
                            for k in c.keyframe_points:
                                k.interpolation = "LINEAR"


def key(owner, prop, t, value):
    setattr(owner, prop, value)
    owner.keyframe_insert(prop, frame=F(t))


def key_input(sock, t, value):
    sock.default_value = value
    sock.keyframe_insert("default_value", frame=F(t))


FONT = None


def text(name, body, x, y, z, size, mat, rot, align="CENTER"):
    global FONT
    if FONT is None:
        FONT = bpy.data.fonts.load("C:/Windows/Fonts/seguisb.ttf")
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.font, cu.size = body, FONT, size
    cu.align_x, cu.align_y = align, "CENTER"
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    ob.location, ob.rotation_euler = (x, y, z), rot
    bpy.context.scene.collection.objects.link(ob)
    return ob


def torus(name, x, y, z, major, minor, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=96, minor_segments=10, location=(x, y, z), rotation=rot)
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(mat)
    for f in ob.data.polygons:
        f.use_smooth = True
    return ob


def ring_mat(name, color):
    """A glow that fades to nothing: at level 0 it is see-through, not a black ring. Returns the material and the level socket to key."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out, mix, tr, em, level, fade = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeBsdfTransparent"), nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeValue"), nt.nodes.new("ShaderNodeMath")
    em.inputs["Color"].default_value = (*color, 1)
    fade.operation, fade.use_clamp = "MULTIPLY", True
    fade.inputs[1].default_value = 2.0
    nt.links.new(level.outputs[0], em.inputs["Strength"])
    nt.links.new(level.outputs[0], fade.inputs[0])
    nt.links.new(fade.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m, level.outputs[0]


# ---- lights ---------------------------------------------------------------------------------------
EMISSIVE = {"stofa": ["shade"], "eldhus": ["led_eldhus"], "svefn": ["shade_svefn"], "bad": ["led_bad"], "forstofa": ["led_forstofa"]}
SWITCH = [
    # (t, group, level, seconds)  scene 1: the kitchen wakes softly
    (10.4, "eldhus", 0.5, 1.4),
    # scene 2: morning, everything on
    (12.9, "svefn", 1, .7), (13.2, "hol_svefn", 1, .7), (13.5, "bad", 1, .7), (13.7, "hol_bad", 1, .7),
    (13.9, "eldhus", 1, .7), (14.2, "stofa", 1, .7), (14.5, "forstofa", 1, .7),
    # one touch on the display: off room by room, ending at the door
    (21.5, "svefn", 0, .35), (21.8, "bad", 0, .35), (22.1, "hol_svefn", 0, .35), (22.4, "stofa", 0, .35),
    (22.7, "eldhus", 0, .35), (23.0, "hol_bad", 0, .35), (23.5, "forstofa", 0, .35),
    # scene 4: home
    (37.4, "forstofa", 1, .4), (38.0, "eldhus", 1, .4), (38.6, "hol_svefn", 1, .4), (38.8, "hol_bad", 1, .4), (39.3, "bad", 1, .4),
    (43.0, "forstofa", 0, 1.0),
    # scene 5: evening, only the stofa stays and dims
    (46.2, "stofa", 1, .6), (46.6, "hol_bad", 0, .5), (46.8, "bad", 0, .5), (47.0, "hol_svefn", 0, .5), (47.2, "eldhus", 0, .5),
    (48.0, "stofa", 0.7, 1.6),
    # scene 6: night, all off
    (55.4, "stofa", 0, 1.2),
    # the end card: the house warms up behind it
    (62.6, "stofa", 1, 1.6), (62.8, "eldhus", 1, 1.6), (63.0, "svefn", 1, 1.6), (63.0, "forstofa", 1, 1.6), (63.2, "bad", 1, 1.6), (63.2, "hol_bad", 1, 1.6), (63.2, "hol_svefn", 1, 1.6),
]


def key_lights(M):
    base = {g: [o.data.energy for o in obs] for g, obs in H.LIGHT_GROUPS.items()}
    ems = {g: [(m, m.node_tree.nodes["Emission"].inputs["Strength"].default_value) for m in (M[n] for n in names)] for g, names in EMISSIVE.items()}

    def put(group, t, level):
        for o, e in zip(H.LIGHT_GROUPS[group], base[group]):
            key(o.data, "energy", t, e * level)
        for m, s in ems.get(group, []):
            key_input(m.node_tree.nodes["Emission"].inputs["Strength"], t, s * level)

    for g in H.LIGHT_GROUPS:
        put(g, 0, 0)
        level = 0
        for t, group, lv, dur in sorted(SWITCH):
            if group == g:
                put(g, t, level)
                put(g, t + dur, lv)
                level = lv


# ---- time of day ----------------------------------------------------------------------------------
NIGHT = dict(sun=0.22, sunc=(0.5, 0.62, 1.0), fill=120, fillc=(0.42, 0.54, 1.0), world=0.06, panel=0.10, panelc=(0.45, 0.55, 1.0), ground=(0.24, 0.30, 0.48), exp=0.55)
MORNING = dict(sun=1.5, sunc=(1.0, 0.86, 0.70), fill=420, fillc=(1.0, 0.94, 0.86), world=0.55, panel=0.42, panelc=(1, 1, 1), ground=(1.05, 1.1, 1.15), exp=0.0)
COLD = dict(sun=0.6, sunc=(0.88, 0.94, 1.0), fill=430, fillc=(0.84, 0.91, 1.0), world=0.65, panel=0.4, panelc=(0.82, 0.9, 1.0), ground=(0.95, 1.0, 1.08), exp=0.0)
DUSK = dict(sun=0.9, sunc=(1.0, 0.68, 0.45), fill=260, fillc=(1.0, 0.82, 0.70), world=0.3, panel=0.4, panelc=(1, 0.8, 0.65), ground=(0.95, 0.9, 0.9), exp=0.05)
SUNSET = dict(sun=1.25, sunc=(1.0, 0.56, 0.32), fill=320, fillc=(1.0, 0.76, 0.58), world=0.22, panel=0.42, panelc=(1, 0.85, 0.75), ground=(1.05, 0.95, 0.88), exp=0.1)
DAY = [(0, NIGHT), (12.6, NIGHT), (14.6, MORNING), (25.5, MORNING), (28.5, COLD), (36, COLD), (44, DUSK), (47.5, SUNSET), (54.5, SUNSET), (57, NIGHT), (DUR, NIGHT)]


def key_day():
    sc = bpy.context.scene
    sun, fill = bpy.data.objects["sun"].data, bpy.data.objects["fill"].data
    bg = sc.world.node_tree.nodes["Background"].inputs["Strength"]
    em = bpy.data.materials["skypanel"].node_tree.nodes["Emission"]
    # the sky panel's colour goes through a tint
    nt = bpy.data.materials["skypanel"].node_tree
    env = next(n for n in nt.nodes if n.type == "TEX_ENVIRONMENT")
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    rgb = nt.nodes.new("ShaderNodeRGB")
    nt.links.new(env.outputs[0], mix.inputs[1])
    nt.links.new(rgb.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], em.inputs["Color"])
    tint = bpy.data.materials["ground"].node_tree.nodes["g_tint"].outputs[0]
    for t, d in DAY:
        key(sun, "energy", t, d["sun"])
        key(sun, "color", t, d["sunc"])
        key(fill, "energy", t, d["fill"])
        key(fill, "color", t, d["fillc"])
        key_input(bg, t, d["world"])
        key_input(em.inputs["Strength"], t, d["panel"])
        key_input(rgb.outputs[0], t, (*d["panelc"], 1))
        key_input(tint, t, (*d["ground"], 1))
        sc.view_settings.exposure = d["exp"]
        sc.view_settings.keyframe_insert("exposure", frame=F(t))


# ---- the events -----------------------------------------------------------------------------------
def alarm(M):
    """The clock: digits, a shake and rings of sound. Rings 2 s to 7.4 s."""
    dig = text("clock.digits", "04:50", 13.42, 6.12, 0.585, 0.046, M["clock_screen"], (math.radians(90), 0, math.radians(-90)))
    root = bpy.data.objects.new("clock.root", None)
    root.location = (13.5, 6.12, 0.56)
    bpy.context.scene.collection.objects.link(root)
    for n in ("clock", "clock.face"):
        o = bpy.data.objects[n]
        o.parent = root
        o.location = Vector(o.location) - root.location
    dig.parent = root
    dig.location = Vector(dig.location) - root.location
    t = 2.0
    i = 0
    while t < 7.4:
        key(root, "rotation_euler", t, (0, 0, math.radians(4 if i % 2 else -4)))
        t += 0.1
        i += 1
    key(root, "rotation_euler", 7.5, (0, 0, 0))
    key_input(M["clock_screen"].node_tree.nodes["Emission"].inputs["Strength"], 0, 3.0)
    glow = H.lamp("clockglow", 13.3, 6.12, 0.62, 0.0, 0.05, color=(1.0, 0.45, 0.12))
    key(glow.data, "energy", 0, 1.5)
    t = 2.0
    while t < 7.4:
        key(glow.data, "energy", t, 7)
        key(glow.data, "energy", t + 0.25, 1.5)
        t += 0.5
    key(glow.data, "energy", 8, 1.0)
    moon = H.lamp("moonroom", 10.6, 7.6, 2.3, 0.0, 0.6, color=(0.45, 0.58, 1.0))
    key(moon.data, "energy", 0, 34)
    key(moon.data, "energy", 12.6, 34)
    key(moon.data, "energy", 14, 0)
    for j in range(3):
        m, s = ring_mat(f"ring{j}", (1.0, 0.62, 0.22))
        ring = torus(f"ring{j}", 13.48, 6.12, 0.62, 0.42, 0.006, m)
        key(ring, "scale", 0, (0.1, 0.1, 1))
        key_input(s, 0, 0)
        p = 2.0 + j * 0.45
        while p < 7.0:
            key(ring, "scale", p, (0.1, 0.1, 1))
            key_input(s, p, 0)
            key_input(s, p + 0.12, 5)
            key_input(s, p + 1.25, 0)
            key(ring, "scale", p + 1.25, (0.95, 0.95, 1))
            p += 1.35


def display(M):
    """The wall display: a button, a touch ring at 20.3 s, and the screen's answer."""
    face = (math.radians(90), 0, math.radians(90))
    btn_on = H.emissive("btn", (1.0, 0.45, 0.08), 0.32)
    H.box("display.btn", 6.0925, 1.0, 1.425, 0.003, 0.17, 0.05, btn_on, 0.001)
    white = H.emissive("ui", (1, 1, 1), 1.4)
    key_input(M["display_screen"].node_tree.nodes["Emission"].inputs["Strength"], 0, 0.6)
    text("ui.title", "Heima", 6.0925, 1.0, 1.487, 0.024, white, face)
    a = text("ui.btn.a", "Slökkva öll ljós", 6.0962, 1.0, 1.423, 0.021, white, face)
    b = text("ui.btn.b", "Allt slökkt", 6.0962, 1.0, 1.423, 0.021, white, face)
    for ob, shown_before in ((a, True), (b, False)):
        key(ob, "hide_render", 0, not shown_before)
        key(ob, "hide_render", 20.45, shown_before)
    s = btn_on.node_tree.nodes["Emission"].inputs["Strength"]
    key_input(s, 20.25, 0.32)
    key_input(s, 20.4, 1.1)
    key_input(s, 21.2, 0.3)
    rm, ss = ring_mat("touch", (1, 1, 1))
    ring = torus("touch", 6.097, 1.0, 1.425, 0.03, 0.0016, rm, (0, math.radians(90), 0))
    key(ring, "scale", 20.2, (0.3, 0.3, 1))
    key_input(ss, 0, 0)
    key_input(ss, 20.2, 0)
    key_input(ss, 20.3, 8)
    key_input(ss, 20.9, 0)
    key(ring, "scale", 20.9, (1.3, 1.3, 1))


def doors():
    door = bpy.data.objects["door.outer"]
    door.hide_render = False
    for v in door.data.vertices:
        v.co.z += 1.09
    door.location.z = 0
    key(door, "scale", 0, (1, 1, 0.27))
    beam = bpy.data.lights.new("beam", "SPOT")
    beam.color, beam.spot_size, beam.spot_blend, beam.shadow_soft_size = (1.0, 0.95, 0.85), math.radians(70), 0.7, 0.2
    ob = bpy.data.objects.new("beam", beam)
    ob.location, ob.rotation_euler = (7.55, -1.4, 1.9), (math.radians(68), 0, 0)
    bpy.context.scene.collection.objects.link(ob)
    key(beam, "energy", 0, 0)
    for t0, t1 in ((16.4, 24.4), (37.0, 39.4)):
        key(door, "scale", t0 - 0.6, (1, 1, 0.27))
        key(door, "scale", t0, (1, 1, 1))
        key(door, "scale", t1 + 1.0, (1, 1, 1))
        key(door, "scale", t1 + 1.6, (1, 1, 0.27))
        key(door, "rotation_euler", t0, (0, 0, 0))
        key(door, "rotation_euler", t0 + 1.0, (0, 0, math.radians(-96)))
        key(door, "rotation_euler", t1, (0, 0, math.radians(-96)))
        key(door, "rotation_euler", t1 + 1.0, (0, 0, 0))
        key(beam, "energy", t0, 0)
        key(beam, "energy", t0 + 1.0, 420)
        key(beam, "energy", t1, 420)
        key(beam, "energy", t1 + 1.0, 0)


def curtain():
    c = bpy.data.objects["curtain.drop"]
    key(c, "hide_render", 0, True)
    key(c, "hide_render", 48.9, False)
    key(c, "scale", 49.0, (1, 1, 0.001))
    key(c, "scale", 52.0, (1, 1, 1))


def math_op(nt, kind, a, b=None):
    """A Math node on two inputs, each a number or a socket. Returns its output."""
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = kind
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


WALL_TOP = 2.6


def snow_mat():
    """White flakes, see-through wherever the camera's view of them crosses the house, so the snow falls around it and never over the rooms."""
    m = H.principled("snowflake", (1, 1, 1), 0.6)
    nt = m.node_tree
    bsdf, out = nt.nodes["Principled BSDF"], nt.nodes["Material Output"]
    geo, sp, si = nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sp.inputs[0])
    nt.links.new(geo.outputs["Incoming"], si.inputs[0])
    hidden = None
    for h in (0.0, WALL_TOP):
        # where the ray to the camera crosses this height, inside the footprint or not
        along = math_op(nt, "DIVIDE", math_op(nt, "SUBTRACT", sp.outputs["Z"], h), si.outputs["Z"])
        qx = math_op(nt, "SUBTRACT", sp.outputs["X"], math_op(nt, "MULTIPLY", si.outputs["X"], along))
        qy = math_op(nt, "SUBTRACT", sp.outputs["Y"], math_op(nt, "MULTIPLY", si.outputs["Y"], along))
        in_x = math_op(nt, "MULTIPLY", math_op(nt, "GREATER_THAN", qx, -0.5), math_op(nt, "LESS_THAN", qx, 14.5))
        in_y = math_op(nt, "MULTIPLY", math_op(nt, "GREATER_THAN", qy, -0.7), math_op(nt, "LESS_THAN", qy, 10.5))
        inside = math_op(nt, "MULTIPLY", in_x, in_y)
        hidden = inside if hidden is None else math_op(nt, "MAXIMUM", hidden, inside)
    mix, tr = nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(hidden, mix.inputs[0])
    nt.links.new(bsdf.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m


def frost_mat(name, width, height, panes):
    """Hoar frost on one window: it grows in from the edge of each pane, fine-grained, and leaves the middle clear. Returns the material and the socket to key: how far in it reaches, in metres."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    tc, sep, big, fine, reach = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeTexNoise"), nt.nodes.new("ShaderNodeTexNoise"), nt.nodes.new("ShaderNodeValue")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    pane = width / panes
    # distance to the nearest edge of the pane, in metres
    fx = math_op(nt, "FRACT", math_op(nt, "DIVIDE", math_op(nt, "ADD", sep.outputs["X"], width / 2), pane))
    dx = math_op(nt, "MULTIPLY", math_op(nt, "MINIMUM", fx, math_op(nt, "SUBTRACT", 1.0, fx)), pane)
    dz = math_op(nt, "SUBTRACT", height / 2, math_op(nt, "ABSOLUTE", sep.outputs["Z"]))
    edge = math_op(nt, "MINIMUM", dx, dz)
    for n, sc in ((big, 7.0), (fine, 45.0)):
        n.inputs["Scale"].default_value, n.inputs["Detail"].default_value, n.inputs["Roughness"].default_value = sc, 12, 0.62
        nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    wander = math_op(nt, "MULTIPLY", math_op(nt, "SUBTRACT", big.outputs[0], 0.5), 0.7)
    grain = math_op(nt, "MULTIPLY", math_op(nt, "SUBTRACT", fine.outputs[0], 0.5), 0.9)
    front = math_op(nt, "SUBTRACT", math_op(nt, "ADD", math_op(nt, "ADD", reach.outputs[0], wander), grain), edge)
    clamp = nt.nodes.new("ShaderNodeClamp")
    clamp.inputs["Min"].default_value, clamp.inputs["Max"].default_value = 0.0, 0.88
    nt.links.new(math_op(nt, "DIVIDE", front, 0.3), clamp.inputs["Value"])
    out, mix, tr, ice, dif, thru = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeBsdfTransparent"), nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeBsdfDiffuse"), nt.nodes.new("ShaderNodeBsdfTranslucent")
    dif.inputs["Color"].default_value = (0.94, 0.97, 1, 1)
    thru.inputs["Color"].default_value = (0.94, 0.97, 1, 1)
    ice.inputs[0].default_value = 0.5
    nt.links.new(dif.outputs[0], ice.inputs[1])
    nt.links.new(thru.outputs[0], ice.inputs[2])
    # the cold daylight through the ice, so it stays pale whatever colour the room is
    glow, lit = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeAddShader")
    glow.inputs["Color"].default_value = (0.78, 0.87, 1, 1)
    glow.inputs["Strength"].default_value = 0.7
    nt.links.new(ice.outputs[0], lit.inputs[0])
    nt.links.new(glow.outputs[0], lit.inputs[1])
    nt.links.new(clamp.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(lit.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m, reach.outputs[0]


def cold():
    """Scene 3: snow falling, frost on the glass, and the floor heating that answers."""
    rnd = random.Random(3)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    ball = [tuple(v.co) for v in bm.verts]
    tris = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    verts, faces = [], []
    while len(verts) < 5000 * len(ball):
        x, y, z = rnd.uniform(-8, 22), rnd.uniform(-10, 18), rnd.uniform(0, 26)
        if -0.5 < x < 14.5 and -0.7 < y < 10.5:
            continue
        r = rnd.uniform(0.02, 0.045)
        n = len(verts)
        verts += [(x + r * a, y + r * b, z + r * c) for a, b, c in ball]
        faces += [[n + i for i in t] for t in tris]
    me = bpy.data.meshes.new("snow")
    me.from_pydata(verts, [], faces)
    for f in me.polygons:
        f.use_smooth = True
    me.materials.append(snow_mat())
    ob = bpy.data.objects.new("snow", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (0, 0, 13)
    key(ob, "location", 26.8, (0, 0, 13))
    key(ob, "location", 41.0, (0, 0, -27))
    ease_linear(ob, "location")
    g = bpy.data.materials["ground"].node_tree.nodes["g_snow"].inputs[0]
    for t, v in ((0, 0), (27.5, 0), (33, 0.9), (44.5, 0.9), (47.5, 0.12), (55, 0.12)):
        key_input(g, t, v)
    # frost on the windows, three panes in the big one and two in the small one
    for name, cx, cz, w, h, panes in (("frost.a", 3.7, 1.25, 4.8, 2.4, 3), ("frost.b", 10.55, 1.55, 2.7, 1.5, 2)):
        m, reach = frost_mat(name, w, h, panes)
        H.box(name, cx, 9.94, cz, w, 0.004, h, m)
        for t, v in ((0, -0.75), (28, -0.75), (33, 0.2), (44.5, 0.2), (47, -0.75), (DUR, -0.75)):
            key_input(reach, t, v)
    # underfloor pipes that glow when the heating runs
    for name in ("floor", "tile"):
        mat = bpy.data.materials[name]
        nt = mat.node_tree
        bsdf, out = nt.nodes["Principled BSDF"], nt.nodes["Material Output"]
        add, em, tc, mp, wave, ramp = nt.nodes.new("ShaderNodeAddShader"), nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeMapping"), nt.nodes.new("ShaderNodeTexWave"), nt.nodes.new("ShaderNodeValToRGB")
        em.inputs["Color"].default_value = (1.0, 0.20, 0.03, 1)
        wave.inputs["Scale"].default_value = 3.2
        wave.inputs["Distortion"].default_value = 0.6
        wave.bands_direction = "Y"
        ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.80, 0.97
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
        nt.links.new(wave.outputs[0], ramp.inputs["Fac"])
        strength = nt.nodes.new("ShaderNodeMath")
        strength.operation = "MULTIPLY"
        nt.links.new(ramp.outputs[0], strength.inputs[0])
        nt.links.new(strength.outputs[0], em.inputs["Strength"])
        nt.links.new(bsdf.outputs[0], add.inputs[0])
        nt.links.new(em.outputs[0], add.inputs[1])
        nt.links.new(add.outputs[0], out.inputs["Surface"])
        for t, v in ((0, 0), (30.5, 0), (33.5, 1.3), (36, 1.3), (38.5, 0.0)):
            key_input(strength.inputs[1], t, v)
        key_input(mp.inputs["Location"], 30, (0, 0, 0))
        key_input(mp.inputs["Location"], 38.5, (0, -1.2, 0))


def water():
    """Scene 6: water on the bathroom floor, seen by the sensor."""
    blue, s = ring_mat("water.ring", (0.15, 0.5, 1.0))
    r = torus("water.ring", 12.2, 2.6, 0.03, 1.0, 0.02, blue)
    pool = H.principled("pool", (0.1, 0.2, 0.32), 0.03)
    H.cylinder("water.pool", 12.2, 2.6, 0.012, 0.42, 0.006, pool).scale = (1, 0.8, 1)
    bpy.data.objects["water.pool"].hide_render = True
    key(bpy.data.objects["water.pool"], "hide_render", 0, True)
    key(bpy.data.objects["water.pool"], "hide_render", 57.9, False)
    li = H.lamp("water", 12.2, 2.6, 0.5, 0.0, 0.2, color=(0.2, 0.5, 1.0))
    key_input(s, 0, 0)
    key(li.data, "energy", 0, 0)
    t = 58.0
    while t < 62.2:
        key_input(s, t, 0)
        key(r, "scale", t, (0.25, 0.25, 1))
        key(li.data, "energy", t, 4)
        key_input(s, t + 0.15, 12)
        key(li.data, "energy", t + 0.15, 32)
        key_input(s, t + 1.1, 0)
        key(r, "scale", t + 1.1, (1.2, 1.2, 1))
        key(li.data, "energy", t + 1.1, 4)
        t += 1.2
    key(li.data, "energy", 63, 0)
    # the floor is dry again behind the end card
    key(bpy.data.objects["water.pool"], "scale", 61.8, (1, 0.8, 1))
    key(bpy.data.objects["water.pool"], "scale", 63.0, (0.01, 0.008, 1))


# ---- camera ---------------------------------------------------------------------------------------
PATH = [
    # t, position, looks at, lens
    (0.0, (7.0, -9.2, 12.4), (7.0, 4.8, 0.2), 28),
    (2.8, (7.2, -7.9, 11.2), (7.3, 5.0, 0.2), 28),
    (4.3, (11.9, 4.9, 4.0), (13.2, 6.1, 0.6), 30),
    (5.8, (12.4, 5.6, 0.95), (13.45, 6.12, 0.62), 40),
    (7.4, (12.5, 5.68, 0.9), (13.45, 6.12, 0.62), 44),
    (9.4, (9.0, 6.05, 1.42), (4.0, 3.6, 0.95), 32),
    (12.8, (8.65, 5.95, 1.40), (4.0, 3.55, 0.95), 32),
    (14.2, (8.2, 4.6, 4.6), (7.0, 4.6, 0.2), 28),
    (15.8, (7.0, -7.4, 10.8), (7.0, 5.0, 0.2), 28),
    (17.2, (7.0, -7.1, 10.5), (7.1, 4.6, 0.2), 28),
    (18.4, (7.5, -1.0, 4.6), (6.6, 1.0, 1.2), 30),
    (19.6, (7.32, 1.05, 1.5), (6.09, 1.0, 1.44), 62),
    (20.9, (7.18, 1.03, 1.47), (6.09, 1.0, 1.44), 66),
    (22.0, (7.6, -1.0, 4.6), (6.8, 1.6, 1.0), 30),
    (23.3, (7.0, -7.2, 10.6), (7.0, 4.9, 0.2), 28),
    (26.0, (6.8, -7.5, 10.9), (7.0, 5.0, 0.2), 28),
    (31.0, (2.6, -6.6, 10.4), (6.6, 5.0, 0.2), 28),
    (36.0, (0.6, -5.0, 9.6), (6.4, 4.4, 0.2), 28),
    (38.4, (6.2, -5.8, 8.4), (7.4, 2.8, 0.3), 30),
    (44.0, (6.8, -6.8, 9.8), (7.0, 4.2, 0.2), 28),
    (46.4, (5.6, -3.5, 8.0), (4.8, 6.6, 0.4), 28),
    (48.6, (3.6, 0.9, 5.6), (3.8, 9.0, 0.9), 28),
    (54.4, (3.7, 1.6, 5.1), (3.8, 9.0, 1.0), 28),
    (56.8, (7.0, -7.0, 10.6), (7.0, 4.8, 0.2), 28),
    (59.2, (11.4, -2.6, 7.6), (11.8, 2.6, 0.2), 32),
    (61.8, (11.5, -2.2, 7.1), (11.9, 2.7, 0.2), 32),
    (64.0, (7.0, -8.2, 11.8), (7.0, 4.6, 0.2), 28),
    (66.0, (7.0, -8.8, 12.4), (7.0, 4.6, 0.2), 28),
]


def key_camera():
    sc = bpy.context.scene
    cam = bpy.data.cameras.new("film")
    ob = bpy.data.objects.new("film", cam)
    tg = bpy.data.objects.new("film.target", None)
    sc.collection.objects.link(ob)
    sc.collection.objects.link(tg)
    con = ob.constraints.new("TRACK_TO")
    con.target, con.track_axis, con.up_axis = tg, "TRACK_NEGATIVE_Z", "UP_Y"
    sc.camera = ob
    cam.sensor_width = 36
    for t, p, a, lens in PATH:
        key(ob, "location", t, p)
        key(tg, "location", t, a)
        key(cam, "lens", t, lens)


def main():
    H.clear()
    M = H.build()
    H.ceiling()
    H.world("belfast_sunset", 0.22, 0.0)
    H.evening()
    key_lights_groups_ready = None  # lights get keyed after the water lamp is added separately
    alarm(M)
    display(M)
    doors()
    curtain()
    cold()
    key_day()
    key_lights(M)
    water()
    key_camera()
    sc = bpy.context.scene
    preview = "--preview" in sys.argv
    H.setup_render(int(H.arg("samples", 16 if preview else 48)), int(H.arg("w", 640 if preview else 1280)), int(H.arg("h", 480 if preview else 960)))
    sc.render.fps = FPS
    sc.frame_start = F(float(H.arg("start", 0)))
    sc.frame_end = F(float(H.arg("end", DUR))) - 1
    sc.frame_step = int(H.arg("step", 3 if preview else 1))
    sc.render.use_overwrite = False
    sc.render.use_placeholder = False
    sc.render.use_persistent_data = True
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 95
    sc.render.filepath = H.arg("frames").rstrip("/") + "/f_"
    if H.arg("save"):
        bpy.ops.wm.save_as_mainfile(filepath=H.arg("save"))
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
