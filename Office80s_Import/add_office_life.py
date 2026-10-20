"""
HRGame / Office: dress the level as a lived-in 1980s office.
Run AFTER replace_blockout_80s.py, with the Office map open:
    py "C:/Users/rbrannig/Documents/GitHub/HRGame/Office80s_Import/add_office_life.py"

- painted two-tone walls, chair rail, baseboard, acoustic-tile ceiling, fluorescent fixtures
- main floor: ~14 desks become meeting tables / supply corners / coffee nooks / storage cubicles
  (done once; kept in Office80s/CubicleFills), the rest get chairs, bins, side files, pin-ups
- themed rooms: reception (BP_Monster4), janitor closet (BP_Monster), boss office (BP_Monster2),
  break room (east), conference room (north)
- a light scattering of wall props and decor elsewhere
Everything regenerated lives in Office80s/Life and is cleared on re-run. One undo step.
"""
import os, math, json, random
import unreal

SEED = 1987
FOLDER = "Office80s/Life"
FILLS = "Office80s/CubicleFills"
DEST = "/Game/Office80s/Props"
MATDEST = "/Game/Office80s/Materials"
RAIL = 135.0
CONVERT_DESKS = 14
CLEARANCE = 100.0
GAMEPLAY_CLEARANCE = 200.0

# room rectangles (x0, y0, x1, y1) read off this level's walls
ROOMS = {
    "reception":  (730, -5720, 2070, -3300),
    "janitor":    (4922, -5720, 5471, -3790),
    "boss":       (5508, 330, 7010, 2786),
    "break":      (5531, -2089, 7010, 259),
    "conference": (2948, 1510, 5440, 2786),
}
RECEPTION_SLAB = "SM_Cube221"
REC_FALLBACK = (1511.5, -4001.0, 513.0, 1218.0, 168.0)   # center x, y, size x, size y, top z

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
rng = random.Random(SEED)


def log(m):
    unreal.log("[Office80s] " + str(m))


def src_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Office80s_Import")


SIZES = json.load(open(os.path.join(src_dir(), "office80s_sizes.json")))
DECOR = {"Poster_Sunset", "Poster_Memphis", "Poster_Teamwork", "WallClock", "BulletinBoard", "CubiclePinup_A",
         "CubiclePinup_B", "CubiclePinup_C", "CeilingLight", "LogoSign", "Painting", "Whiteboard", "RugBoss", "RugLobby"}
_mesh_cache = {}


def mesh(short):
    """SM_80s_<short>, imported on first use."""
    name = "SM_80s_" + short
    if name in _mesh_cache:
        return _mesh_cache[name]
    dest = DEST + "/" + name
    task = unreal.AssetImportTask()
    task.filename = os.path.join(src_dir(), name + ".glb")
    task.destination_path = dest
    task.automated = True
    task.replace_existing = True
    task.save = True
    asset_tools.import_asset_tasks([task])
    sm = None
    for p in list(task.imported_object_paths or []) + list(unreal.EditorAssetLibrary.list_assets(dest, recursive=True)):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            sm = a
            break
    if sm is None:
        raise RuntimeError("import failed: " + name)
    sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    sub.remove_collisions(sm)
    if short not in DECOR:
        sub.add_simple_collisions(sm, unreal.ScriptCollisionShapeType.BOX)
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
    _mesh_cache[name] = sm
    return sm


def find_mesh(folder):
    for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            return a
    raise RuntimeError("missing mesh in " + folder + " (run replace_blockout_80s.py first)")


def size_of(short):
    s = SIZES["SM_80s_" + short]
    return s["min"], s["max"]


# ------------------------------------------------------------------ materials
def lin(hexcol):
    h = hexcol.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return unreal.LinearColor(c[0], c[1], c[2], 1.0)


def fresh_material(name):
    path = MATDEST + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.load_asset(path)
        mel.delete_all_material_expressions(mat)
        return mat
    return asset_tools.create_asset(name, MATDEST, unreal.Material, unreal.MaterialFactoryNew())


def c3(mat, col, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, x, y)
    e.set_editor_property("constant", lin(col))
    return e


def c1(mat, v, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, x, y)
    e.set_editor_property("r", v)
    return e


def mask(mat, src, ch, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, x, y)
    for c in "rgba":
        e.set_editor_property(c, c == ch)
    mel.connect_material_expressions(src, "", e, "")
    return e


def link(src, dst, names):
    for n in names:
        if mel.connect_material_expressions(src, "", dst, n):
            return True
    log("WARNING: could not connect material input %s" % names[0])
    return False


def if_node(mat, a, b, gt, eq, lt, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionIf, x, y)
    link(a, e, ["A"])
    link(b, e, ["B"])
    link(gt, e, ["A > B", "AGreaterThanB", "A>B"])
    link(eq, e, ["A == B", "AEqualsB", "A=B", "A==B"])
    link(lt, e, ["A < B", "ALessThanB", "A<B"])
    return e


def finish(mat):
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def flat_material(name, col, rough):
    mat = fresh_material(name)
    mel.connect_material_property(c3(mat, col, -400, 0), "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(c1(mat, rough, -400, 200), "", unreal.MaterialProperty.MP_ROUGHNESS)
    return finish(mat)


def wall_material(floor_z):
    """Plain cream paint. (The slate lower band is real geometry, see Wainscot.)"""
    return flat_material("M_80s_WallTwoTone", "#D8CEB6", 0.85)


def ceiling_material(tiles_u, tiles_v):
    """Acoustic tile texture repeated across the ceiling's UVs (no world-position math)."""
    tex_path = "/Game/Office80s/Textures/T_80s_CeilingTile"
    task = unreal.AssetImportTask()
    task.filename = os.path.join(src_dir(), "T_80s_CeilingTile.png")
    task.destination_path = "/Game/Office80s/Textures"
    task.automated = True
    task.replace_existing = True
    task.save = True
    asset_tools.import_asset_tasks([task])
    tex = None
    for p in unreal.EditorAssetLibrary.list_assets("/Game/Office80s/Textures", recursive=True):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.Texture2D) and "CeilingTile" in a.get_name():
            tex = a
    mat = fresh_material("M_80s_CeilingTile")
    if tex is None:
        log("WARNING: ceiling texture missing, using flat color")
        mel.connect_material_property(c3(mat, "#E6E2D6", -400, 0), "", unreal.MaterialProperty.MP_BASE_COLOR)
    else:
        uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 0)
        uv.set_editor_property("u_tiling", float(tiles_u))
        uv.set_editor_property("v_tiling", float(tiles_v))
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -450, 0)
        ts.set_editor_property("texture", tex)
        mel.connect_material_expressions(uv, "", ts, "UVs")
        mel.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(c1(mat, 0.95, -400, 300), "", unreal.MaterialProperty.MP_ROUGHNESS)
    return finish(mat)


# ------------------------------------------------------------------ geometry
class OBox:
    def __init__(self, a):
        comp = a.static_mesh_component
        b = comp.static_mesh.get_bounding_box()
        s = a.get_actor_scale3d()
        e = b.max - b.min
        self.sx, self.sy, self.sz = abs(e.x * s.x), abs(e.y * s.y), abs(e.z * s.z)
        self.center = a.get_actor_transform().transform_location((b.min + b.max) * 0.5)
        r = a.get_actor_rotation()
        self.yaw = r.yaw
        self.fwd = unreal.Rotator(0, 0, r.yaw).get_forward_vector()
        self.right = unreal.Rotator(0, 0, r.yaw).get_right_vector()
        self.bottom = self.center.z - self.sz / 2
        self.top = self.center.z + self.sz / 2
        self.actor = a
        self.scale = s

    def local(self, p):
        d = p - self.center
        return d.dot(self.fwd), d.dot(self.right)


def V(x, y, z=0.0):
    return unreal.Vector(x, y, z)


def yaw_facing(n):
    """yaw that points a model's front (-Y) along direction n"""
    return math.degrees(math.atan2(n.x, -n.y))


EAST, WEST, NORTH, SOUTH = V(1, 0), V(-1, 0), V(0, 1), V(0, -1)


def rect_aabb(center, yaw, mn, mx, margin=0.0):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    xs, ys = [], []
    for lx in (mn[0], mx[0]):
        for ly in (mn[1], mx[1]):
            xs.append(center.x + lx * c - ly * s)
            ys.append(center.y + lx * s + ly * c)
    return (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def grow(b, m):
    return (b[0] - m, b[1] - m, b[2] + m, b[3] + m)


def in_rect(p, r, pad=0.0):
    return r[0] - pad <= p.x <= r[2] + pad and r[1] - pad <= p.y <= r[3] + pad


def room_of(p):
    for k, r in ROOMS.items():
        if in_rect(p, r):
            return k
    return None


SKIP_CLASSES = ("GroupActor", "WorldDataLayers", "PostProcessVolume", "SkyAtmosphere", "SkyLight", "VolumetricCloud",
                "WorldPartitionMiniMap", "DirectionalLight", "RectLight", "PointLight", "SpotLight", "ExponentialHeightFog")


# ------------------------------------------------------------------ main
def run():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world.get_name() != "Office":
        raise RuntimeError("Open the Office map first")

    all_actors = actor_sub.get_all_level_actors()
    old = [a for a in all_actors if str(a.get_folder_path()).startswith(FOLDER)]
    fills_done = any(str(a.get_folder_path()).startswith(FILLS) for a in all_actors)

    floor_z, floor_box = 20.0, None
    walls, ceiling, desks, panels, lights = [], None, [], [], []
    obstacles, gameplay, slab = [], [], None
    for a in all_actors:
        if a in old:
            continue
        cls = a.get_class().get_name()
        label = a.get_actor_label()
        if isinstance(a, unreal.RectLight):
            lights.append(a.get_actor_location())
            continue
        if cls in SKIP_CLASSES:
            continue
        o, e = a.get_actor_bounds(False)
        aabb = (o.x - e.x, o.y - e.y, o.x + e.x, o.y + e.y)
        zmin, zmax = o.z - e.z, o.z + e.z
        if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
            mpath = a.static_mesh_component.static_mesh.get_path_name()
            if mpath.endswith("SM_Plane.SM_Plane") and e.x > 1000:
                floor_z, floor_box = zmax, aabb
                continue
            if label == RECEPTION_SLAB:
                slab = OBox(a)
                continue
            if label.startswith("Desk80s_"):
                desks.append(OBox(a))
            elif label.startswith("CubiclePanel80s_"):
                panels.append(OBox(a))
            elif mpath.startswith("/Game/LevelPrototyping/Meshes/SM_Cube."):
                ob = OBox(a)
                if ob.sz < 150 and ob.sx > 1000 and ob.sy > 1000:
                    if ob.bottom > 500:
                        ceiling = ob
                    continue
                if ob.sz >= 300 or ob.bottom >= 300:
                    walls.append(ob)
        else:
            gameplay.append(aabb)
        if zmax > floor_z + 5 and zmin < floor_z + 400:
            obstacles.append((a, aabb))
    if floor_box is None:
        raise RuntimeError("couldn't find the floor plane")

    def in_floor(p):
        return floor_box[0] + 30 < p.x < floor_box[2] - 30 and floor_box[1] + 30 < p.y < floor_box[3] - 30

    def free(box, extra=(), ignore=(), gp_margin=GAMEPLAY_CLEARANCE):
        for a, b in obstacles:
            if a not in ignore and overlaps(box, b):
                return False
        if any(overlaps(box, b) for b in extra):
            return False
        return not any(overlaps(box, grow(g, gp_margin)) for g in gameplay)

    chair = find_mesh("/Game/Office80s/Meshes/SM_OfficeChair80s")
    cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    count = {}

    def spawn(m, loc, yaw, sub, scale=None, collide=True, mat=None, folder=FOLDER):
        a = actor_sub.spawn_actor_from_object(m, loc, unreal.Rotator(0, 0, yaw))
        if scale:
            a.set_actor_scale3d(scale)
        count[sub] = count.get(sub, 0) + 1
        a.set_actor_label("%s_%03d" % (sub, count[sub]))
        a.set_folder_path(folder + "/" + sub)
        c = a.static_mesh_component
        c.set_mobility(unreal.ComponentMobility.STATIC)
        if not collide:
            c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        if mat:
            c.set_material(0, mat)
        return a

    placed = []

    def put(short, x, y, n, sub=None, z=None, collide=None, yaw_extra=0.0, folder=FOLDER, check=True):
        """Place SM_80s_<short> with its front facing n. Floor props are checked against
        gameplay actors so a hard-coded spot never lands on a monster or task item."""
        mn, mx = size_of(short)
        yaw = yaw_facing(n) + yaw_extra
        p = V(x, y, floor_z if z is None else z)
        is_decor = short in DECOR
        box = rect_aabb(p, yaw, mn, mx)
        if check and not is_decor and any(overlaps(box, grow(g, 25)) for g in gameplay):
            log("skipped %s at (%.0f, %.0f): too close to a gameplay actor" % (short, x, y))
            return None
        a = spawn(mesh(short), p, yaw, sub or short, collide=(not is_decor) if collide is None else collide, folder=folder)
        if not is_decor:
            placed.append(box)
        return a

    def against(short, face, n, along, sub=None, z=None, gap=5.0, **kw):
        """Floor prop with its back to a wall. face = wall coordinate, n = direction into the room."""
        mn, mx = size_of(short)
        d = gap + mx[1]
        if abs(n.x) > 0.5:
            return put(short, face + n.x * d, along, n, sub, z, **kw)
        return put(short, along, face + n.y * d, n, sub, z, **kw)

    def on_wall(short, face, n, along, height, sub=None):
        """Wall-hung piece (back plane at the wall)."""
        if abs(n.x) > 0.5:
            return put(short, face + n.x * 0.5, along, n, sub, floor_z + height)
        return put(short, along, face + n.y * 0.5, n, sub, floor_z + height)

    with unreal.ScopedEditorTransaction("Add 80s office life"):
        if old:
            actor_sub.destroy_actors(old)

        # ============================================================ surfaces
        m_wall = wall_material(floor_z)
        m_ceil = ceiling_material(ceiling.sx / 81.0, ceiling.sy / 81.0) if ceiling else None
        m_wain = flat_material("M_80s_Wainscot", "#56656E", 0.8)
        m_rail = flat_material("M_80s_WoodTrim", "#5B3B23", 0.45)
        m_base = flat_material("M_80s_Baseboard", "#2B2622", 0.6)
        for w in walls:
            w.actor.static_mesh_component.set_material(0, m_wall)
        if ceiling:
            ceiling.actor.static_mesh_component.set_material(0, m_ceil)

        faces = []
        for w in walls:
            if w.bottom > floor_z + 30:
                continue
            if w.sx >= w.sy:
                axis, L, T, nrm = w.fwd, w.sx, w.sy, w.right
            else:
                axis, L, T, nrm = w.right, w.sy, w.sx, w.fwd
            for s in (1.0, -1.0):
                n = nrm * s
                fc = w.center + n * (T / 2)
                probe = fc + n * 60
                if not in_floor(probe):
                    continue
                if any(o is not w and abs(o.local(probe)[0]) < o.sx / 2 and abs(o.local(probe)[1]) < o.sy / 2 for o in walls):
                    continue
                faces.append((w, axis, L, n, fc))
        for w, axis, L, n, fc in faces:
            yaw = math.degrees(math.atan2(axis.y, axis.x))
            for zc, h, d, mat, sub in ((floor_z + RAIL / 2, RAIL, 1.0, m_wain, "Wainscot"),
                                       (floor_z + 8, 16, 2.0, m_base, "Baseboard"), (floor_z + RAIL, 7, 3.0, m_rail, "ChairRail")):
                p = fc + n * (d / 2)
                spawn(cube, V(p.x, p.y, zc), yaw, sub, unreal.Vector(L / 100, d / 100, h / 100), False, mat)
        if ceiling:
            for lp in lights:
                put("CeilingLight", lp.x, lp.y, SOUTH, z=ceiling.bottom)

        # ============================================================ cubicle conversions (one time)
        main_desks = [d for d in desks if room_of(d.center) is None]
        converted = []
        if not fills_done and main_desks:
            pool = sorted(main_desks, key=lambda d: (round(d.center.y / 400), d.center.x))
            chosen = []
            for d in rng.sample(pool, len(pool)):
                if len(chosen) >= CONVERT_DESKS:
                    break
                if all((d.center - c.center).length() > 420 for c in chosen):
                    chosen.append(d)
            kinds = ["meeting", "supply", "coffee", "storage"]
            for i, d in enumerate(chosen):
                kind = kinds[i % len(kinds)]
                s = d.scale
                Ld, Dd = 175 * s.x, 100 * s.y
                front = d.right * -1.0
                back = d.right
                base = V(d.center.x, d.center.y, floor_z)
                ign = (d.actor,)

                def fit(short, pos, facing, extra_yaw=0.0):
                    mn, mx = size_of(short)
                    yaw = yaw_facing(facing) + extra_yaw
                    box = rect_aabb(pos, yaw, mn, mx, 3)
                    if free(box, placed, ign, gp_margin=40) and in_floor(pos):
                        spawn(mesh(short), V(pos.x, pos.y, floor_z), yaw, short, folder=FILLS)
                        placed.append(box)
                        return True
                    return False

                def back_pos(short, along=0.0):
                    mn, mx = size_of(short)
                    return base + back * (Dd / 2 - mx[1]) + d.fwd * along

                if kind == "meeting":
                    tp = base + front * 35
                    fit("RoundTable", tp, front)
                    for k, dirv in enumerate((front, d.fwd, d.fwd * -1.0, back)):
                        cp = tp + dirv * 100
                        cmn, cmx = (-35, -40), (42, 40)
                        yaw = yaw_facing(dirv * -1.0) + rng.uniform(-20, 20)
                        box = rect_aabb(cp, yaw, cmn, cmx, 3)
                        if k < 3 and free(box, placed, ign, gp_margin=40):
                            spawn(chair, V(cp.x, cp.y, floor_z), yaw, "Chair", folder=FILLS)
                            placed.append(box)
                elif kind == "supply":
                    fit("FileBank", back_pos("FileBank", -Ld / 2 + 76), front)
                    fit("BoxStack", back_pos("BoxStack", Ld / 2 - 40), front, rng.uniform(-10, 10))
                    fit("SnakePlant", base + front * 40 + d.fwd * (Ld / 2 + 10), front)
                elif kind == "coffee":
                    fit("CoffeeStation", back_pos("CoffeeStation", -30), front)
                    fit("WaterCooler", back_pos("WaterCooler", 85), front)
                    fit("Wastebasket", base + front * 20 + d.fwd * (-Ld / 2 + 10), front)
                else:  # storage
                    fit("BoxStack", back_pos("BoxStack", -40), front, rng.uniform(-15, 15))
                    fit("FileCabinet4", back_pos("FileCabinet4", 60), front)
                    fit("CoatRack", base + front * 50 + d.fwd * (Ld / 2), front)
                converted.append(d)
            if converted:
                for d in converted:
                    desks.remove(d)
                actor_sub.destroy_actors([d.actor for d in converted])
                obstacles[:] = [(a, b) for a, b in obstacles if a not in [d.actor for d in converted]]
            log("converted %d desks into other cubicle uses" % len(converted))

        # ============================================================ desk dressing
        for d in desks:
            s = d.scale
            Ld, Dd, Hd = 175 * s.x, 100 * s.y, 99 * s.z
            front = d.right * -1.0
            base = V(d.center.x, d.center.y, floor_z)
            cp = base + front * (Dd / 2 + rng.uniform(22, 48)) + d.fwd * rng.uniform(-20, 20)
            spawn(chair, cp, d.yaw + 180 + rng.uniform(-28, 28), "Chair")
            side = rng.choice((-1, 1))
            bp = base + front * (Dd / 2 + 22) + d.fwd * (side * (Ld / 2 - 20))
            put("Wastebasket", bp.x, bp.y, front, yaw_extra=rng.uniform(0, 360), check=False)
            if rng.random() < 0.5:
                mn, mx = size_of("FileCabinet2")
                for sd in (-side, side):
                    fp = base + d.fwd * (sd * (Ld / 2 + 34)) - front * (Dd / 2 - mx[1])
                    box = rect_aabb(fp, d.yaw, mn, mx, 3)
                    if free(box, placed, gp_margin=40) and in_floor(fp):
                        spawn(mesh("FileCabinet2"), fp, d.yaw, "DeskFile")
                        placed.append(box)
                        break
            probe = d.center - front * (Dd / 2 + 15)
            best = None
            for p in panels:
                if abs(p.right.dot(front)) < 0.95 or p.sx < 150:
                    continue
                lx, ly = p.local(probe)
                if abs(lx) > p.sx / 2 or abs(ly) > p.sy / 2 + 120:
                    continue
                if best is None or abs(ly) < abs(best[1]):
                    best = (p, ly)
            if best and rng.random() < 0.85:
                p = best[0]
                n = p.right * (1.0 if (d.center - p.center).dot(p.right) > 0 else -1.0)
                lx = max(-p.sx / 2 + 85, min(p.sx / 2 - 85, p.local(d.center)[0]))
                q = p.center + p.fwd * lx + n * (p.sy / 2 + 0.3)
                spawn(mesh(rng.choice(["CubiclePinup_A", "CubiclePinup_B", "CubiclePinup_C"])),
                      V(q.x, q.y, floor_z + Hd + 80), yaw_facing(n), "Pinup", collide=False)

        # ============================================================ themed rooms
        # --- reception: real counter instead of the slab, waiting area by the west wall
        if slab:
            rc = (slab.center.x, slab.center.y, slab.sx, slab.sy, slab.top)
        else:
            rc = REC_FALLBACK
        cx, cy, sx, sy, top = rc
        long_, deep = max(sx, sy), min(sx, sy)
        scale = unreal.Vector(long_ / 1218.0, deep / 513.0, (top - floor_z) / 148.0)
        spawn(mesh("ReceptionCounter"), V(cx, cy, floor_z), yaw_facing(WEST), "ReceptionCounter", scale=scale)
        if slab:
            actor_sub.destroy_actor(slab.actor)
        on_wall("LogoSign", 2070, WEST, cy, 330)
        for y in (-4720, -4080):
            against("WaitingChairs", 730, EAST, y)
        put("RugLobby", 905, -4400, EAST)
        put("CoffeeTable", 905, -4400, EAST)
        against("Ficus", 730, EAST, -3700, gap=20)
        against("SnakePlant", 730, EAST, -5000, gap=10)
        against("WaterCooler", 730, EAST, -3480)
        on_wall("WallClock", 730, EAST, -4400, 330)
        on_wall("Poster_Teamwork", 730, EAST, -3700, 290)

        # --- janitor closet (keep the doorway on the north side clear)
        J = ROOMS["janitor"]
        against("MetalShelf", J[2], WEST, -4180)
        against("MetalShelf", J[2], WEST, -5300)
        against("UtilitySink", J[1], NORTH, 5200)
        against("MetalShelf", J[0], EAST, -4250)
        against("FileCabinet4", J[2], WEST, -4450)
        against("Brooms", J[0], EAST, -5450)
        against("BoxStack", J[0], EAST, -5200, yaw_extra=8)
        put("MopBucket", 5080, -4330, EAST, yaw_extra=25)
        put("WetFloorSign", 5180, -4060, NORTH, yaw_extra=-20)

        # --- boss office: desk between the door and the boss, who sits on the east side
        B = ROOMS["boss"]
        # the boss stands at ~(6360, 1550); his desk sits right in front of him
        put("RugBoss", 6150, 1550, EAST)
        put("ExecDesk", 6200, 1550, EAST, check=False)
        put("ExecChair", 6305, 1530, WEST, collide=False, check=False, yaw_extra=15)
        for y in (1430, 1670):
            put("GuestChair", 5990, y, EAST, yaw_extra=rng.uniform(-12, 12), check=False)
        # small sitting area by the south wall
        put("CoffeeTable", 6350, 720, NORTH)
        put("GuestChair", 6100, 720, EAST, yaw_extra=-10)
        put("GuestChair", 6600, 720, WEST, yaw_extra=10)
        against("Bookshelf", B[3], SOUTH, 6250)
        against("Bookshelf", B[3], SOUTH, 6420)
        against("Credenza", B[2], WEST, 1550)
        on_wall("Painting", B[2], WEST, 1550, 330)
        put("Globe", 6850, 2450, WEST)
        against("Ficus", B[3], SOUTH, 6900, gap=20)
        against("Ficus", B[1], NORTH, 6900, gap=20)
        put("CoatRack", 5610, 950, EAST)
        on_wall("WallClock", B[1], NORTH, 5900, 330)

        # --- break room
        R = ROOMS["break"]
        against("Kitchenette", R[2], WEST, -1300)
        against("Fridge", R[2], WEST, -1650)
        against("VendingMachine", R[3], SOUTH, 6500)
        put("BreakTable", 6380, -380, NORTH)
        for dx in (-55, 55):
            put("StackChair", 6380 + dx, -380 + 88, SOUTH, yaw_extra=rng.uniform(-15, 15))
            put("StackChair", 6380 + dx, -380 - 88, NORTH, yaw_extra=rng.uniform(-15, 15))
        against("SnakePlant", R[3], SOUTH, 5620, gap=15)
        put("BreakTable", 6500, -1650, NORTH)
        for dx in (-55, 55):
            put("StackChair", 6500 + dx, -1650 + 88, SOUTH, yaw_extra=rng.uniform(-15, 15))
            put("StackChair", 6500 + dx, -1650 - 88, NORTH, yaw_extra=rng.uniform(-15, 15))
        against("Ficus", R[1], NORTH, 5620, gap=20)
        against("WaterCooler", R[3], SOUTH, 5900)
        against("CoatRack", R[0], EAST, -1300)
        against("Wastebasket", R[2], WEST, -900)
        on_wall("BulletinBoard", R[1], NORTH, 6300, 280)
        on_wall("WallClock", R[3], SOUTH, 6100, 330)

        # --- conference room
        C = ROOMS["conference"]
        put("ConfTable", 4400, 2200, SOUTH)
        for x in (4250, 4400, 4550):
            spawn(chair, V(x + rng.uniform(-10, 10), 2200 + 128, floor_z), yaw_facing(SOUTH) + rng.uniform(-15, 15), "Chair")
            spawn(chair, V(x + rng.uniform(-10, 10), 2200 - 128, floor_z), yaw_facing(NORTH) + rng.uniform(-15, 15), "Chair")
        spawn(chair, V(4400 + 258, 2200, floor_z), yaw_facing(WEST), "Chair")
        spawn(chair, V(4400 - 258, 2200, floor_z), yaw_facing(EAST), "Chair")
        on_wall("Whiteboard", C[2], WEST, 2200, 250)
        against("CoffeeStation", C[0], EAST, 2450)
        against("Credenza", C[3], SOUTH, 4400)
        against("Bookshelf", C[0], EAST, 2000)
        against("Ficus", C[3], SOUTH, 3600, gap=20)
        against("Ficus", C[3], SOUTH, 5340, gap=20)
        against("SnakePlant", C[3], SOUTH, 3050, gap=15)
        on_wall("WallClock", C[3], SOUTH, 4400, 340)

        # desks + converted cubicles count as obstacles for the wall pass
        for d in desks + converted:
            c = d.center + d.right * -60.0
            placed.append((min(d.center.x, c.x) - 160, min(d.center.y, c.y) - 160, max(d.center.x, c.x) + 160, max(d.center.y, c.y) + 160))

        # ============================================================ light scattering along other walls
        generic = list(faces)
        rng.shuffle(generic)
        weights = [("FileBank", 4), ("FileCabinet4", 2), ("Ficus", 3), ("SnakePlant", 2), ("WaterCooler", 1), ("Copier", 1.2), ("CoatRack", 1)]
        caps = {"WaterCooler": 2, "Copier": 2, "CoatRack": 3}
        used = {}
        for w, axis, L, n, fc in generic:
            t = -L / 2 + 150
            while t < L / 2 - 150:
                if rng.random() < 0.35:
                    pool = [(k, wt) for k, wt in weights if used.get(k, 0) < caps.get(k, 99)]
                    r = rng.uniform(0, sum(wt for _, wt in pool))
                    for name, wt in pool:
                        r -= wt
                        if r <= 0:
                            break
                    mn, mx = size_of(name)
                    width = mx[0] - mn[0]
                    pos = fc + axis * t + n * (5 + mx[1])
                    yaw = yaw_facing(n)
                    box = rect_aabb(pos, yaw, mn, mx)
                    if abs(t) + width / 2 < L / 2 - 90 and in_floor(pos) and room_of(pos) is None and free(rect_aabb(pos, yaw, mn, mx, CLEARANCE), placed, (w.actor,)):
                        spawn(mesh(name), V(pos.x, pos.y, floor_z), yaw + (rng.uniform(0, 360) if name in ("Ficus", "SnakePlant") else 0), name)
                        placed.append(box)
                        used[name] = used.get(name, 0) + 1
                        t += width + 150
                        continue
                t += 220

        # sparse wall decor: at most one piece per ~8 m of wall, never two close together
        decor_w = [("Poster_Sunset", 3), ("Poster_Memphis", 3), ("Poster_Teamwork", 2), ("BulletinBoard", 1), ("WallClock", 1)]
        decor_boxes = []
        clocks = 0
        for w, axis, L, n, fc in generic:
            slots = max(0, int((L - 300) // 800))
            for k in range(slots):
                if rng.random() > 0.5:
                    continue
                t = -L / 2 + 150 + (k + 0.5) * (L - 300) / slots + rng.uniform(-80, 80)
                pool = [(nm, wt) for nm, wt in decor_w if not (nm == "WallClock" and clocks >= 2)]
                r = rng.uniform(0, sum(wt for _, wt in pool))
                for name, wt in pool:
                    r -= wt
                    if r <= 0:
                        break
                mn, mx = size_of(name)
                pos = fc + axis * t + n * 0.5
                box = rect_aabb(pos, yaw_facing(n), mn, (mx[0], 40, mx[2]), 300)
                if abs(t) + (mx[0] - mn[0]) / 2 < L / 2 - 60 and room_of(pos + n * 30) is None and not any(overlaps(box, b) for b in decor_boxes):
                    spawn(mesh(name), V(pos.x, pos.y, floor_z + (300 if name == "WallClock" else 280)), yaw_facing(n), name, collide=False)
                    decor_boxes.append(box)
                    clocks += name == "WallClock"

    log("office life added: " + ", ".join("%s %d" % kv for kv in sorted(count.items())))


run()
