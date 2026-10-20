"""Builds 1980s office furniture as .glb files for Unreal.

Everything is authored in Unreal space (centimeters, X = length, Y = depth,
Z = up, pivot at bottom center) and converted to glTF (meters, Y-up) on
export. Each model is one mesh with one material per part type.
"""
import json, struct, math, os, sys
import numpy as np
import trimesh



def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


MATS = {
    # name: (color, metallic, roughness, emissive)
    "DeskSteel":    ("#A39A84", 0.0, 0.42, None),   # putty enamel steel
    "DeskLaminate": ("#6E4C30", 0.0, 0.32, None),   # faux walnut top
    "VinylTrim":    ("#232120", 0.0, 0.60, None),
    "Chrome":       ("#C8CACC", 1.0, 0.22, None),
    "PanelFabric":  ("#7C6B57", 0.0, 0.96, None),   # oatmeal-brown burlap weave
    "PanelTrim":    ("#9C978C", 0.0, 0.48, None),
    "KickPlate":    ("#2F2C29", 0.0, 0.70, None),
    "BeigePlastic": ("#D6CCB4", 0.0, 0.50, None),
    "CRTScreen":    ("#0E150E", 0.0, 0.08, [0.010, 0.045, 0.014]),
    "KeyCaps":      ("#5B5650", 0.0, 0.55, None),
    "Paper":        ("#ECE6D4", 0.0, 0.90, None),
    "Mug":          ("#8A3A22", 0.0, 0.35, None),
    "BlackPlastic": ("#1C1B1A", 0.0, 0.45, None),
    "ChairFabric":  ("#5E3F2B", 0.0, 0.95, None),   # brown tweed
}


class Model:
    def __init__(self):
        self.parts = {}

    def add(self, mesh, mat):
        self.parts.setdefault(mat, []).append(mesh)

    def box(self, mn, mx, mat):
        mn, mx = np.array(mn, float), np.array(mx, float)
        b = trimesh.creation.box(extents=mx - mn)
        b.apply_translation((mn + mx) / 2)
        self.add(b, mat)

    def boxc(self, center, size, mat, yaw=0.0):
        b = trimesh.creation.box(extents=size)
        if yaw:
            b.apply_transform(trimesh.transformations.rotation_matrix(math.radians(yaw), [0, 0, 1]))
        b.apply_translation(center)
        self.add(b, mat)

    def cyl(self, base, radius, height, mat, axis="z", sections=20):
        c = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
        c.apply_translation([0, 0, height / 2])
        if axis == "x":
            c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        elif axis == "y":
            c.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))
        c.apply_translation(base)
        self.add(c, mat)

    def bounds(self):
        allv = np.vstack([m.vertices for ms in self.parts.values() for m in ms])
        return allv.min(0), allv.max(0)


# ---------------------------------------------------------------- glb writer
def write_glb(model, path, name):
    buf = bytearray()
    views, accessors, prims, materials = [], [], [], []

    def push(arr, target):
        nonlocal buf
        while len(buf) % 4:
            buf += b"\0"
        off = len(buf)
        data = arr.tobytes()
        buf += data
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(data), "target": target})
        return len(views) - 1

    for mi, (mat, meshes) in enumerate(sorted(model.parts.items())):
        m = trimesh.util.concatenate(meshes)
        m = trimesh.graph.smooth_shade(m, angle=math.radians(35))
        v = np.asarray(m.vertices, np.float64)
        n = np.asarray(m.vertex_normals, np.float64)
        f = np.asarray(m.faces, np.uint32)
        # Unreal (x,y,z) cm  ->  glTF (x, z, y) m. That swap mirrors, so flip winding.
        gv = (v[:, [0, 2, 1]] / 100.0).astype(np.float32)
        gn = n[:, [0, 2, 1]].astype(np.float32)
        gf = f[:, [0, 2, 1]].copy()
        # box-projected UVs (1 tile per meter)
        an = np.abs(n).argmax(1)
        uv = np.where(an[:, None] == 0, v[:, [1, 2]], np.where(an[:, None] == 1, v[:, [0, 2]], v[:, [0, 1]])) / 100.0
        uv = uv.astype(np.float32)
        pv = push(gv, 34962); pn = push(gn, 34962); pu = push(uv, 34962); pi = push(gf.flatten(), 34963)
        a0 = len(accessors)
        accessors += [
            {"bufferView": pv, "componentType": 5126, "count": len(gv), "type": "VEC3",
             "min": gv.min(0).tolist(), "max": gv.max(0).tolist()},
            {"bufferView": pn, "componentType": 5126, "count": len(gn), "type": "VEC3"},
            {"bufferView": pu, "componentType": 5126, "count": len(uv), "type": "VEC2"},
            {"bufferView": pi, "componentType": 5125, "count": gf.size, "type": "SCALAR"},
        ]
        col, met, rough, emis = MATS[mat]
        md = {"name": "MI_80s_" + mat,
              "pbrMetallicRoughness": {"baseColorFactor": srgb(col) + [1.0],
                                       "metallicFactor": met, "roughnessFactor": rough}}
        if emis:
            md["emissiveFactor"] = emis
        materials.append(md)
        prims.append({"attributes": {"POSITION": a0, "NORMAL": a0 + 1, "TEXCOORD_0": a0 + 2},
                      "indices": a0 + 3, "material": mi})

    gltf = {"asset": {"version": "2.0", "generator": "office80s"},
            "scene": 0, "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0, "name": name}],
            "meshes": [{"name": name, "primitives": prims}],
            "materials": materials, "accessors": accessors, "bufferViews": views,
            "buffers": [{"byteLength": len(buf)}]}
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    while len(buf) % 4:
        buf += b"\0"
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(buf))
    out += struct.pack("<II", len(js), 0x4E4F534A) + js
    out += struct.pack("<II", len(buf), 0x004E4942) + bytes(buf)
    open(path, "wb").write(out)
    mn, mx = model.bounds()
    return {"file": os.path.basename(path), "size_cm": [round(x, 2) for x in (mx - mn)],
            "tris": int(sum(len(m.faces) for ms in model.parts.values() for m in ms))}


# ---------------------------------------------------------------- desk
# Blockout desks: 175 x 100 top, top surface 99 cm off the floor.
# The front (where you sit) is -Y.
def desk(props=None, W=175.0, D=100.0, H=99.0):
    m = Model()
    hw, hd = W / 2, D / 2
    top_t = 4.0
    m.box([-hw, -hd, H - top_t], [hw, hd, H], "DeskLaminate")
    # black vinyl T-molding around the edge of the top
    e = 0.8
    m.box([-hw - e, -hd - e, H - top_t], [hw + e, -hd, H + 0.15], "VinylTrim")
    m.box([-hw - e, hd, H - top_t], [hw + e, hd + e, H + 0.15], "VinylTrim")
    m.box([-hw - e, -hd, H - top_t], [-hw, hd, H + 0.15], "VinylTrim")
    m.box([hw, -hd, H - top_t], [hw + e, hd, H + 0.15], "VinylTrim")

    ped_w = 46.0
    body_top = H - top_t
    base_h = 6.0
    for side in (-1, 1):
        x0, x1 = (-hw + 1.5, -hw + 1.5 + ped_w) if side < 0 else (hw - 1.5 - ped_w, hw - 1.5)
        # pedestal shell
        m.box([x0, -hd + 3, base_h], [x1, hd - 1.5, body_top], "DeskSteel")
        # recessed black kick base
        m.box([x0 + 1.5, -hd + 6, 0], [x1 - 1.5, hd - 4, base_h], "KickPlate")
        # drawer fronts: left = box, box, file. right = file, file
        fx0, fx1 = x0 + 1.2, x1 - 1.2
        avail = body_top - base_h - 1.0
        layout = [0.24, 0.24, 0.52] if side < 0 else [0.5, 0.5]
        z = body_top - 0.6
        for frac in layout:
            h = avail * frac
            z0, z1 = z - h + 0.6, z
            m.box([fx0, -hd + 1.4, z0], [fx1, -hd + 3.0, z1], "DeskSteel")
            # chrome recessed pull (lip + bar)
            cz = z1 - min(9.0, h * 0.35)
            m.box([fx0 + 9, -hd + 0.4, cz - 1.0], [fx1 - 9, -hd + 1.4, cz + 1.0], "Chrome")
            m.box([fx0 + 9, -hd + 0.4, cz - 2.2], [fx1 - 9, -hd + 1.0, cz - 1.0], "KickPlate")
            # label card holder on file drawers
            if frac > 0.4:
                m.box([-4 + (fx0 + fx1) / 2, -hd + 1.0, z1 - 6.5], [4 + (fx0 + fx1) / 2, -hd + 1.4, z1 - 3.5], "Chrome")
            z = z0 - 0.6
    # center pencil drawer
    cx0, cx1 = -hw + 1.5 + ped_w + 0.6, hw - 1.5 - ped_w - 0.6
    m.box([cx0, -hd + 3, body_top - 9], [cx1, hd - 6, body_top], "DeskSteel")
    m.box([cx0 + 0.6, -hd + 1.4, body_top - 8.4], [cx1 - 0.6, -hd + 3.0, body_top - 0.6], "DeskSteel")
    m.box([-12, -hd + 0.4, body_top - 5.2], [12, -hd + 1.4, body_top - 3.4], "Chrome")
    # modesty panel at the back of the knee hole
    m.box([cx0, hd - 4.5, 22], [cx1, hd - 2.5, body_top - 9], "DeskSteel")

    if props:
        props(m, H)
    return m


def crt_terminal(m, H, x=-22, y=8, k=1.32):
    # beige CRT with tapered back, sitting on a little tilt base
    m.cyl([x, y, H], 9 * k, 3 * k, "BeigePlastic")
    w, h, d = 36 * k, 31 * k, 22 * k
    zb = H + 3 * k
    m.box([x - w / 2, y - d / 2, zb], [x + w / 2, y + d / 2, zb + h], "BeigePlastic")
    m.box([x - w * 0.36, y + d / 2, zb + 3 * k], [x + w * 0.36, y + d / 2 + 16 * k, zb + h - 4 * k], "BeigePlastic")
    m.box([x - w * 0.26, y + d / 2 + 16 * k, zb + 6 * k], [x + w * 0.26, y + d / 2 + 22 * k, zb + h - 9 * k], "BeigePlastic")
    # dark bezel + slightly glowing screen
    m.box([x - w * 0.42, y - d / 2 - 0.4, zb + 6 * k], [x + w * 0.42, y - d / 2, zb + h - 3 * k], "BlackPlastic")
    m.box([x - w * 0.37, y - d / 2 - 0.8, zb + 7.5 * k], [x + w * 0.37, y - d / 2 - 0.4, zb + h - 4.5 * k], "CRTScreen")
    # power button + vents
    m.box([x + w * 0.38, y - d / 2 - 0.6, zb + 2 * k], [x + w * 0.45, y - d / 2, zb + 4 * k], "KeyCaps")
    for i in range(5):
        vx = x - w * 0.3 + i * w * 0.15
        m.box([vx, y + d / 2 + 3 * k, zb + h - 4.2 * k], [vx + w * 0.08, y + d / 2 + 13 * k, zb + h - 3.8 * k], "BlackPlastic")


def keyboard(m, H, x=-22, y=-30, k=1.32):
    w, d = 46 * k, 18 * k
    m.box([x - w / 2, y - d / 2, H], [x + w / 2, y + d / 2, H + 3 * k], "BeigePlastic")
    m.box([x - w * 0.45, y - d * 0.38, H + 3 * k], [x + w * 0.30, y + d * 0.40, H + 4.2 * k], "KeyCaps")
    m.box([x + w * 0.33, y - d * 0.38, H + 3 * k], [x + w * 0.46, y + d * 0.40, H + 4.2 * k], "KeyCaps")
    m.box([x - w * 0.30, y - d * 0.38, H + 4.2 * k], [x + w * 0.10, y - d * 0.26, H + 4.6 * k], "BeigePlastic")  # space bar


def papers(m, H, x, y, k=1.32, n=3, yaw=8):
    for i in range(n):
        m.boxc([x + i * 0.8, y - i * 0.6, H + (i + 0.5) * 0.35], [21.6 * k, 27.9 * k, 0.35], "Paper", yaw=yaw - i * 5)


def mug(m, H, x, y, k=1.32):
    m.cyl([x, y, H], 4.2 * k, 9.5 * k, "Mug", sections=18)
    m.box([x + 4 * k, y - 0.8 * k, H + 2.5 * k], [x + 6.8 * k, y + 0.8 * k, H + 7.5 * k], "Mug")


def desk_phone(m, H, x, y, k=1.32):
    m.box([x - 11 * k, y - 10 * k, H], [x + 11 * k, y + 10 * k, H + 6 * k], "BeigePlastic")
    m.box([x - 7 * k, y - 8 * k, H + 6 * k], [x + 7 * k, y - 1 * k, H + 6.6 * k], "KeyCaps")  # keypad
    # handset lying across the top
    m.box([x - 10 * k, y + 2 * k, H + 6 * k], [x + 10 * k, y + 7 * k, H + 9 * k], "BeigePlastic")
    m.box([x - 12 * k, y + 1.5 * k, H + 6 * k], [x - 7 * k, y + 7.5 * k, H + 10.5 * k], "BeigePlastic")
    m.box([x + 7 * k, y + 1.5 * k, H + 6 * k], [x + 12 * k, y + 7.5 * k, H + 10.5 * k], "BeigePlastic")


def in_tray(m, H, x, y, k=1.32):
    w, d = 26 * k, 34 * k
    for lvl in range(2):
        z = H + lvl * 9 * k
        m.box([x - w / 2, y - d / 2, z], [x + w / 2, y + d / 2, z + 0.8], "BlackPlastic")
        m.box([x - w / 2, y + d / 2 - 1, z], [x + w / 2, y + d / 2, z + 6 * k], "BlackPlastic")
        m.box([x - w / 2, y - d / 2, z], [x - w / 2 + 1, y + d / 2, z + 6 * k], "BlackPlastic")
        m.box([x + w / 2 - 1, y - d / 2, z], [x + w / 2, y + d / 2, z + 6 * k], "BlackPlastic")
        m.box([x - w * 0.4, y - d * 0.42, z + 0.8], [x + w * 0.4, y + d * 0.42, z + 0.8 + (2.5 - lvl) * 1.2], "Paper")
    for sx in (-1, 1):
        m.box([x + sx * w / 2 - 1, y - d / 2, H], [x + sx * w / 2, y - d / 2 + 1, H + 9 * k + 1], "Chrome")


def rolodex(m, H, x, y, k=1.32):
    m.box([x - 9 * k, y - 6 * k, H], [x + 9 * k, y + 6 * k, H + 2 * k], "BlackPlastic")
    m.cyl([x - 8 * k, y, H + 8 * k], 0.5 * k, 16 * k, "Chrome", axis="x", sections=8)
    for i in range(14):
        a = math.radians(-60 + i * 9)
        m.boxc([x, y + math.sin(a) * 4 * k, H + 8 * k + math.cos(a) * 4 * k], [13 * k, 0.15, 7 * k], "Paper")


def task_lamp(m, H, x, y, k=1.32):
    m.cyl([x, y, H], 8 * k, 2.5 * k, "BlackPlastic")
    m.cyl([x, y, H + 2.5 * k], 0.9 * k, 30 * k, "Chrome", sections=10)
    m.box([x - 0.9 * k, y - 22 * k, H + 31 * k], [x + 0.9 * k, y + 0.9 * k, H + 33 * k], "Chrome")
    m.cyl([x, y - 22 * k, H + 22 * k], 7 * k, 11 * k, "BlackPlastic", sections=16)


def props_terminal(m, H):
    crt_terminal(m, H, x=-30, y=10)
    keyboard(m, H, x=-30, y=-32)
    mug(m, H, x=22, y=-28)
    papers(m, H, x=48, y=0, n=4, yaw=-6)


def props_clerical(m, H):
    in_tray(m, H, x=-58, y=12)
    desk_phone(m, H, x=48, y=18)
    papers(m, H, x=-8, y=-14, n=6, yaw=4)
    rolodex(m, H, x=20, y=22)
    task_lamp(m, H, x=72, y=34)
    mug(m, H, x=-30, y=-34)


# ---------------------------------------------------------------- cubicle panel
# Built at the blockout's real panel size so nothing stretches.
def panel(L, T=25.0, H=253.0):
    m = Model()
    hl, ht = L / 2, T / 2
    post = 4.5
    kick = 9.0
    cap = 5.0
    # end posts
    for s in (-1, 1):
        x0, x1 = (-hl, -hl + post) if s < 0 else (hl - post, hl)
        m.box([x0, -ht, 0], [x1, ht, H - cap], "PanelTrim")
    # kick plate (slightly inset)
    m.box([-hl + post, -ht + 1.2, 0], [hl - post, ht - 1.2, kick], "KickPlate")
    # fabric faces, inset from the trim
    m.box([-hl + post, -ht + 0.8, kick], [hl - post, ht - 0.8, H - cap], "PanelFabric")
    # rounded top cap
    m.box([-hl, -ht, H - cap], [hl, ht, H - cap / 2], "PanelTrim")
    c = trimesh.creation.cylinder(radius=ht, height=L, sections=24)
    c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    c.apply_scale([1, 1, (cap / 2) / ht])
    c.apply_translation([0, 0, H - cap / 2])
    m.add(c, "PanelTrim")
    # thin metal raceway seam a third of the way up, both faces
    for s in (-1, 1):
        y0, y1 = (-ht + 0.4, -ht + 0.9) if s < 0 else (ht - 0.9, ht - 0.4)
        m.box([-hl + post, y0, kick + 70], [hl - post, y1, kick + 72], "PanelTrim")
    # leveling feet
    for s in (-1, 1):
        m.cyl([s * (hl - post / 2), 0, -0.01], 2.0, 1.0, "KickPlate", sections=10)
    return m


# ---------------------------------------------------------------- chair (optional)
def chair(k=1.32):
    m = Model()
    for i in range(5):
        a = i * 72
        m.boxc([math.cos(math.radians(a)) * 15 * k, math.sin(math.radians(a)) * 15 * k, 6 * k],
               [30 * k, 4 * k, 3 * k], "BlackPlastic", yaw=a)
        cx, cy = math.cos(math.radians(a)) * 29 * k, math.sin(math.radians(a)) * 29 * k
        m.cyl([cx, cy, 0], 2.6 * k, 4.5 * k, "BlackPlastic", sections=12)
    m.cyl([0, 0, 4 * k], 3.5 * k, 34 * k, "Chrome", sections=16)
    m.box([-24 * k, -23 * k, 38 * k], [24 * k, 23 * k, 46 * k], "ChairFabric")
    m.box([-20 * k, -20 * k, 35 * k], [20 * k, 20 * k, 38 * k], "BlackPlastic")
    # back (seated person faces -Y, so the back sits at +Y)
    m.box([-3 * k, 17 * k, 40 * k], [3 * k, 21 * k, 60 * k], "Chrome")
    m.box([-21 * k, 18 * k, 55 * k], [21 * k, 26 * k, 92 * k], "ChairFabric")
    for s in (-1, 1):
        m.box([s * 24 * k - 1.5 * k, -10 * k, 46 * k], [s * 24 * k + 1.5 * k, 14 * k, 48 * k], "Chrome")
        m.box([s * 24 * k - 1.5 * k, -16 * k, 62 * k], [s * 24 * k + 2.0 * k, 12 * k, 66 * k], "BlackPlastic")
        m.box([s * 24 * k - 1.0 * k, -12 * k, 48 * k], [s * 24 * k + 1.0 * k, -9 * k, 62 * k], "Chrome")
    return m


if __name__ == "__main__":
    OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
    os.makedirs(OUT, exist_ok=True)
    report = {}
    report["SM_Desk80s_Terminal"] = write_glb(desk(props_terminal), f"{OUT}/SM_Desk80s_Terminal.glb", "SM_Desk80s_Terminal")
    report["SM_Desk80s_Clerical"] = write_glb(desk(props_clerical), f"{OUT}/SM_Desk80s_Clerical.glb", "SM_Desk80s_Clerical")
    report["SM_Desk80s_Plain"] = write_glb(desk(None), f"{OUT}/SM_Desk80s_Plain.glb", "SM_Desk80s_Plain")
    for L in (100, 262, 318):
        n = f"SM_CubiclePanel80s_{L}"
        report[n] = write_glb(panel(float(L)), f"{OUT}/{n}.glb", n)
    report["SM_OfficeChair80s"] = write_glb(chair(), f"{OUT}/SM_OfficeChair80s.glb", "SM_OfficeChair80s")
    print(json.dumps(report, indent=1))
