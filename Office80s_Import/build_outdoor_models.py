"""Outdoor set dressing: grass tufts, dead trees, iron fence, lamp post, rocks + a tileable grass texture."""
import math, os, sys, json, random
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter
from build_models import Model, MATS, write_glb

K = 1.32
MATS.update({
    "GrassDark":  ("#2E3A1E", 0.0, 0.80, None),
    "GrassDead":  ("#6B6236", 0.0, 0.85, None),
    "GrassMid":   ("#45502A", 0.0, 0.80, None),
    "Bark":       ("#2C2520", 0.0, 0.95, None),
    "BarkDark":   ("#1C1815", 0.0, 0.95, None),
    "Iron":       ("#1A1A1C", 0.5, 0.55, None),
    "RustIron":   ("#3A2418", 0.3, 0.80, None),
    "LampGlass":  ("#C9C27A", 0.0, 0.20, [2.2, 2.0, 0.9]),
    "Stone":      ("#55524C", 0.0, 0.90, None),
    "StoneMoss":  ("#3E4733", 0.0, 0.95, None),
})


def seg_cyl(m, p0, p1, r0, r1, mat, sections=7):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    L = np.linalg.norm(p1 - p0)
    c = trimesh.creation.cylinder(radius=1.0, height=L, sections=sections)
    v = c.vertices
    t = (v[:, 2] / L) + 0.5
    rr = r0 + (r1 - r0) * t
    v[:, 0] *= rr; v[:, 1] *= rr
    c.vertices = v
    c.apply_translation([0, 0, L / 2])
    R = trimesh.geometry.align_vectors([0, 0, 1], (p1 - p0) / L)
    c.apply_transform(R)
    c.apply_translation(p0)
    m.add(c, mat)


def dead_tree(seed, height=820):
    rng = random.Random(seed)
    m = Model()
    def branch(p, d, length, r, depth):
        d = np.array(d) / np.linalg.norm(d)
        # gnarled: split into wiggly sub-segments
        n = 3
        q = np.array(p, float)
        for i in range(n):
            jitter = np.array([rng.uniform(-.35, .35), rng.uniform(-.35, .35), rng.uniform(-.15, .2)])
            dd = d + jitter
            dd /= np.linalg.norm(dd)
            q2 = q + dd * length / n
            seg_cyl(m, q, q2, r * (1 - 0.2 * i / n), r * (1 - 0.2 * (i + 1) / n), "Bark" if depth < 2 else "BarkDark")
            q = q2
        if depth >= 4 or r < 1.2:
            return
        kids = rng.randint(2, 3)
        for k in range(kids):
            ang = rng.uniform(0, 2 * math.pi)
            tilt = rng.uniform(0.45, 0.95)
            nd = d * (1 - tilt) + np.array([math.cos(ang), math.sin(ang), 0]) * tilt
            nd[2] += rng.uniform(-0.1, 0.35)
            branch(q, nd, length * rng.uniform(0.55, 0.75), r * rng.uniform(0.5, 0.65), depth + 1)
    # flared roots
    for i in range(5):
        a = i * 72 + rng.uniform(-15, 15)
        seg_cyl(m, [0, 0, 30], [math.cos(math.radians(a)) * 70, math.sin(math.radians(a)) * 70, -6], 13, 4, "Bark")
    trunk_len = height * 0.42
    seg_cyl(m, [0, 0, -5], [0, 0, 20], 24, 22, "Bark")
    branch([0, 0, 15], [rng.uniform(-.12, .12), rng.uniform(-.12, .12), 1], trunk_len, 21, 0)
    return m


def iron_fence(length=300, seed=0):
    rng = random.Random(seed)
    m = Model()
    h = 160 * K
    for x in (-length / 2, length / 2):
        m.box([x - 4, -4, 0], [x + 4, 4, h + 10], "Iron")
        s = trimesh.creation.icosphere(subdivisions=1, radius=6); s.apply_translation([x, 0, h + 14]); m.add(s, "Iron")
    for z in (22, h - 18):
        m.box([-length / 2, -1.5, z - 2], [length / 2, 1.5, z + 2], "RustIron" if rng.random() < 0.4 else "Iron")
    x = -length / 2 + 14
    while x < length / 2 - 8:
        if rng.random() < 0.06:          # missing picket
            x += 14; continue
        lean = rng.uniform(-3, 3) if rng.random() < 0.8 else rng.uniform(-14, 14)
        hh = h if rng.random() > 0.08 else h * rng.uniform(0.5, 0.8)   # snapped
        b = trimesh.creation.box(extents=[1.8, 1.8, hh])
        b.apply_translation([0, 0, hh / 2])
        b.apply_transform(trimesh.transformations.rotation_matrix(math.radians(lean), [0, 1, 0]))
        b.apply_translation([x, 0, 0])
        m.add(b, "Iron" if rng.random() > 0.25 else "RustIron")
        if hh == h:
            tip = trimesh.creation.cone(radius=3.2, height=9, sections=4)
            tip.apply_translation([0, 0, hh])
            tip.apply_transform(trimesh.transformations.rotation_matrix(math.radians(lean), [0, 1, 0]))
            tip.apply_translation([x, 0, 0]); m.add(tip, "Iron")
        x += 14
    return m


def lamp_post():
    m = Model()
    h = 330 * K
    for i in range(4):
        a = math.radians(i * 90 + 45)
        seg_cyl(m, [0, 0, 0], [math.cos(a) * 22, math.sin(a) * 22, 0.1], 6, 6, "Iron", 6)
    seg_cyl(m, [0, 0, 0], [0, 0, 40], 16, 11, "Iron", 12)
    seg_cyl(m, [0, 0, 40], [0, 0, h - 40], 6, 4.5, "Iron", 10)
    seg_cyl(m, [0, 0, h - 40], [0, 0, h - 26], 9, 9, "Iron", 10)
    # lantern
    z0 = h - 26
    m.box([-18, -18, z0], [18, 18, z0 + 4], "Iron")
    m.box([-15, -15, z0 + 4], [15, 15, z0 + 48], "LampGlass")
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box([sx * 15 - 1.5, sy * 15 - 1.5, z0 + 4], [sx * 15 + 1.5, sy * 15 + 1.5, z0 + 48], "Iron")
    cap = trimesh.creation.cone(radius=26, height=22, sections=4)
    cap.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 4, [0, 0, 1]))
    cap.apply_translation([0, 0, z0 + 48]); m.add(cap, "Iron")
    s = trimesh.creation.icosphere(subdivisions=1, radius=4); s.apply_translation([0, 0, z0 + 72]); m.add(s, "Iron")
    return m


def grass_patch(seed, size=420, blades=420):
    rng = random.Random(seed)
    m = Model()
    for i in range(blades):
        # clumpy distribution
        cx, cy = rng.gauss(0, size / 4), rng.gauss(0, size / 4)
        cx = max(-size / 2, min(size / 2, cx)); cy = max(-size / 2, min(size / 2, cy))
        hh = rng.uniform(14, 42) * K
        b = trimesh.creation.box(extents=[rng.uniform(1.8, 3.2), 0.3, hh])
        v = b.vertices
        v[:, 0] *= np.where(v[:, 2] > 0, 0.25, 1.0)      # taper to a point
        b.vertices = v
        b.apply_translation([0, 0, hh / 2])
        b.apply_transform(trimesh.transformations.euler_matrix(rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(0, 6.28), "sxyz"))
        b.apply_translation([cx, cy, -1])
        r = rng.random()
        m.add(b, "GrassDead" if r < 0.35 else ("GrassMid" if r < 0.65 else "GrassDark"))
    return m


def rocks(seed):
    rng = random.Random(seed)
    m = Model()
    for i in range(rng.randint(2, 4)):
        s = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
        s.vertices *= np.array([rng.uniform(20, 45), rng.uniform(16, 35), rng.uniform(10, 24)])
        s.vertices += np.random.default_rng(seed * 10 + i).normal(scale=2.0, size=s.vertices.shape)
        s.apply_translation([rng.uniform(-40, 40), rng.uniform(-40, 40), 2])
        m.add(s, "Stone" if i % 2 == 0 else "StoneMoss")
    return m


def grass_texture(path, N=1024, seed=5):
    rng = random.Random(seed)
    base = np.zeros((N, N, 3), np.float32)
    # low-frequency patchiness (tileable via summed cosines)
    yy, xx = np.mgrid[0:N, 0:N] / N
    patch = np.zeros((N, N))
    for k in range(18):
        fx, fy = rng.randint(-5, 5), rng.randint(-5, 5)
        if fx == 0 and fy == 0:
            continue
        patch += np.cos(2 * np.pi * (fx * xx + fy * yy) + rng.uniform(0, 6.28)) / (1 + 0.35 * k)
    patch = (patch - patch.min()) / (patch.max() - patch.min())
    dark = np.array([38, 50, 26]); dead = np.array([96, 88, 52]); dirt = np.array([52, 42, 30])
    base[:] = dark * (1 - patch[..., None]) + dead * patch[..., None]
    dirt_mask = np.clip((patch - 0.82) * 5, 0, 1)[..., None]
    base = base * (1 - dirt_mask) + dirt * dirt_mask
    base += np.random.default_rng(seed).normal(0, 6, base.shape)
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for i in range(26000):  # blades, drawn with wraparound so the tile repeats seamlessly
        x, y = rng.uniform(0, N), rng.uniform(0, N)
        L = rng.uniform(6, 18); a = rng.uniform(-0.6, 0.6) - math.pi / 2
        shade = rng.random()
        col = (int(30 + 60 * shade), int(44 + 52 * shade), int(20 + 26 * shade))
        if rng.random() < 0.25:
            col = (int(90 + 40 * shade), int(84 + 30 * shade), int(48 + 16 * shade))
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                d.line((x + ox, y + oy, x + ox + math.cos(a) * L, y + oy + math.sin(a) * L), fill=col, width=1)
    im = im.filter(ImageFilter.GaussianBlur(0.5))
    im.save(path)


if __name__ == "__main__":
    OUT = sys.argv[1] if len(sys.argv) > 1 else "out_outdoor"
    os.makedirs(OUT, exist_ok=True)
    grass_texture(f"{OUT}/T_80s_Grass.png")
    models = {
        "SM_80s_DeadTree_A": dead_tree(11, 820),
        "SM_80s_DeadTree_B": dead_tree(23, 700),
        "SM_80s_DeadTree_C": dead_tree(37, 950),
        "SM_80s_IronFence": iron_fence(300, 1),
        "SM_80s_IronFence_B": iron_fence(300, 2),
        "SM_80s_LampPost": lamp_post(),
        "SM_80s_GrassPatch_A": grass_patch(1, blades=700),
        "SM_80s_GrassPatch_B": grass_patch(2, blades=500),
        "SM_80s_Rocks_A": rocks(3),
        "SM_80s_Rocks_B": rocks(8),
    }
    rep = {}
    for n, mdl in models.items():
        rep[n] = write_glb(mdl, f"{OUT}/{n}.glb", n)
        mn, mx = mdl.bounds()
        rep[n]["min"] = [round(float(x), 1) for x in mn]; rep[n]["max"] = [round(float(x), 1) for x in mx]
        print(n, rep[n]["min"], rep[n]["max"], rep[n]["tris"])
    json.dump(rep, open(f"{OUT}/sizes.json", "w"), indent=1)
