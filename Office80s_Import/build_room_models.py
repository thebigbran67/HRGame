"""Third batch: themed rooms (reception, boss office, janitor closet, break room, conference room)
and cubicle alternatives. Same conventions: cm, front = -Y, pivot bottom center; wall pieces have
their back plane at y=0 and are vertically centered."""
import math, os, sys, json, random
import numpy as np
import trimesh
from build_models import Model, MATS, write_glb
import build_life_models as L
import build_models as B
from build_life_models import K, rot_box, frame_rect

MATS.update({
    "Walnut":       ("#4A2E1A", 0.0, 0.40, None),
    "WalnutLight":  ("#6B4426", 0.0, 0.45, None),
    "Brass":        ("#B48A3C", 1.0, 0.30, None),
    "Oxblood":      ("#5A1A16", 0.0, 0.35, None),
    "VinylOrange":  ("#B5541E", 0.0, 0.40, None),
    "GreenLeather": ("#1F4A33", 0.0, 0.40, None),
    "RugRed":       ("#7A1E1E", 0.0, 0.95, None),
    "RugCream":     ("#D9C9A3", 0.0, 0.95, None),
    "RugNavy":      ("#24304F", 0.0, 0.95, None),
    "RugBrown":     ("#6A4A2E", 0.0, 0.95, None),
    "RugRust":      ("#9A4A22", 0.0, 0.95, None),
    "Cardboard":    ("#B08A5A", 0.0, 0.90, None),
    "SafetyYellow": ("#E8C21C", 0.0, 0.50, None),
    "MopGray":      ("#BEB8A8", 0.0, 0.95, None),
    "SteelGray":    ("#7F8287", 0.6, 0.45, None),
    "Porcelain":    ("#E9E7E0", 0.0, 0.15, None),
    "Glass":        ("#2A3438", 0.0, 0.05, None),
    "Whiteboard":   ("#F3F4F1", 0.0, 0.10, None),
    "MarkerBlue":   ("#2448A8", 0.0, 0.40, None),
    "MarkerRed":    ("#B42424", 0.0, 0.40, None),
    "FridgeAlmond": ("#E3D9C2", 0.0, 0.30, None),
    "VendRed":      ("#8E1B1B", 0.0, 0.35, None),
    "SnackA":       ("#D4A017", 0.0, 0.50, None),
    "SnackB":       ("#2F6DB5", 0.0, 0.50, None),
    "SnackC":       ("#C2412D", 0.0, 0.50, None),
    "VendGlow":     ("#E8EEF0", 0.0, 0.20, [1.2, 1.25, 1.3]),
    "Globe":        ("#3D6E8A", 0.0, 0.35, None),
    "GlobeLand":    ("#B79A5B", 0.0, 0.40, None),
    "Laminate2":    ("#C9B28A", 0.0, 0.35, None),
    "Formica":      ("#D8CDB0", 0.0, 0.30, None),
    "PaintingSky":  ("#8C7A5A", 0.0, 0.60, None),
    "PaintingLand": ("#4C5A2E", 0.0, 0.60, None),
    "PaintingSun":  ("#D9A441", 0.0, 0.60, None),
})
rng = random.Random(42)


def copy_into(dst, src, offset=(0, 0, 0), yaw=0.0):
    T = trimesh.transformations.rotation_matrix(math.radians(yaw), [0, 0, 1])
    T[:3, 3] = offset
    for mat, meshes in src.parts.items():
        for mm in meshes:
            c = mm.copy(); c.apply_transform(T); dst.add(c, mat)


# ------------------------------------------------------------------ cubicle alternatives
def round_table():
    m = Model()
    r, h = 54 * K, 74 * K
    m.cyl([0, 0, h - 3 * K], r, 3 * K, "Laminate2", sections=36)
    m.cyl([0, 0, h - 3.6 * K], r + 0.6, 0.8 * K, "VinylTrim", sections=36)
    m.cyl([0, 0, 2 * K], 4 * K, h - 5 * K, "KickPlate", sections=16)
    for i in range(4):
        rot_box(m, [math.cos(i * math.pi / 2) * 18 * K, math.sin(i * math.pi / 2) * 18 * K, 1.5 * K], [40 * K, 5 * K, 3 * K], "KickPlate", yaw=i * 90)
    # a few things on it
    B.papers(m, h, 8, -6, k=K, n=3, yaw=20)
    B.mug(m, h, -22, 14, k=K)
    m.box([18, 20, h], [18 + 22 * K, 20 + 15 * K, h + 1.5 * K], "PosterNavy")  # notepad
    return m


def archive_box(m, x, y, z, yaw=0, lid=True):
    w, d, h = 39 * K, 31 * K, 26 * K
    rot_box(m, [x, y, z + h / 2], [w, d, h], "Cardboard", yaw=yaw)
    if lid:
        rot_box(m, [x, y, z + h - 2 * K], [w + 1, d + 1, 4 * K], "Cardboard", yaw=yaw)
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    rot_box(m, [x - s * (-d / 2 - 0.3), y + c * (-d / 2 - 0.3), z + h * 0.55], [10 * K, 0.4, 6 * K], "Paper", yaw=yaw)


def box_stack():
    m = Model()
    h = 26 * K
    for col, (x, y, n) in enumerate(((-24 * K, 0, 3), (24 * K, 2, 2), (0, -38 * K, 1))):
        for i in range(n):
            archive_box(m, x + rng.uniform(-2, 2), y + rng.uniform(-2, 2), i * h, yaw=rng.uniform(-6, 6))
    return m


def coffee_station():
    m = Model()
    w, d, h = 100 * K, 55 * K, 80 * K
    m.box([-w / 2, -d / 2 + 2, 0], [w / 2, d / 2, 6 * K], "KickPlate")
    m.box([-w / 2, -d / 2 + 2, 6 * K], [w / 2, d / 2, h - 3 * K], "WalnutLight")
    for sx in (-1, 1):
        m.box([sx * w / 4 - w / 4 + 1 if sx < 0 else 1, -d / 2, 8 * K], [sx * w / 4 + w / 4 - 1 if sx > 0 else -1, -d / 2 + 2, h - 5 * K], "Walnut")
        m.box([sx * 4 * K - 1.5 * K, -d / 2 - 1.2, h - 22 * K], [sx * 4 * K + 1.5 * K, -d / 2, h - 12 * K], "Brass")
    m.box([-w / 2 - 1, -d / 2 - 1, h - 3 * K], [w / 2 + 1, d / 2 + 1, h], "Formica")
    t = h
    # drip coffee maker
    m.box([-30 * K, -2 * K, t], [-10 * K, 14 * K, t + 34 * K], "BlackPlastic")
    m.box([-30 * K, -10 * K, t + 26 * K], [-10 * K, 14 * K, t + 34 * K], "BlackPlastic")
    m.cyl([-20 * K, -5 * K, t + 2 * K], 6.5 * K, 13 * K, "Glass", sections=18)
    m.cyl([-20 * K, -5 * K, t + 4 * K], 6.2 * K, 5 * K, "Walnut", sections=18)  # coffee inside
    m.box([-30 * K, -10 * K, t], [-10 * K, 14 * K, t + 2 * K], "BlackPlastic")
    # mugs, sugar, cups
    for i, mat in enumerate(("Mug", "BeigePlastic", "PosterTeal", "WallPaper")):
        B.mug(m, t, 6 * K + i * 9 * K, -12 * K, k=K * 0.8)
    m.cyl([30 * K, 12 * K, t], 5 * K, 12 * K, "Glass", sections=14)
    m.cyl([30 * K, 12 * K, t + 12 * K], 5.2 * K, 1.5 * K, "Chrome", sections=14)
    m.cyl([16 * K, 14 * K, t], 3.5 * K, 22 * K, "WallPaper", sections=14)  # cup stack
    m.box([-44 * K, -18 * K, t], [-36 * K, -6 * K, t + 4 * K], "PosterPink")  # sweetener box
    return m


# ------------------------------------------------------------------ reception
def reception_counter(Lx=1218.0, Dy=513.0, top=148.0):
    """U-shaped counter filling an Lx x Dy footprint. Visitors stand on -Y; open toward +Y."""
    m = Model()
    hl, hd = Lx / 2, Dy / 2
    t = 45.0  # counter body depth
    def wood_run(x0, y0, x1, y1, axis):
        m.box([x0, y0, 8], [x1, y1, top - 6], "Walnut")
        m.box([x0 + 2, y0 + 2, 0], [x1 - 2, y1 - 2, 8], "KickPlate")
        # vertical slats on the visitor face
        if axis == "x":
            n = int((x1 - x0) / 22)
            for i in range(n):
                xx = x0 + 11 + i * 22
                m.box([xx - 3, y0 - 1.2, 10], [xx + 3, y0, top - 10], "WalnutLight")
        else:
            n = int((y1 - y0) / 22)
            for i in range(n):
                yy = y0 + 11 + i * 22
                face = x0 - 1.2 if x0 < 0 else x1
                m.box([face, yy - 3, 10], [face + 1.2, yy + 3, top - 10], "WalnutLight")
    wood_run(-hl, -hd, hl, -hd + t, "x")
    wood_run(-hl, -hd + t, -hl + t, hd, "y")
    wood_run(hl - t, -hd + t, hl, hd, "y")
    # transaction ledge with brass edge
    m.box([-hl - 8, -hd - 14, top - 6], [hl + 8, -hd + t, top], "Formica")
    m.box([-hl - 8, -hd - 14.5, top - 7], [hl + 8, -hd - 13, top + 0.5], "Brass")
    for x0, x1 in ((-hl - 8, -hl + t), (hl - t, hl + 8)):
        m.box([x0, -hd - 14, top - 6], [x1, hd, top], "Formica")
    # inner work surface at desk height
    ws = 99.0
    m.box([-hl + t, -hd + t, ws - 4], [hl - t, -hd + t + 75, ws], "Laminate2")
    m.box([-hl + t, -hd + t, 0], [-hl + t + 46, -hd + t + 75, ws - 4], "DeskSteel")
    m.box([hl - t - 46, -hd + t, 0], [hl - t, -hd + t + 75, ws - 4], "DeskSteel")
    # receptionist gear on the work surface (they face -Y, toward visitors)
    def at(x, y, mdl_fn):
        tmp = Model(); mdl_fn(tmp); copy_into(m, tmp, (x, y, 0), 180)
    at(-120, -hd + t + 40, lambda mm: (L_crt(mm, ws), B.keyboard(mm, ws, x=-30, y=-34, k=K)))
    at(80, -hd + t + 38, lambda mm: B.desk_phone(mm, ws, 0, 0, k=K))
    at(260, -hd + t + 38, lambda mm: B.rolodex(mm, ws, 0, 0, k=K))
    at(-300, -hd + t + 35, lambda mm: B.in_tray(mm, ws, 0, 0, k=K))
    B.papers(m, ws, 420, -hd + t + 35, k=K, n=5, yaw=10)
    # on the ledge: bell, nameplate, sign-in clipboard, pen cup, small plant
    m.cyl([-60, -hd - 2, top], 6 * K, 1 * K, "Brass", sections=16)
    s = trimesh.creation.icosphere(subdivisions=2, radius=4 * K); s.vertices[:, 2] = np.maximum(s.vertices[:, 2], 0)
    s.apply_translation([-60, -hd - 2, top + 1 * K]); m.add(s, "Brass")
    rot_box(m, [60, -hd - 6, top + 4 * K], [26 * K, 2 * K, 7 * K], "Walnut", pitch=0, roll=-20)
    m.box([60 - 10 * K, -hd - 6 - 1.5 * K, top + 2.5 * K], [60 + 10 * K, -hd - 6 - 1.2 * K, top + 5.5 * K], "Brass")
    m.box([200, -hd - 10, top], [200 + 23 * K, -hd - 10 + 31 * K, top + 1 * K], "WoodFrame")
    m.box([200 + 1, -hd - 8, top + 1 * K], [200 + 23 * K - 1, -hd - 12 + 31 * K, top + 1.3 * K], "Paper")
    m.cyl([300, -hd - 2, top], 4 * K, 11 * K, "BlackPlastic", sections=12)
    for i in range(4):
        rot_box(m, [300 + rng.uniform(-2, 2), -hd - 2 + rng.uniform(-2, 2), top + 14 * K], [0.8 * K, 0.8 * K, 12 * K], rng.choice(["MarkerBlue", "MarkerRed", "KickPlate"]), pitch=rng.uniform(-12, 12), roll=rng.uniform(-12, 12))
    sp = L.snake_plant(); copy_into(m, _scaled(sp, 0.45), (-hl + 40, -hd + 10, top))
    return m


def L_crt(mm, ws):
    B.crt_terminal(mm, ws, x=-30, y=10, k=K)


def _scaled(model, s):
    out = Model()
    for mat, meshes in model.parts.items():
        for mm in meshes:
            c = mm.copy(); c.apply_scale(s); out.add(c, mat)
    return out


def waiting_chairs(n=3):
    m = Model()
    seat_w = 56 * K
    total = n * seat_w + (n + 1) * 6 * K
    x0 = -total / 2
    sh = 44 * K
    # chrome beam + legs
    m.box([x0, -4 * K, sh - 14 * K], [-x0, 4 * K, sh - 10 * K], "Chrome")
    for sx in (x0 + 10 * K, -x0 - 10 * K):
        for sy in (-18 * K, 18 * K):
            m.box([sx - 1.5 * K, sy - 1.5 * K, 0], [sx + 1.5 * K, sy + 1.5 * K, sh - 10 * K], "Chrome")
        m.box([sx - 1.5 * K, -20 * K, 0], [sx + 1.5 * K, 20 * K, 2 * K], "Chrome")
    for i in range(n + 1):  # arms
        ax = x0 + i * (seat_w + 6 * K) + 3 * K
        m.box([ax - 3 * K, -22 * K, sh + 18 * K], [ax + 3 * K, 18 * K, sh + 21 * K], "Walnut")
        m.box([ax - 1 * K, -18 * K, sh - 10 * K], [ax + 1 * K, -14 * K, sh + 18 * K], "Chrome")
    for i in range(n):
        cx = x0 + 6 * K + seat_w / 2 + i * (seat_w + 6 * K)
        m.box([cx - seat_w / 2, -24 * K, sh - 8 * K], [cx + seat_w / 2, 22 * K, sh], "VinylOrange")
        rot_box(m, [cx, 26 * K, sh + 24 * K], [seat_w, 8 * K, 44 * K], "VinylOrange", roll=-8)
        m.box([cx - 1.5 * K, 22 * K, sh - 8 * K], [cx + 1.5 * K, 26 * K, sh + 10 * K], "Chrome")
    return m


def coffee_table_magazines():
    m = Model()
    w, d, h = 110 * K, 55 * K, 42 * K
    m.box([-w / 2, -d / 2, h - 4 * K], [w / 2, d / 2, h], "Walnut")
    m.box([-w / 2 + 3, -d / 2 + 3, 6 * K], [w / 2 - 3, d / 2 - 3, 8 * K], "Walnut")  # lower shelf
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box([sx * (w / 2 - 4 * K) - 2 * K, sy * (d / 2 - 4 * K) - 2 * K, 0], [sx * (w / 2 - 4 * K) + 2 * K, sy * (d / 2 - 4 * K) + 2 * K, h - 4 * K], "Walnut")
    cols = ["PosterPink", "PosterTeal", "PosterYellow", "PosterNavy", "PhotoSky", "PosterOrange"]
    for i in range(6):
        rot_box(m, [rng.uniform(-w / 3, w / 3), rng.uniform(-d / 4, d / 4), h + 0.35 + i * 0.5], [21 * K, 28 * K, 0.5], cols[i], yaw=rng.uniform(-40, 40))
    for i in range(4):
        rot_box(m, [rng.uniform(-w / 3, w / 3), 0, 8 * K + 0.5 + i * 0.6], [21 * K, 28 * K, 0.6], cols[(i + 2) % 6], yaw=rng.uniform(-20, 20))
    m.cyl([w / 3, d / 5, h], 7 * K, 3 * K, "Glass", sections=20)  # glass ashtray
    return m


def logo_sign():
    """Walnut panel with a brass abstract corporate mark. Wall piece."""
    m = Model()
    w, h = 220 * K, 90 * K
    m.box([-w / 2, -3, -h / 2], [w / 2, 0, h / 2], "Walnut")
    m.cyl([-w / 2 + 50 * K, -3.8, 0], 28 * K, 0.8, "Brass", axis="y", sections=40)
    m.cyl([-w / 2 + 50 * K, -4.4, 0], 20 * K, 0.6, "Walnut", axis="y", sections=40)
    for i in range(3):
        m.box([-w / 2 + 34 * K + i * 12 * K, -5, -24 * K], [-w / 2 + 40 * K + i * 12 * K, -3, 24 * K], "Brass")
    # wordmark stand-in: bars of "letters" (no actual text)
    x = -w / 2 + 92 * K
    for i in range(7):
        bw = rng.choice([8, 10, 12]) * K
        m.box([x, -4.5, -6 * K], [x + bw, -3, 12 * K], "Brass")
        x += bw + 4 * K
    m.box([-w / 2 + 92 * K, -4.5, -16 * K], [x - 4 * K, -3, -13 * K], "Brass")
    return m


# ------------------------------------------------------------------ boss office
def exec_desk():
    m = Model()
    W, D, H = 200 * K, 100 * K, 76 * K
    hw, hd = W / 2, D / 2
    m.box([-hw - 3, -hd - 3, H - 5 * K], [hw + 3, hd + 3, H], "Walnut")
    m.box([-hw + 12 * K, -hd + 10 * K, H], [hw - 12 * K, hd - 10 * K, H + 0.3], "GreenLeather")
    for sx in (-1, 1):
        x0, x1 = sorted([sx * hw, sx * (hw - 55 * K)])
        m.box([x0, -hd, 6 * K], [x1, hd, H - 5 * K], "Walnut")
        m.box([x0 + 1, -hd + 1, 0], [x1 - 1, hd - 1, 6 * K], "KickPlate")
        for i in range(3):
            z0 = 9 * K + i * 19 * K
            m.box([x0 + 2, -hd - 1.2, z0], [x1 - 2, -hd, z0 + 17 * K], "WalnutLight")
            m.box([(x0 + x1) / 2 - 7 * K, -hd - 2.5, z0 + 12 * K], [(x0 + x1) / 2 + 7 * K, -hd - 1.2, z0 + 13.5 * K], "Brass")
    m.box([-hw + 55 * K, hd - 4 * K, 18 * K], [hw - 55 * K, hd, H - 5 * K], "Walnut")  # modesty panel (visitor side)
    for i in range(12):  # fluted visitor face
        x = -hw + 58 * K + i * ((W - 116 * K) / 11)
        m.box([x - 2, hd, 20 * K], [x + 2, hd + 1.2, H - 7 * K], "WalnutLight")
    # banker's lamp
    m.box([-hw + 20 * K, 0, H], [-hw + 34 * K, 10 * K, H + 2 * K], "Brass")
    m.cyl([-hw + 27 * K, 5 * K, H + 2 * K], 1 * K, 30 * K, "Brass", sections=10)
    c = trimesh.creation.cylinder(radius=6 * K, height=32 * K, sections=16)
    c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    c.apply_scale([1, 1, 0.6]); c.apply_translation([-hw + 27 * K, 0, H + 34 * K]); m.add(c, "GreenLeather")
    # pen set, phone, papers, cigar box, nameplate facing visitors (+Y)
    m.box([-12 * K, 20 * K, H], [12 * K, 30 * K, H + 3 * K], "Walnut")
    for sx in (-6, 6):
        rot_box(m, [sx * K, 25 * K, H + 10 * K], [1 * K, 1 * K, 14 * K], "Brass", roll=sx * 3)
    B.desk_phone(m, H, hw - 38 * K, -10 * K, k=K)
    B.papers(m, H, 10 * K, -15 * K, k=K, n=3, yaw=-8)
    m.box([hw - 75 * K, 15 * K, H], [hw - 55 * K, 28 * K, H + 6 * K], "WoodFrame")
    rot_box(m, [0, hd - 6 * K, H + 4 * K], [34 * K, 2 * K, 7 * K], "Walnut", roll=20)
    m.box([-14 * K, hd - 6 * K + 1.2 * K, H + 2 * K], [14 * K, hd - 6 * K + 1.6 * K, H + 6 * K], "Brass")
    return m


def exec_chair():
    m = Model()
    for i in range(5):
        a = i * 72
        rot_box(m, [math.cos(math.radians(a)) * 16 * K, math.sin(math.radians(a)) * 16 * K, 6 * K], [32 * K, 4 * K, 3 * K], "Chrome", yaw=a)
        m.cyl([math.cos(math.radians(a)) * 30 * K, math.sin(math.radians(a)) * 30 * K, 0], 2.6 * K, 4.5 * K, "BlackPlastic", sections=10)
    m.cyl([0, 0, 4 * K], 3.5 * K, 36 * K, "Chrome", sections=14)
    m.box([-30 * K, -28 * K, 40 * K], [30 * K, 26 * K, 52 * K], "Oxblood")
    m.box([-28 * K, 22 * K, 50 * K], [28 * K, 34 * K, 125 * K], "Oxblood")
    for r_ in range(4):  # tufting lines
        m.box([-26 * K, 21.6 * K, (62 + r_ * 15) * K], [26 * K, 22 * K, (62.6 + r_ * 15) * K], "BlackPlastic")
    for sx in (-1, 1):
        m.box([sx * 30 * K - 5 * K, -20 * K, 52 * K], [sx * 30 * K + 5 * K, 30 * K, 70 * K], "Oxblood")
    return m


def guest_chair():
    m = Model()
    w, d, sh = 58 * K, 56 * K, 45 * K
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box([sx * (w / 2 - 3 * K) - 2 * K, sy * (d / 2 - 3 * K) - 2 * K, 0], [sx * (w / 2 - 3 * K) + 2 * K, sy * (d / 2 - 3 * K) + 2 * K, sh], "Walnut")
        m.box([sx * w / 2 - 3 * K, -d / 2, sh + 15 * K], [sx * w / 2 + 3 * K, d / 2, sh + 19 * K], "Walnut")
        m.box([sx * w / 2 - 2 * K, -d / 2 + 2 * K, sh], [sx * w / 2 + 2 * K, -d / 2 + 6 * K, sh + 15 * K], "Walnut")
    m.box([-w / 2 + 3 * K, -d / 2, sh - 4 * K], [w / 2 - 3 * K, d / 2, sh + 5 * K], "Oxblood")
    m.box([-w / 2 + 3 * K, d / 2 - 6 * K, sh + 5 * K], [w / 2 - 3 * K, d / 2, sh + 48 * K], "Oxblood")
    m.box([-w / 2, d / 2 - 3 * K, sh + 46 * K], [w / 2, d / 2 + 1, sh + 50 * K], "Walnut")
    return m


def bookshelf():
    m = Model()
    w, d, h = 120 * K, 35 * K, 200 * K
    m.box([-w / 2, d / 2 - 2, 0], [w / 2, d / 2, h], "Walnut")
    for sx in (-1, 1):
        m.box([sx * w / 2 - (3 if sx > 0 else 0), -d / 2, 0], [sx * w / 2 + (0 if sx > 0 else 3), d / 2, h], "Walnut")
    m.box([-w / 2, -d / 2, h - 4], [w / 2, d / 2, h], "Walnut")
    shelves = 5
    sp = (h - 12 * K) / shelves
    for i in range(shelves):
        z = 8 * K + i * sp
        m.box([-w / 2 + 3, -d / 2, z - 3], [w / 2 - 3, d / 2 - 2, z], "Walnut")
        x = -w / 2 + 6
        while x < w / 2 - 12:
            if rng.random() < 0.12:
                x += rng.uniform(10, 25)  # gap / ornament
                if rng.random() < 0.5:
                    m.cyl([x - 6, 0, z], 4 * K, 14 * K, "Brass", sections=12)
                continue
            bw = rng.uniform(2.5, 5.5) * K
            bh = rng.uniform(0.62, 0.85) * sp
            bd = rng.uniform(0.6, 0.85) * d
            lean = rng.uniform(-6, 6) if rng.random() < 0.15 else 0
            rot_box(m, [x + bw / 2, d / 2 - 2 - bd / 2, z + bh / 2], [bw, bd, bh],
                    rng.choice(["Oxblood", "RugNavy", "GreenLeather", "WalnutLight", "MopGray", "PosterNavy", "CoatTan"]), pitch=lean)
            x += bw + 0.3
    m.box([-w / 2, -d / 2, 0], [w / 2, d / 2, 8 * K], "Walnut")
    return m


def credenza():
    m = Model()
    w, d, h = 180 * K, 50 * K, 75 * K
    m.box([-w / 2, -d / 2, 6 * K], [w / 2, d / 2, h], "Walnut")
    m.box([-w / 2 + 2, -d / 2 + 2, 0], [w / 2 - 2, d / 2 - 2, 6 * K], "KickPlate")
    for i in range(4):
        x0 = -w / 2 + 2 + i * (w - 4) / 4
        m.box([x0 + 1, -d / 2 - 1.2, 9 * K], [x0 + (w - 4) / 4 - 1, -d / 2, h - 4 * K], "WalnutLight")
        m.box([x0 + (w - 4) / 8 - 1 * K, -d / 2 - 2.5, h - 22 * K], [x0 + (w - 4) / 8 + 1 * K, -d / 2 - 1.2, h - 12 * K], "Brass")
    # decanter set on a tray, framed photo
    m.box([-w / 2 + 20 * K, -12 * K, h], [-w / 2 + 60 * K, 12 * K, h + 1.5 * K], "Brass")
    m.cyl([-w / 2 + 32 * K, 0, h + 1.5 * K], 6 * K, 18 * K, "Glass", sections=16)
    m.cyl([-w / 2 + 32 * K, 0, h + 1.5 * K], 5.6 * K, 9 * K, "PaintingSun", sections=16)
    m.cyl([-w / 2 + 32 * K, 0, h + 19.5 * K], 2 * K, 6 * K, "Glass", sections=10)
    for gx in (46, 54):
        m.cyl([-w / 2 + gx * K, -4 * K, h + 1.5 * K], 3 * K, 8 * K, "Glass", sections=12)
    rot_box(m, [w / 2 - 40 * K, 6 * K, h + 11 * K], [24 * K, 2 * K, 20 * K], "Brass", roll=12)
    rot_box(m, [w / 2 - 40 * K, 5 * K, h + 11 * K], [20 * K, 2.2 * K, 16 * K], "PhotoSky", roll=12)
    return m


def rug(colors, w=300, d=200):
    m = Model()
    w, d = w * K, d * K
    c0, c1, c2 = colors
    m.box([-w / 2, -d / 2, 0], [w / 2, d / 2, 0.6], c0)
    m.box([-w / 2 + 12 * K, -d / 2 + 12 * K, 0.6], [w / 2 - 12 * K, d / 2 - 12 * K, 0.8], c1)
    m.box([-w / 2 + 18 * K, -d / 2 + 18 * K, 0.8], [w / 2 - 18 * K, d / 2 - 18 * K, 1.0], c0)
    rot_box(m, [0, 0, 1.1], [d * 0.45, d * 0.45, 0.2], c2, yaw=45)
    rot_box(m, [0, 0, 1.2], [d * 0.25, d * 0.25, 0.2], c1, yaw=45)
    for sx in (-1, 1):
        for i in range(int(d / (4 * K))):
            m.box([sx * w / 2 - (0 if sx < 0 else -6 * K) - (6 * K if sx < 0 else 0), -d / 2 + i * 4 * K + 1, 0], [sx * w / 2 + (0 if sx < 0 else 6 * K), -d / 2 + i * 4 * K + 2.4, 0.3], "RugCream")
    return m


def painting():
    m = Model()
    w, h = 130 * K, 90 * K
    frame_rect(m, w, h, 6, "Brass")
    iw, ih = w - 6 * K, h - 6 * K
    m.box([-iw / 2, -2, -ih / 2], [iw / 2, -1, ih / 2], "PaintingSky")
    m.cyl([iw * 0.2, -2.3, ih * 0.15], 10 * K, 0.3, "PaintingSun", axis="y", sections=24)
    for i in range(5):
        rot_box(m, [rng.uniform(-iw / 2.5, iw / 2.5), -2.6 - i * 0.1, -ih / 2 + rng.uniform(10, 25) * K], [rng.uniform(40, 70) * K, 0.2, rng.uniform(15, 30) * K], "PaintingLand", pitch=rng.uniform(-25, 25))
    m.box([-iw / 2, -3.2, -ih / 2], [iw / 2, -3, -ih / 2 + 14 * K], "PaintingLand")
    m.box([-8 * K, -7, -h / 2 - 5 * K], [8 * K, -5, -h / 2 - 1 * K], "Brass")  # little plaque
    return m


def floor_globe():
    m = Model()
    for i in range(3):
        a = math.radians(i * 120)
        rot_box(m, [math.cos(a) * 14 * K, math.sin(a) * 14 * K, 30 * K], [3 * K, 3 * K, 62 * K], "Walnut", pitch=-14 * math.cos(a), roll=14 * math.sin(a))
    m.cyl([0, 0, 58 * K], 24 * K, 3 * K, "Walnut", sections=32)
    g = trimesh.creation.icosphere(subdivisions=3, radius=20 * K); g.apply_translation([0, 0, 82 * K]); m.add(g, "Globe")
    for i in range(6):  # continents
        b = trimesh.creation.icosphere(subdivisions=1, radius=rng.uniform(5, 9) * K)
        b.vertices *= [1, 1, 0.5]
        th, ph = rng.uniform(0, 2 * math.pi), rng.uniform(-0.9, 0.9)
        n = np.array([math.cos(ph) * math.cos(th), math.cos(ph) * math.sin(th), math.sin(ph)])
        R = trimesh.geometry.align_vectors([0, 0, 1], n)
        b.apply_transform(R); b.apply_translation(n * 18.6 * K + [0, 0, 82 * K]); m.add(b, "GlobeLand")
    c = trimesh.creation.annulus(r_min=21 * K, r_max=23 * K, height=1.5 * K, sections=40)
    c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    c.apply_translation([0, 0, 82 * K]); m.add(c, "Brass")
    return m


# ------------------------------------------------------------------ janitor closet
def metal_shelf():
    m = Model()
    w, d, h = 90 * K, 45 * K, 180 * K
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box([sx * w / 2 - (3 if sx > 0 else 0), sy * d / 2 - (3 if sy > 0 else 0), 0], [sx * w / 2 + (0 if sx > 0 else 3), sy * d / 2 + (0 if sy > 0 else 3), h], "SteelGray")
    levels = [8 * K, 50 * K, 95 * K, 140 * K, h - 2]
    for z in levels:
        m.box([-w / 2, -d / 2, z - 2], [w / 2, d / 2, z], "SteelGray")
    # supplies
    def bottle(x, y, z, mat, hh=24 * K, r=4.5 * K):
        m.cyl([x, y, z], r, hh, mat, sections=12)
        m.cyl([x, y, z + hh], r * 0.4, 4 * K, "BlackPlastic", sections=8)
    for i in range(5):
        bottle(-w / 2 + 10 * K + i * 11 * K, -6 * K, levels[2], rng.choice(["MemoBlue", "SafetyYellow", "PosterTeal", "WallPaper"]))
    for i in range(6):  # toilet paper rolls
        m.cyl([-w / 2 + 8 * K + (i % 3) * 13 * K, -d / 4 + (i // 3) * 13 * K, levels[1]], 6 * K, 11 * K, "WallPaper", sections=14)
    archive_box(m, w / 4, 0, levels[1])
    archive_box(m, -w / 5, 0, levels[3])
    archive_box(m, w / 4, 0, levels[0], lid=False)
    for i in range(3):  # paper towels
        m.cyl([w / 6 + i * 12 * K, 0, levels[2]], 6 * K, 26 * K, "Paper", sections=14)
    m.cyl([w / 4, 0, levels[3]], 14 * K, 30 * K, "SteelGray", sections=16)  # spare bucket
    for i in range(4):  # rags
        rot_box(m, [-w / 3, -d / 4 + i * 3, levels[0] + 2 + i * 2.5], [26 * K, 18 * K, 2.4], "MopGray", yaw=rng.uniform(-15, 15))
    return m


def mop_bucket():
    m = Model()
    w, d, h = 46 * K, 36 * K, 34 * K
    b = trimesh.creation.box(extents=[w, d, h])
    v = b.vertices; v[:, :2] *= np.where(v[:, 2:3] < 0, 0.85, 1.0); b.vertices = v
    b.apply_translation([0, 0, h / 2 + 5 * K]); m.add(b, "SafetyYellow")
    m.box([-w / 2 + 2, -d / 2 + 2, h + 4 * K], [w / 2 - 2, d / 2 - 2, h + 5.2 * K], "PhotoSky")  # dirty water
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cyl([sx * (w / 2 - 4 * K), sy * (d / 2 - 4 * K), 0], 2.5 * K, 5 * K, "BlackPlastic", sections=10)
    # wringer on one end
    m.box([w / 2 - 14 * K, -d / 2, h + 5 * K], [w / 2, d / 2, h + 24 * K], "SafetyYellow")
    rot_box(m, [w / 2 - 7 * K, 0, h + 42 * K], [3 * K, 3 * K, 40 * K], "SteelGray", pitch=-20)
    # mop leaning in the bucket
    rot_box(m, [-6 * K, 0, h + 50 * K], [2.5 * K, 2.5 * K, 140 * K], "WalnutLight", roll=12)
    for i in range(14):
        a = i / 14 * 2 * math.pi
        rot_box(m, [-6 * K + math.cos(a) * 4 * K, math.sin(a) * 4 * K - 3 * K, h - 2 * K], [2 * K, 2 * K, 30 * K], "MopGray", pitch=math.cos(a) * 25, roll=math.sin(a) * 25)
    return m


def broom_set():
    m = Model()
    # two brooms + dustpan leaning against the wall (+Y is the wall)
    for i, x in enumerate((-12 * K, 14 * K)):
        lean = 14
        top = [x, 22 * K, 150 * K]
        rot_box(m, [x, 22 * K - 75 * K * math.sin(math.radians(lean)), 75 * K + 6 * K], [2.6 * K, 2.6 * K, 150 * K], "WalnutLight", roll=-lean)
        rot_box(m, [x, 3 * K, 7 * K], [28 * K, 8 * K, 14 * K], "SafetyYellow" if i else "Cardboard", roll=-lean)
    rot_box(m, [34 * K, 20 * K, 30 * K], [28 * K, 2 * K, 28 * K], "MemoBlue", roll=-75)
    rot_box(m, [34 * K, 26 * K, 58 * K], [3 * K, 3 * K, 30 * K], "MemoBlue", roll=-15)
    return m


def wet_floor_sign():
    m = Model()
    w, h = 30 * K, 64 * K
    for s in (-1, 1):
        rot_box(m, [0, s * 9 * K, h / 2], [w, 1.2 * K, h], "SafetyYellow", roll=s * 16)
    m.box([-4 * K, -1.5 * K, h - 2 * K], [4 * K, 1.5 * K, h + 3 * K], "SafetyYellow")
    # generic hazard pictogram (triangle + figure) on both faces
    for s in (-1, 1):
        y = s * (9 * K + 1.0)
        rot_box(m, [0, y - s * 0.3 + s * 0.4, h * 0.6], [14 * K, 0.3, 2 * K], "KickPlate", roll=s * 16)
        rot_box(m, [-4 * K, y + s * 0.4, h * 0.6 + 5 * K], [2 * K, 0.3, 12 * K], "KickPlate", roll=s * 16, pitch=30)
        rot_box(m, [4 * K, y + s * 0.4, h * 0.6 + 5 * K], [2 * K, 0.3, 12 * K], "KickPlate", roll=s * 16, pitch=-30)
        rot_box(m, [0, y + s * 0.4, h * 0.3], [18 * K, 0.3, 3 * K], "KickPlate", roll=s * 16)
    return m


def utility_sink():
    m = Model()
    w, d, h = 70 * K, 55 * K, 30 * K
    m.box([-w / 2, -d / 2, 0], [w / 2, d / 2, h], "Porcelain")
    m.box([-w / 2 + 5 * K, -d / 2 + 5 * K, 8 * K], [w / 2 - 5 * K, d / 2 - 5 * K, h + 0.2], "SteelGray")
    m.box([-w / 2, d / 2 - 2, h], [w / 2, d / 2, h + 50 * K], "Porcelain")  # splash panel
    m.cyl([0, d / 2 - 24 * K, h + 30 * K], 1.8 * K, 22 * K, "Chrome", axis="y", sections=10)
    m.box([-1.5 * K, d / 2 - 22 * K, h + 18 * K], [1.5 * K, d / 2 - 18 * K, h + 32 * K], "Chrome")
    for sx in (-12, 12):
        m.cyl([sx * K, d / 2 - 6 * K, h + 36 * K], 2.5 * K, 3 * K, "RedLight" if sx < 0 else "MemoBlue", sections=8)
    rot_box(m, [w / 2 - 8 * K, -d / 4, h + 20 * K], [3 * K, 3 * K, 40 * K], "BlackPlastic", roll=20)  # hose
    return m


# ------------------------------------------------------------------ break room
def fridge():
    m = Model()
    w, d, h = 76 * K, 72 * K, 170 * K
    m.box([-w / 2, -d / 2 + 4, 0], [w / 2, d / 2, h], "FridgeAlmond")
    m.box([-w / 2 + 0.5, -d / 2, 8 * K], [w / 2 - 0.5, -d / 2 + 4, 108 * K], "FridgeAlmond")
    m.box([-w / 2 + 0.5, -d / 2, 110 * K], [w / 2 - 0.5, -d / 2 + 4, h - 2 * K], "FridgeAlmond")
    for z0, z1 in ((70 * K, 104 * K), (114 * K, 140 * K)):
        m.box([-w / 2 + 4 * K, -d / 2 - 4 * K, z0], [-w / 2 + 7 * K, -d / 2, z1], "Chrome")
    m.box([-w / 2, -d / 2, 0], [w / 2, -d / 2 + 4, 8 * K], "KickPlate")
    for i in range(5):  # magnets and notes
        rot_box(m, [rng.uniform(-w / 3, w / 3), -d / 2 - 0.4, rng.uniform(60, 100) * K], [rng.uniform(8, 14) * K, 0.3, rng.uniform(8, 18) * K], rng.choice(["Paper", "MemoYellow", "PhotoSky"]), pitch=rng.uniform(-8, 8))
    return m


def vending_machine():
    m = Model()
    w, d, h = 95 * K, 80 * K, 183 * K
    m.box([-w / 2, -d / 2, 0], [w / 2, d / 2, h], "VendRed")
    gx0, gx1 = -w / 2 + 6 * K, w / 2 - 28 * K
    m.box([gx0, -d / 2 - 0.5, 40 * K], [gx1, -d / 2, h - 12 * K], "VendGlow")
    rows = 6
    for r in range(rows):
        z = 44 * K + r * (h - 58 * K) / rows
        m.box([gx0 + 2, -d / 2 - 1.2, z], [gx1 - 2, -d / 2 - 0.5, z + 1 * K], "Chrome")
        for c in range(6):
            x = gx0 + 6 * K + c * ((gx1 - gx0 - 8 * K) / 6)
            m.box([x, -d / 2 - 1.0, z + 1 * K], [x + 7 * K, -d / 2 - 0.6, z + 11 * K], rng.choice(["SnackA", "SnackB", "SnackC", "PosterYellow"]))
    m.box([gx1 + 4 * K, -d / 2 - 1, 100 * K], [w / 2 - 4 * K, -d / 2, 150 * K], "BlackPlastic")  # keypad panel
    for r in range(4):
        for c in range(3):
            m.box([gx1 + 7 * K + c * 5 * K, -d / 2 - 1.8, 128 * K - r * 6 * K], [gx1 + 10 * K + c * 5 * K, -d / 2 - 1, 131 * K - r * 6 * K], "Chrome")
    m.box([gx1 + 8 * K, -d / 2 - 1.8, 136 * K], [w / 2 - 8 * K, -d / 2 - 1, 145 * K], "GreenLight")
    m.box([gx0, -d / 2 - 2, 12 * K], [gx1, -d / 2, 32 * K], "BlackPlastic")  # pickup bin
    m.box([-w / 2, -d / 2 - 0.6, h - 10 * K], [w / 2, -d / 2, h - 2 * K], "PosterYellow")  # header stripe
    return m


def kitchenette():
    m = Model()
    w, d, h = 240 * K, 62 * K, 90 * K
    m.box([-w / 2, -d / 2 + 4, 0], [w / 2, d / 2, 8 * K], "KickPlate")
    m.box([-w / 2, -d / 2 + 2, 8 * K], [w / 2, d / 2, h - 4 * K], "WalnutLight")
    n = 4
    for i in range(n):
        x0 = -w / 2 + i * w / n
        m.box([x0 + 1, -d / 2, 10 * K], [x0 + w / n - 1, -d / 2 + 2, h - 6 * K], "Walnut")
        m.box([x0 + w / n / 2 - 1 * K, -d / 2 - 1.2, h - 20 * K], [x0 + w / n / 2 + 1 * K, -d / 2, h - 12 * K], "Brass")
    m.box([-w / 2 - 1, -d / 2 - 2, h - 4 * K], [w / 2 + 1, d / 2, h], "Formica")
    m.box([-w / 2, d / 2 - 2, h], [w / 2, d / 2, h + 12 * K], "Formica")  # backsplash
    # sink
    m.box([-30 * K, -d / 4, h - 14 * K], [10 * K, d / 3, h + 0.2], "SteelGray")
    m.cyl([-10 * K, d / 2 - 8 * K, h], 1.8 * K, 26 * K, "Chrome", sections=10)
    rot_box(m, [-10 * K, d / 2 - 15 * K, h + 25 * K], [2.5 * K, 16 * K, 2.5 * K], "Chrome")
    # microwave (faux woodgrain 80s)
    mx = 60 * K
    m.box([mx - 26 * K, -d / 2 + 14 * K, h], [mx + 26 * K, d / 2 - 6 * K, h + 30 * K], "WalnutLight")
    m.box([mx - 24 * K, -d / 2 + 13.5 * K, h + 4 * K], [mx + 10 * K, -d / 2 + 14 * K, h + 26 * K], "Glass")
    m.box([mx + 12 * K, -d / 2 + 13.5 * K, h + 4 * K], [mx + 24 * K, -d / 2 + 14 * K, h + 26 * K], "Chrome")
    # coffee maker + mugs + paper towel
    cs = coffee_station()
    for mat, meshes in cs.parts.items():
        for mm in meshes:
            if mm.bounds[0][2] >= 80 * K - 0.5:
                c = mm.copy(); c.apply_translation([-85 * K, 0, h - 80 * K]); m.add(c, mat)
    m.cyl([105 * K, 10 * K, h], 1 * K, 30 * K, "Chrome", sections=8)
    m.cyl([105 * K, 10 * K, h + 2 * K], 6 * K, 26 * K, "Paper", sections=14)
    # upper cabinets
    m.box([-w / 2, d / 2 - 35 * K, h + 55 * K], [w / 2, d / 2, h + 125 * K], "WalnutLight")
    for i in range(n):
        x0 = -w / 2 + i * w / n
        m.box([x0 + 1, d / 2 - 36.2 * K, h + 57 * K], [x0 + w / n - 1, d / 2 - 35 * K, h + 123 * K], "Walnut")
    return m


def break_table():
    m = Model()
    w, d, h = 150 * K, 80 * K, 74 * K
    m.box([-w / 2, -d / 2, h - 3 * K], [w / 2, d / 2, h], "Formica")
    m.box([-w / 2 - 0.5, -d / 2 - 0.5, h - 3.4 * K], [w / 2 + 0.5, d / 2 + 0.5, h - 2.6 * K], "Chrome")
    for sx in (-1, 1):
        m.cyl([sx * (w / 2 - 25 * K), 0, 3 * K], 3 * K, h - 6 * K, "Chrome", sections=12)
        m.box([sx * (w / 2 - 25 * K) - 3 * K, -d / 2 + 8 * K, 0], [sx * (w / 2 - 25 * K) + 3 * K, d / 2 - 8 * K, 3 * K], "Chrome")
    B.mug(m, h, -30 * K, 10 * K, k=K)
    m.box([10 * K, -12 * K, h], [42 * K, 14 * K, h + 1 * K], "Paper")  # newspaper
    m.box([12 * K, -10 * K, h + 1 * K], [40 * K, 12 * K, h + 1.4 * K], "Paper")
    m.cyl([-50 * K, -18 * K, h], 7 * K, 3 * K, "Glass", sections=18)  # ashtray
    return m


def stack_chair():
    m = Model()
    w, d, sh = 46 * K, 48 * K, 45 * K
    for sx in (-1, 1):
        m.box([sx * w / 2 - 1.5 * K, -d / 2, 0], [sx * w / 2 + 1.5 * K, -d / 2 + 3 * K, sh], "Chrome")
        m.box([sx * w / 2 - 1.5 * K, d / 2 - 3 * K, 0], [sx * w / 2 + 1.5 * K, d / 2, sh + 40 * K], "Chrome")
    m.box([-w / 2, -d / 2, sh - 3 * K], [w / 2, d / 2, sh], "VinylOrange")
    rot_box(m, [0, d / 2 - 1.5 * K, sh + 30 * K], [w, 3 * K, 20 * K], "VinylOrange", roll=-6)
    return m


# ------------------------------------------------------------------ conference
def conf_table():
    m = Model()
    w, d, h = 360 * K * 0.8, 120 * K, 74 * K
    hw, hd = w / 2, d / 2
    t = trimesh.creation.box(extents=[w - d, d, 4 * K]); t.apply_translation([0, 0, h - 2 * K]); m.add(t, "Walnut")
    for sx in (-1, 1):
        m.cyl([sx * (hw - hd), 0, h - 4 * K], hd, 4 * K, "Walnut", sections=32)
    for sx in (-1, 1):
        m.box([sx * (hw - 80 * K) - 30 * K, -18 * K, 0], [sx * (hw - 80 * K) + 30 * K, 18 * K, h - 4 * K], "Walnut")
    for i in range(6):
        sx = -hw + 60 * K + i * (w - 120 * K) / 5
        sy = (-1 if i % 2 else 1) * 30 * K
        rot_box(m, [sx, sy, h + 0.3], [21.6 * K, 27.9 * K, 0.4], "Paper", yaw=rng.uniform(-15, 15))
    m.box([-12 * K, -10 * K, h], [12 * K, 10 * K, h + 6 * K], "BlackPlastic")  # speakerphone
    m.box([-8 * K, -6 * K, h + 6 * K], [8 * K, 6 * K, h + 6.6 * K], "KeyCaps")
    m.cyl([hw - 70 * K, 0, h], 9 * K, 24 * K, "Glass", sections=16)  # water pitcher
    return m


def whiteboard():
    m = Model()
    w, h = 180 * K, 100 * K
    frame_rect(m, w, h, 3, "Chrome")
    m.box([-w / 2 + 2, -1.5, -h / 2 + 2], [w / 2 - 2, -0.5, h / 2 - 2], "Whiteboard")
    m.box([-w / 2 + 10 * K, -10 * K, -h / 2 - 3 * K], [w / 2 - 10 * K, 0, -h / 2], "Chrome")  # tray
    for i, mat in enumerate(("MarkerBlue", "MarkerRed", "KickPlate")):
        m.cyl([-w / 4 + i * 16 * K, -6 * K, -h / 2 + 1.5 * K], 1.2 * K, 13 * K, mat, axis="x", sections=8)
    m.box([w / 4, -8 * K, -h / 2], [w / 4 + 12 * K, -2 * K, -h / 2 + 5 * K], "MopGray")  # eraser
    # half-erased meeting notes: boxes + arrows as strokes
    for i in range(6):
        y = h / 2 - 15 * K - i * 11 * K
        m.box([-w / 2 + 14 * K, -1.6, y], [-w / 2 + 14 * K + rng.uniform(40, 80) * K, -1.5, y + 1 * K], "MarkerBlue")
    for (cx, cz) in ((30 * K, 15 * K), (60 * K, -15 * K)):
        frame = Model(); frame_rect(frame, 26 * K, 16 * K, 0.1, "MarkerRed")
        copy_into(m, frame, (cx, -1.5, cz))
    rot_box(m, [45 * K, -1.6, 0], [30 * K, 0.1, 1 * K], "MarkerRed", pitch=40)
    return m


def chair_from_base(name):
    import build_models as B
    return B.chair()


if __name__ == "__main__":
    OUT = sys.argv[1] if len(sys.argv) > 1 else "out_rooms"
    os.makedirs(OUT, exist_ok=True)
    models = {
        "SM_80s_RoundTable": round_table(),
        "SM_80s_BoxStack": box_stack(),
        "SM_80s_CoffeeStation": coffee_station(),
        "SM_80s_ReceptionCounter": reception_counter(),
        "SM_80s_WaitingChairs": waiting_chairs(3),
        "SM_80s_CoffeeTable": coffee_table_magazines(),
        "SM_80s_LogoSign": logo_sign(),
        "SM_80s_ExecDesk": exec_desk(),
        "SM_80s_ExecChair": exec_chair(),
        "SM_80s_GuestChair": guest_chair(),
        "SM_80s_Bookshelf": bookshelf(),
        "SM_80s_Credenza": credenza(),
        "SM_80s_RugBoss": rug(("RugRed", "RugNavy", "RugCream")),
        "SM_80s_RugLobby": rug(("RugBrown", "RugRust", "RugCream"), 260, 180),
        "SM_80s_Painting": painting(),
        "SM_80s_Globe": floor_globe(),
        "SM_80s_MetalShelf": metal_shelf(),
        "SM_80s_MopBucket": mop_bucket(),
        "SM_80s_Brooms": broom_set(),
        "SM_80s_WetFloorSign": wet_floor_sign(),
        "SM_80s_UtilitySink": utility_sink(),
        "SM_80s_Fridge": fridge(),
        "SM_80s_VendingMachine": vending_machine(),
        "SM_80s_Kitchenette": kitchenette(),
        "SM_80s_BreakTable": break_table(),
        "SM_80s_StackChair": stack_chair(),
        "SM_80s_ConfTable": conf_table(),
        "SM_80s_Whiteboard": whiteboard(),
    }
    rep = {}
    for n, mdl in models.items():
        rep[n] = write_glb(mdl, f"{OUT}/{n}.glb", n)
        mn, mx = mdl.bounds()
        rep[n]["min"] = [round(float(x), 1) for x in mn]; rep[n]["max"] = [round(float(x), 1) for x in mx]
    json.dump(rep, open(f"{OUT}/sizes.json", "w"), indent=1)
    for n, r in rep.items():
        print(n, r["min"], r["max"], r["tris"])
