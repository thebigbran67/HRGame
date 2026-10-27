"""Plan for shrinking the whole Office building toward its south-west entrance corner.
Walls, trim, door frames, ceiling, floor and ceiling lights are scaled uniformly (sx, sy) about the anchor.
Furniture is grouped into clusters (a cubicle block, a table and its chairs...) that keep their own size and
spacing; each cluster keeps its place inside its room, with the gaps to the walls shrinking proportionally.
Pure python so it can be tested offline on a level dump and run inside Unreal."""

BUILDING = (600.0, -5900.0, 7150.0, 2920.0)
SKIP_CLS = {"PostProcessVolume", "LocalFogVolume", "GroupActor", "WorldDataLayers", "WorldPartitionMiniMap",
            "SkyLight", "SkyAtmosphere", "DirectionalLight", "VolumetricCloud", "BP_QuestManager_C",
            "BP_TrashDropOff_C", "BP_Monster_Angry_C"}
CUBEISH = ("Office80s/Cubicles", "Office80s/Desks", "Office80s/CubicleFills")


def classify(r):
    b0, b1 = r["bmin"], r["bmax"]
    cx, cy = (b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2
    f, m, cls = r["folder"], r.get("mesh") or "", r["cls"]
    if cls in SKIP_CLS or f.startswith("Office80s/Outdoor") or f.startswith("Lights"):
        return None
    if not (BUILDING[0] < cx < BUILDING[2] and BUILDING[1] < cy < BUILDING[3]):
        return None
    lx, ly = b1[0] - b0[0], b1[1] - b0[1]
    if "SM_Plane" in m or (("SM_Cube." in m) and lx > 3000 and ly > 3000):
        return "slab"
    if "SM_Cube." in m and b1[2] - b0[2] > 80:
        return "wall"
    if cls == "BP_CubeDoor_C" or "RoomDoor" in m or "GlassDoor" in m:
        return "door"
    if m.startswith("/Engine/BasicShapes/Cube") or "GlassFront" in m:
        return "thin"
    if cls in ("RectLight", "PointLight", "SpotLight") or b0[2] > 800:
        return "fixture"
    return "furn"


def plan(recs, sx, sy, ax, ay):
    S = (sx, sy)
    A = (ax, ay)

    def f(axis, v):
        return A[axis] + S[axis] * (v - A[axis])

    kinds = [classify(r) for r in recs]
    ops = {}
    # ---- walls: new bounds
    walls = []
    for i, r in enumerate(recs):
        if kinds[i] != "wall":
            continue
        b0, b1 = r["bmin"], r["bmax"]
        long = 0 if (b1[0] - b0[0]) >= (b1[1] - b0[1]) else 1
        per = 1 - long
        c = (b0[per] + b1[per]) / 2
        nb0, nb1 = list(b0[:2]), list(b1[:2])
        nb0[long], nb1[long] = f(long, b0[long]), f(long, b1[long])
        d = f(per, c) - c
        nb0[per] += d; nb1[per] += d
        full = b0[2] < 60 and b1[2] > 300
        walls.append({"i": i, "old": (b0[0], b0[1], b1[0], b1[1]), "new": (nb0[0], nb0[1], nb1[0], nb1[1]),
                      "long": long, "pd": d, "full": full})
        ops[i] = {"op": "span", "axis": long, "lo": nb0[long], "hi": nb1[long], "d": [0, 0]}
        ops[i]["d"][per] = d

    def snap_wall(lo, hi, axis_along, pc, tol_p=45, tol_a=25):
        """wall (incl. headers) running along axis_along whose thickness band is near pc and overlapping lo..hi"""
        best, bd = None, 1e9
        per = 1 - axis_along
        for w in walls:
            if w["long"] != axis_along:
                continue
            o = w["old"]
            plo, phi = o[per], o[per + 2]
            alo, ahi = o[axis_along], o[axis_along + 2]
            if ahi < lo - tol_a or alo > hi + tol_a:
                continue
            dist = 0 if plo <= pc <= phi else min(abs(pc - plo), abs(pc - phi))
            if dist <= tol_p and dist < bd:
                best, bd = w, dist
        return best

    for i, r in enumerate(recs):
        k = kinds[i]
        b0, b1 = r["bmin"], r["bmax"]
        if k == "slab":
            ops[i] = {"op": "slab", "lo": [f(0, b0[0]), f(1, b0[1])], "hi": [f(0, b1[0]), f(1, b1[1])]}
        elif k == "fixture":
            cx, cy = r["loc"][0], r["loc"][1]
            ops[i] = {"op": "move", "d": [f(0, cx) - cx, f(1, cy) - cy]}
        elif k == "thin":
            long = 0 if (b1[0] - b0[0]) >= (b1[1] - b0[1]) else 1
            per = 1 - long
            pc = (b0[per] + b1[per]) / 2
            w = snap_wall(b0[long], b1[long], long, pc)
            dper = w["pd"] if w else f(per, pc) - pc
            L = b1[long] - b0[long]
            if L > 40:
                o = {"op": "span", "axis": long, "lo": f(long, b0[long]), "hi": f(long, b1[long]), "d": [0, 0]}
            else:
                c = (b0[long] + b1[long]) / 2
                o = {"op": "move", "d": [0, 0]}
                o["d"][long] = f(long, c) - c
            o["d"][per] = dper
            ops[i] = o
        elif k == "door":
            p = r["loc"]
            w = None
            for along in (0, 1):
                w = snap_wall(p[along] - 5, p[along] + 5, along, p[1 - along], tol_p=60, tol_a=5)
                if w:
                    break
            if w is None:
                along = 0 if (b1[0] - b0[0]) >= (b1[1] - b0[1]) else 1
                dper = f(1 - along, p[1 - along]) - p[1 - along]
            else:
                along = w["long"]; dper = w["pd"]
            o = {"op": "door", "d": [0, 0], "axis": along, "s": S[along]}
            o["d"][along] = f(along, p[along]) - p[along]
            o["d"][1 - along] = dper
            ops[i] = o

    # ---- furniture clusters
    furn = [i for i in range(len(recs)) if kinds[i] == "furn"]
    parent = {i: i for i in furn}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def gap(a, b):
        A0, A1, B0, B1 = recs[a]["bmin"], recs[a]["bmax"], recs[b]["bmin"], recs[b]["bmax"]
        gx = max(B0[0] - A1[0], A0[0] - B1[0], 0)
        gy = max(B0[1] - A1[1], A0[1] - B1[1], 0)
        return max(gx, gy)

    cub = {i for i in furn if recs[i]["folder"].startswith(CUBEISH)}
    for ii, a in enumerate(furn):
        for b in furn[ii + 1:]:
            th = 260 if (a in cub and b in cub) else 60
            if gap(a, b) <= th:
                parent[find(a)] = find(b)
    clusters = {}
    for i in furn:
        clusters.setdefault(find(i), []).append(i)

    def wall_new(w, side, axis):
        return w["new"][axis + 2] if side == "lo" else w["new"][axis]

    cinfo = []
    for root, mem in clusters.items():
        bx0 = min(recs[i]["bmin"][0] for i in mem); by0 = min(recs[i]["bmin"][1] for i in mem)
        bx1 = max(recs[i]["bmax"][0] for i in mem); by1 = max(recs[i]["bmax"][1] for i in mem)
        B = (bx0, by0, bx1, by1)
        d = [0.0, 0.0]
        for axis in (0, 1):
            per = 1 - axis
            lo_w, hi_w = None, None
            for w in walls:
                if not w["full"]:
                    continue
                o = w["old"]
                if o[per + 2] <= B[per] or o[per] >= B[per + 2]:
                    continue
                if o[axis + 2] <= B[axis] + 8 and (lo_w is None or o[axis + 2] > lo_w["old"][axis + 2]):
                    lo_w = w
                if o[axis] >= B[axis + 2] - 8 and (hi_w is None or o[axis] < hi_w["old"][axis]):
                    hi_w = w
            W = B[axis + 2] - B[axis]
            if lo_w is None or hi_w is None:
                c = (B[axis] + B[axis + 2]) / 2
                d[axis] = f(axis, c) - c
                continue
            L, R = lo_w["old"][axis + 2], hi_w["old"][axis]
            nL, nR = lo_w["new"][axis + 2], hi_w["new"][axis]
            gl, gr = max(B[axis] - L, 0), max(R - B[axis + 2], 0)
            space = max(nR - nL - W, 0)
            newmin = nL + (space * gl / (gl + gr) if gl + gr > 1e-6 else space / 2)
            d[axis] = newmin - B[axis]
        cinfo.append({"members": mem, "B": B, "d": d})

    # ---- resolve: push clusters out of walls / small clusters out of big ones (only new overlaps)
    def ov(a, b, m=1.0):
        return a[0] < b[2] - m and b[0] < a[2] - m and a[1] < b[3] - m and b[1] < a[3] - m

    def nbox(c):
        B, d = c["B"], c["d"]
        return (B[0] + d[0], B[1] + d[1], B[2] + d[0], B[3] + d[1])

    def push(c, ob):
        nb = nbox(c)
        pen = [(ob[2] - nb[0], 0, 1), (nb[2] - ob[0], 0, -1), (ob[3] - nb[1], 1, 1), (nb[3] - ob[1], 1, -1)]
        p, axis, sgn = min(pen)
        c["d"][axis] += sgn * (p + 2)

    for _ in range(3):
        for c in cinfo:
            for w in walls:
                if w["full"] and ov(nbox(c), w["new"]) and not ov(c["B"], w["old"], 6):
                    push(c, w["new"])
        for c in cinfo:
            if len(c["members"]) > 4:
                continue
            for o in cinfo:
                if o is c or len(o["members"]) <= 4:
                    continue
                if ov(nbox(c), nbox(o)) and not ov(c["B"], o["B"]):
                    push(c, nbox(o))
    for c in cinfo:
        for i in c["members"]:
            ops[i] = {"op": "move", "d": list(c["d"])}
    return kinds, ops, walls, cinfo
