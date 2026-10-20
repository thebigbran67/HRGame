"""Second batch: props and wall dressing that make the office feel lived in.
Same conventions as build_models.py: Unreal cm, front faces -Y, pivot at bottom center
(wall pieces: pivot at the wall-contact plane, vertically centered; ceiling light: pivot at top)."""
import math, os, sys, json, random
import numpy as np
import trimesh
from build_models import Model, MATS, write_glb

K = 1.32  # this level is built about 1.32x real size

MATS.update({
    "WallPaper":    ("#F2EEDF", 0.0, 0.85, None),
    "MemoYellow":   ("#F3DE6A", 0.0, 0.85, None),
    "MemoPink":     ("#F1A9B8", 0.0, 0.85, None),
    "MemoBlue":     ("#A9C8E8", 0.0, 0.85, None),
    "Cork":         ("#A9784A", 0.0, 0.95, None),
    "WoodFrame":    ("#5A3A22", 0.0, 0.45, None),
    "Terracotta":   ("#A0522D", 0.0, 0.80, None),
    "Soil":         ("#2B1D14", 0.0, 1.00, None),
    "Leaf":         ("#3E6B2F", 0.0, 0.55, None),
    "LeafDark":     ("#2C5124", 0.0, 0.55, None),
    "WaterJug":     ("#8DBBDA", 0.0, 0.05, None),
    "CoatTan":      ("#A88B62", 0.0, 0.90, None),
    "FluoroPanel":  ("#F4F6EE", 0.0, 0.30, [6.0, 6.2, 5.4]),
    "FixtureWhite": ("#DCDAD2", 0.0, 0.40, None),
    "ClockFace":    ("#F4F1E6", 0.0, 0.30, None),
    "PosterOrange": ("#E8763A", 0.0, 0.60, None),
    "PosterPink":   ("#D9578B", 0.0, 0.60, None),
    "PosterPurple": ("#5B3A82", 0.0, 0.60, None),
    "PosterTeal":   ("#2E9C9A", 0.0, 0.60, None),
    "PosterYellow": ("#F2C230", 0.0, 0.60, None),
    "PosterNavy":   ("#1E2A4A", 0.0, 0.60, None),
    "PhotoSky":     ("#7FA6C4", 0.0, 0.60, None),
    "PhotoGrass":   ("#5F7F3C", 0.0, 0.60, None),
    "CopierGray":   ("#BDB8AC", 0.0, 0.50, None),
    "RedLight":     ("#C0201A", 0.0, 0.30, [0.6, 0.02, 0.02]),
    "GreenLight":   ("#20A040", 0.0, 0.30, [0.02, 0.5, 0.06]),
})

rng = random.Random(1987)


def rot_box(m, center, size, mat, yaw=0, pitch=0, roll=0):
    b = trimesh.creation.box(extents=size)
    R = trimesh.transformations.euler_matrix(math.radians(roll), math.radians(pitch), math.radians(yaw), "sxyz")
    b.apply_transform(R)
    b.apply_translation(center)
    m.add(b, mat)


# ------------------------------------------------------------------ floor props
def filing_cabinet(drawers=4):
    m = Model()
    w, d = 38 * K, 66 * K
    dh = 31 * K
    h = drawers * dh + 6 * K
    m.box([-w / 2, -d / 2 + 1.5, 0], [w / 2, d / 2, h], "DeskSteel")
    m.box([-w / 2 + 2, -d / 2 + 2.5, 0], [w / 2 - 2, -d / 2 + 4, 5 * K], "KickPlate")
    for i in range(drawers):
        z0 = 5 * K + i * dh + 0.6
        z1 = z0 + dh - 1.2
        m.box([-w / 2 + 1.2, -d / 2, z0], [w / 2 - 1.2, -d / 2 + 1.6, z1], "DeskSteel")
        cz = z1 - dh * 0.32
        m.box([-7 * K, -d / 2 - 1.4, cz - 1.2], [7 * K, -d / 2, cz + 1.2], "Chrome")
        m.box([-4 * K, -d / 2 - 0.4, z1 - dh * 0.2 - 2.4 * K], [4 * K, -d / 2, z1 - dh * 0.2], "Paper")
        m.box([-4.6 * K, -d / 2 - 0.6, z1 - dh * 0.2 - 2.8 * K], [4.6 * K, -d / 2 - 0.4, z1 - dh * 0.2 - 2.4 * K], "Chrome")
    # lock cylinder
    m.cyl([w / 2 - 6, -d / 2 - 0.6, h - 4 * K], 1.2 * K, 0.8, "Chrome", axis="y", sections=10)
    return m


def file_bank(n=3):
    """n tall cabinets side by side, with clutter on top."""
    m = Model()
    one = filing_cabinet(4)
    w = 38 * K
    h = 4 * 31 * K + 6 * K
    for i in range(n):
        x = (i - (n - 1) / 2) * (w + 0.6)
        for mat, meshes in one.parts.items():
            for mm in meshes:
                c = mm.copy(); c.apply_translation([x, 0, 0]); m.add(c, mat)
    # stuff on top: binder stack, box, plant
    m.box([-w * 1.2, -15 * K, h], [-w * 0.3, 15 * K, h + 4 * K], "PosterNavy")
    m.box([-w * 1.15, -14 * K, h + 4 * K], [-w * 0.35, 14 * K, h + 7.5 * K], "PosterTeal")
    m.box([w * 0.1, -18 * K, h], [w * 0.9, 18 * K, h + 22 * K], "CoatTan")  # archive box
    m.box([w * 0.1 - 0.3, -18 * K - 0.3, h + 19 * K], [w * 0.9 + 0.3, 18 * K + 0.3, h + 23 * K], "CoatTan")
    return m


def short_cabinet():
    return filing_cabinet(2)


def wastebasket():
    m = Model()
    r, h = 13 * K, 30 * K
    # tapered bin: slice a cone
    c = trimesh.creation.cylinder(radius=r, height=h, sections=20)
    v = c.vertices
    v[:, :2] *= np.where(v[:, 2:3] < 0, 0.8, 1.0)
    c.vertices = v
    c.apply_translation([0, 0, h / 2])
    m.add(c, "KickPlate")
    m.cyl([0, 0, h - 0.2], r - 1.2, 0.4, "BlackPlastic")  # dark opening
    for i in range(3):
        s = trimesh.creation.icosphere(subdivisions=1, radius=4.5 * K)
        s.vertices *= 1 + 0.25 * np.array([[rng.random() - .5 for _ in range(3)] for _ in s.vertices])
        s.apply_translation([rng.uniform(-5, 5) * K, rng.uniform(-5, 5) * K, h - 2 * K + i])
        m.add(s, "Paper")
    return m


def water_cooler():
    m = Model()
    w = 32 * K
    hb = 92 * K
    m.box([-w / 2, -w / 2, 0], [w / 2, w / 2, hb], "BeigePlastic")
    m.box([-w / 2 + 2, -w / 2 - 0.4, 4 * K], [w / 2 - 2, -w / 2, 50 * K], "CopierGray")  # cabinet door
    m.box([-w / 2 + 3, -w / 2 - 6 * K, hb - 40 * K], [w / 2 - 3, -w / 2, hb - 38 * K], "KickPlate")  # drip tray
    for sx, mat in ((-6 * K, "MemoBlue"), (6 * K, "Mug")):
        m.box([sx - 1.5 * K, -w / 2 - 4 * K, hb - 25 * K], [sx + 1.5 * K, -w / 2, hb - 20 * K], mat)  # taps
    # cup dispenser on the side
    m.cyl([w / 2 + 4 * K, 0, hb - 45 * K], 4 * K, 30 * K, "Chrome", sections=12)
    # 5-gallon bottle upside down
    m.cyl([0, 0, hb], 6 * K, 6 * K, "WaterJug", sections=20)
    m.cyl([0, 0, hb + 6 * K], 13.5 * K, 34 * K, "WaterJug", sections=24)
    m.cyl([0, 0, hb + 14 * K], 13.8 * K, 1.5 * K, "WaterJug", sections=24)
    m.cyl([0, 0, hb + 28 * K], 13.8 * K, 1.5 * K, "WaterJug", sections=24)
    return m


def ficus():
    m = Model()
    m.cyl([0, 0, 0], 18 * K, 34 * K, "Terracotta", sections=24)
    m.cyl([0, 0, 30 * K], 20 * K, 5 * K, "Terracotta", sections=24)
    m.cyl([0, 0, 34 * K], 17 * K, 0.6, "Soil", sections=24)
    # three braided trunks
    for i in range(3):
        a = i * 120
        rot_box(m, [math.cos(math.radians(a)) * 2 * K, math.sin(math.radians(a)) * 2 * K, 34 * K + 55 * K],
                [2 * K, 2 * K, 110 * K], "WoodFrame", pitch=rng.uniform(-5, 5), roll=rng.uniform(-5, 5))
    # leaf clusters
    for i in range(340):
        u = rng.random(); t = rng.uniform(0, 2 * math.pi)
        z = 34 * K + (75 + 95 * u) * K
        rad = (38 - abs(u - 0.45) * 50) * K * math.sqrt(rng.random())
        mat = "Leaf" if rng.random() < 0.6 else "LeafDark"
        rot_box(m, [math.cos(t) * rad, math.sin(t) * rad, z], [9 * K, 4.6 * K, 0.4], mat,
                yaw=rng.uniform(0, 360), pitch=rng.uniform(-40, 40), roll=rng.uniform(-40, 40))
    return m


def snake_plant():
    m = Model()
    m.cyl([0, 0, 0], 14 * K, 30 * K, "BeigePlastic", sections=20)
    m.cyl([0, 0, 29.5 * K], 13 * K, 0.6, "Soil", sections=20)
    for i in range(16):
        t = rng.uniform(0, 2 * math.pi); r = rng.uniform(0, 9) * K
        h = rng.uniform(45, 80) * K
        rot_box(m, [math.cos(t) * r, math.sin(t) * r, 30 * K + h / 2], [5 * K, 0.6, h],
                "Leaf" if i % 2 else "LeafDark", yaw=rng.uniform(0, 180), pitch=rng.uniform(-10, 10), roll=rng.uniform(-10, 10))
    return m


def coat_rack():
    m = Model()
    h = 175 * K
    for i in range(3):
        a = math.radians(i * 120 + 90)
        rot_box(m, [math.cos(a) * 18 * K, math.sin(a) * 18 * K, 4 * K], [40 * K, 3 * K, 2.5 * K], "WoodFrame", yaw=math.degrees(a), pitch=0)
    m.cyl([0, 0, 0], 2.2 * K, h, "WoodFrame", sections=12)
    m.cyl([0, 0, h], 3.5 * K, 4 * K, "WoodFrame", sections=12)
    for i in range(6):
        a = math.radians(i * 60)
        rot_box(m, [math.cos(a) * 8 * K, math.sin(a) * 8 * K, h - 12 * K], [16 * K, 1.6 * K, 1.6 * K], "WoodFrame",
                yaw=math.degrees(a), pitch=-30)
    # trench coat hanging on one hook
    a = math.radians(300)
    cx, cy = math.cos(a) * 18 * K, math.sin(a) * 18 * K
    coat = trimesh.creation.box(extents=[38 * K, 14 * K, 105 * K])
    v = coat.vertices
    v[:, 0] *= np.where(v[:, 2:3].ravel() > 0, 0.75, 1.15)
    coat.vertices = v
    coat.apply_translation([cx, cy, h - 20 * K - 52 * K])
    m.add(coat, "CoatTan")
    rot_box(m, [cx, cy, h - 24 * K], [16 * K, 12 * K, 6 * K], "CoatTan")
    # fedora on the top
    m.cyl([0, 0, h + 4 * K], 15 * K, 1.2 * K, "KickPlate", sections=20)
    m.cyl([0, 0, h + 4 * K], 9 * K, 11 * K, "KickPlate", sections=20)
    return m


def copier():
    m = Model()
    w, d, h = 78 * K, 62 * K, 92 * K
    m.box([-w / 2, -d / 2, 6 * K], [w / 2, d / 2, h], "CopierGray")
    m.box([-w / 2 + 3, -d / 2 + 3, 0], [w / 2 - 3, d / 2 - 3, 6 * K], "KickPlate")
    for i in range(3):  # paper cassettes
        z = 10 * K + i * 14 * K
        m.box([-w / 2 + 4, -d / 2 - 0.8, z], [w / 2 - 4, -d / 2, z + 12 * K], "BeigePlastic")
        m.box([-8 * K, -d / 2 - 2.2, z + 8 * K], [8 * K, -d / 2 - 0.8, z + 10 * K], "KickPlate")
    m.box([-w / 2, -d / 2, h], [w / 2, d / 2, h + 5 * K], "BeigePlastic")  # lid
    m.box([-w / 2 + 2, -d / 2 - 12 * K, h - 8 * K], [-w / 2 + 34 * K, -d / 2, h - 2 * K], "BeigePlastic")  # control panel
    m.box([-w / 2 + 4, -d / 2 - 12.2 * K, h - 6 * K], [-w / 2 + 14 * K, -d / 2 - 12 * K, h - 3 * K], "GreenLight")
    m.box([-w / 2 + 18 * K, -d / 2 - 12.2 * K, h - 6 * K], [-w / 2 + 20 * K, -d / 2 - 12 * K, h - 4 * K], "RedLight")
    # output tray with copies
    m.box([w / 2, -d * 0.35, h - 30 * K], [w / 2 + 28 * K, d * 0.35, h - 28 * K], "BeigePlastic")
    m.box([w / 2 + 2, -d * 0.28, h - 28 * K], [w / 2 + 24 * K, d * 0.28, h - 25 * K], "Paper")
    # stack of paper reams beside
    m.box([-w / 2 + 6, -d / 2 + 6, h + 5 * K], [-w / 2 + 6 + 22 * K, -d / 2 + 6 + 28 * K, h + 11 * K], "Paper")
    return m


# ------------------------------------------------------------------ wall pieces (front = -Y, back plane at y=0)
def frame_rect(m, w, h, depth, mat):
    t = 2.5 * K
    m.box([-w / 2, -depth, -h / 2], [w / 2, 0, -h / 2 + t], mat)
    m.box([-w / 2, -depth, h / 2 - t], [w / 2, 0, h / 2], mat)
    m.box([-w / 2, -depth, -h / 2], [-w / 2 + t, 0, h / 2], mat)
    m.box([w / 2 - t, -depth, -h / 2], [w / 2, 0, h / 2], mat)


def poster(style):
    m = Model()
    w, h = 60 * K, 80 * K
    frame_rect(m, w, h, 2.5, "BlackPlastic" if style != 1 else "Chrome")
    iw, ih = w - 5 * K, h - 5 * K
    m.box([-iw / 2, -1.2, -ih / 2], [iw / 2, -0.4, ih / 2], "WallPaper")
    if style == 0:  # synthwave sunset stripes
        bands = ["PosterPurple", "PosterPink", "PosterOrange", "PosterYellow"]
        for i, b in enumerate(bands):
            z0 = -ih / 2 + 6 * K + i * 8 * K
            m.box([-iw / 2 + 4 * K, -1.6, z0], [iw / 2 - 4 * K, -1.2, z0 + 7 * K], b)
        m.cyl([0, -1.7, 10 * K], 15 * K, 0.5, "PosterOrange", axis="y", sections=32)
        m.box([-iw / 2 + 4 * K, -1.8, -ih / 2 + 3 * K], [iw / 2 - 4 * K, -1.6, -ih / 2 + 5 * K], "PosterNavy")
    elif style == 1:  # memphis shapes
        m.box([-iw / 2, -1.4, -ih / 2], [iw / 2, -1.2, ih / 2], "PosterNavy")
        for i in range(14):
            mat = rng.choice(["PosterPink", "PosterTeal", "PosterYellow", "PosterOrange"])
            x, z = rng.uniform(-iw / 2 + 6, iw / 2 - 6), rng.uniform(-ih / 2 + 6, ih / 2 - 6)
            if i % 3 == 0:
                m.cyl([x, -1.8, z], rng.uniform(2, 5) * K, 0.4, mat, axis="y", sections=16)
            else:
                rot_box(m, [x, -1.6, z], [rng.uniform(4, 12) * K, 0.4, rng.uniform(1, 3) * K], mat, pitch=rng.uniform(-60, 60))
    else:  # corporate "teamwork" poster: photo + caption bars
        m.box([-iw / 2, -1.4, -ih / 2], [iw / 2, -1.2, ih / 2], "PosterNavy")
        m.box([-iw / 2 + 4 * K, -1.6, -ih / 2 + 22 * K], [iw / 2 - 4 * K, -1.4, ih / 2 - 4 * K], "PhotoSky")
        m.box([-iw / 2 + 4 * K, -1.8, -ih / 2 + 22 * K], [iw / 2 - 4 * K, -1.6, -ih / 2 + 32 * K], "PhotoGrass")
        m.box([-14 * K, -1.6, -ih / 2 + 13 * K], [14 * K, -1.4, -ih / 2 + 17 * K], "WallPaper")
        m.box([-20 * K, -1.6, -ih / 2 + 7 * K], [20 * K, -1.4, -ih / 2 + 9 * K], "WallPaper")
    return m


def wall_clock():
    m = Model()
    r = 17 * K
    m.cyl([0, -4 * K, 0], r, 4 * K, "BlackPlastic", axis="y", sections=36)
    m.cyl([0, -4 * K - 0.4, 0], r - 1.5 * K, 0.4, "ClockFace", axis="y", sections=36)
    for i in range(12):
        a = math.radians(i * 30)
        L = 3 * K if i % 3 == 0 else 1.5 * K
        rot_box(m, [math.sin(a) * (r - 4 * K), -4.6 * K, math.cos(a) * (r - 4 * K)], [0.8 * K, 0.3, L], "KickPlate", pitch=-math.degrees(a))
    for ang, ln, wd in ((300, 8 * K, 1.2 * K), (60, 12 * K, 0.8 * K)):  # 10:10
        a = math.radians(ang)
        rot_box(m, [math.sin(a) * ln / 2, -4.8 * K, math.cos(a) * ln / 2], [wd, 0.3, ln], "KickPlate", pitch=-ang)
    rot_box(m, [0, -5 * K, -5 * K], [0.3 * K, 0.2, 12 * K], "RedLight", pitch=12)
    return m


def bulletin_board():
    m = Model()
    w, h = 120 * K, 80 * K
    frame_rect(m, w, h, 3, "WoodFrame")
    m.box([-w / 2 + 2, -2, -h / 2 + 2], [w / 2 - 2, -0.5, h / 2 - 2], "Cork")
    pin_papers(m, w - 12 * K, h - 12 * K, 9, y0=-2)
    return m


def pin_papers(m, W, H, n, y0=0.0):
    placed = []
    for i in range(n * 4):
        if len(placed) >= n:
            break
        kind = rng.random()
        if kind < 0.55:
            pw, ph, mat = 21.6 * K * 0.55, 27.9 * K * 0.55, "Paper"
        elif kind < 0.85:
            pw = ph = 7.6 * K; mat = rng.choice(["MemoYellow", "MemoPink", "MemoBlue"])
        else:
            pw, ph, mat = 15 * K, 10 * K, "PhotoSky"
        x, z = rng.uniform(-W / 2 + pw / 2, W / 2 - pw / 2), rng.uniform(-H / 2 + ph / 2, H / 2 - ph / 2)
        if any(abs(x - a) < (pw + b) / 2.3 and abs(z - c) < (ph + d) / 2.3 for a, c, b, d in placed):
            continue
        placed.append((x, z, pw, ph))
        dy = y0 - 0.3 - 0.15 * len(placed)
        rot_box(m, [x, dy, z], [pw, 0.15, ph], mat, pitch=rng.uniform(-6, 6))
        if mat == "PhotoSky":
            m.box([x - pw / 2 + 1, dy - 0.2, z - ph / 2 + 1], [x + pw / 2 - 1, dy - 0.1, z - ph * 0.1], "PhotoGrass")
        m.cyl([x, dy - 0.1 - 0.8 * K, z + ph / 2 - 1.5 * K], 0.6 * K, 0.8 * K, rng.choice(["RedLight", "PosterYellow", "MemoBlue"]), axis="y", sections=8)


def calendar():
    m = Model()
    w, h = 28 * K, 43 * K
    m.box([-w / 2, -0.6, -h / 2], [w / 2, -0.2, h / 2], "WallPaper")
    m.box([-w / 2 + 1, -0.8, 1 * K], [w / 2 - 1, -0.6, h / 2 - 1], "PhotoSky")      # picture half
    m.box([-w / 2 + 1, -0.9, 1 * K], [w / 2 - 1, -0.8, 8 * K], "PhotoGrass")
    m.box([-w / 2 + 1, -0.8, -1.5 * K], [w / 2 - 1, -0.7, 0], "MemoPink")             # month bar
    gw, gh = (w - 2) / 7, (h / 2 - 3 * K) / 5
    for i in range(8):
        x = -w / 2 + 1 + i * gw
        m.box([x - 0.1, -0.75, -h / 2 + 1], [x + 0.1, -0.65, -1.6 * K], "KickPlate")
    for j in range(6):
        z = -h / 2 + 1 + j * gh
        m.box([-w / 2 + 1, -0.75, z - 0.1], [w / 2 - 1, -0.65, z + 0.1], "KickPlate")
    m.cyl([0, -0.9 - 0.8 * K, h / 2 - 1.5 * K], 0.6 * K, 0.8 * K, "RedLight", axis="y", sections=8)
    return m


def cubicle_pinup(variant):
    """Papers pinned on the cubicle fabric above a desk."""
    m = Model()
    rngl = random.Random(variant * 31 + 7)
    global rng
    old, rng = rng, rngl
    pin_papers(m, 110 * K, 55 * K, 5 + variant % 3)
    if variant % 2 == 0:
        c = calendar()
        for mat, meshes in c.parts.items():
            for mm in meshes:
                cc = mm.copy(); cc.apply_translation([(-1 if variant % 4 == 0 else 1) * 62 * K, -0.1, 0]); m.add(cc, mat)
    rng = old
    return m


def ceiling_light():
    """2x4 fluorescent troffer, pivot at its top (ceiling contact)."""
    m = Model()
    w, l, d = 61 * K, 122 * K, 8 * K
    m.box([-l / 2, -w / 2, -d], [l / 2, w / 2, 0], "FixtureWhite")
    m.box([-l / 2 + 3, -w / 2 + 3, -d - 0.4], [l / 2 - 3, w / 2 - 3, -d + 0.1], "FluoroPanel")
    for i in range(1, 4):  # louver lines
        y = -w / 2 + i * w / 4
        m.box([-l / 2 + 3, y - 0.4, -d - 0.8], [l / 2 - 3, y + 0.4, -d], "FixtureWhite")
    return m


if __name__ == "__main__":
    OUT = sys.argv[1] if len(sys.argv) > 1 else "out_life"
    os.makedirs(OUT, exist_ok=True)
    models = {
        "SM_80s_FileBank": file_bank(3),
        "SM_80s_FileCabinet4": filing_cabinet(4),
        "SM_80s_FileCabinet2": short_cabinet(),
        "SM_80s_Wastebasket": wastebasket(),
        "SM_80s_WaterCooler": water_cooler(),
        "SM_80s_Ficus": ficus(),
        "SM_80s_SnakePlant": snake_plant(),
        "SM_80s_CoatRack": coat_rack(),
        "SM_80s_Copier": copier(),
        "SM_80s_Poster_Sunset": poster(0),
        "SM_80s_Poster_Memphis": poster(1),
        "SM_80s_Poster_Teamwork": poster(2),
        "SM_80s_WallClock": wall_clock(),
        "SM_80s_BulletinBoard": bulletin_board(),
        "SM_80s_CubiclePinup_A": cubicle_pinup(0),
        "SM_80s_CubiclePinup_B": cubicle_pinup(1),
        "SM_80s_CubiclePinup_C": cubicle_pinup(2),
        "SM_80s_CeilingLight": ceiling_light(),
    }
    rep = {}
    for n, mdl in models.items():
        rep[n] = write_glb(mdl, f"{OUT}/{n}.glb", n)
        mn, mx = mdl.bounds()
        rep[n]["min"] = [round(x, 1) for x in mn]; rep[n]["max"] = [round(x, 1) for x in mx]
    json.dump(rep, open(f"{OUT}/sizes.json", "w"), indent=1)
    for n, r in rep.items():
        print(n, r["min"], r["max"], r["tris"])
