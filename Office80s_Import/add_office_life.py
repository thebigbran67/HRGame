"""
HRGame / Office: dress the level so it reads as a real 1980s office.
Run AFTER replace_blockout_80s.py, with the Office map open:
    py "C:/Users/rbrannig/Documents/GitHub/HRGame/Office80s_Import/add_office_life.py"

Adds (all under the Outliner folder Office80s/Life, one undo step):
  - two-tone painted walls with a wood chair rail and baseboard, acoustic-tile ceiling
  - fluorescent fixtures under every ceiling RectLight (no new lights)
  - per desk: swivel chair, wastebasket, sometimes a 2-drawer file, papers pinned on the cubicle wall
  - along the walls: file cabinet banks, plants, water coolers, copiers, coat racks
  - on the walls: posters, bulletin boards, clocks
Props keep ~1m of clearance from cubicles/desks/each other and ~2m from doors, monsters,
trash bags/drop-off and the player start. Safe to run again: it clears its own previous output first.
"""
import os, math, json, random
import unreal

SEED = 1987
FOLDER = "Office80s/Life"
DEST = "/Game/Office80s/Props"
MATDEST = "/Game/Office80s/Materials"
RAIL_Z_ABOVE_FLOOR = 135.0       # where the wall color changes / chair rail sits
WALL_PROP_CHANCE = 0.5
WALL_DECOR_CHANCE = 0.6
CLEARANCE = 100.0                # walkway kept free around floor props
GAMEPLAY_CLEARANCE = 200.0       # extra room around blueprints / player start

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


SIZES = json.load(open(os.path.join(src_dir(), "life_sizes.json")))


# ------------------------------------------------------------------ assets
def import_mesh(name, collision=True):
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
    if collision:
        sub.add_simple_collisions(sm, unreal.ScriptCollisionShapeType.BOX)
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
    return sm


def lin(hexcol):
    h = hexcol.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return unreal.LinearColor(c[0], c[1], c[2], 1.0)


def new_material(name):
    path = MATDEST + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path), False
    return asset_tools.create_asset(name, MATDEST, unreal.Material, unreal.MaterialFactoryNew()), True


def const3(mat, col, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, x, y)
    e.set_editor_property("constant", lin(col))
    return e


def const1(mat, v, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, x, y)
    e.set_editor_property("r", v)
    return e


def mask(mat, src, ch, x, y):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, x, y)
    for c in "rgba":
        e.set_editor_property(c, c == ch)
    mel.connect_material_expressions(src, "", e, "")
    return e


def flat_material(name, col, rough):
    mat, fresh = new_material(name)
    if fresh:
        mel.connect_material_property(const3(mat, col, -400, 0), "", unreal.MaterialProperty.MP_BASE_COLOR)
        mel.connect_material_property(const1(mat, rough, -400, 200), "", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def wall_material(floor_z):
    mat, fresh = new_material("M_80s_WallTwoTone")
    if fresh:
        wp = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -900, 0)
        z = mask(mat, wp, "b", -700, 0)
        cmp = mel.create_material_expression(mat, unreal.MaterialExpressionIf, -400, 0)
        cmp.set_editor_property("const_b", floor_z + RAIL_Z_ABOVE_FLOOR)
        mel.connect_material_expressions(z, "", cmp, "A")
        upper = const3(mat, "#D8CEB6", -700, 200)   # cream paint
        lower = const3(mat, "#56656E", -700, 350)   # slate blue-gray wainscot
        mel.connect_material_expressions(upper, "", cmp, "AGreaterThanB")
        mel.connect_material_expressions(upper, "", cmp, "AEqualsB")
        mel.connect_material_expressions(lower, "", cmp, "ALessThanB")
        mel.connect_material_property(cmp, "", unreal.MaterialProperty.MP_BASE_COLOR)
        mel.connect_material_property(const1(mat, 0.82, -400, 300), "", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def ceiling_material():
    mat, fresh = new_material("M_80s_CeilingTile")
    if fresh:
        wp = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -1200, 0)
        lines = []
        for i, ch in enumerate("rg"):
            m = mask(mat, wp, ch, -1000, i * 200)
            dv = mel.create_material_expression(mat, unreal.MaterialExpressionDivide, -850, i * 200)
            dv.set_editor_property("const_b", 81.0)  # 2ft tiles at this level's scale
            mel.connect_material_expressions(m, "", dv, "A")
            fr = mel.create_material_expression(mat, unreal.MaterialExpressionFrac, -700, i * 200)
            mel.connect_material_expressions(dv, "", fr, "")
            ifn = mel.create_material_expression(mat, unreal.MaterialExpressionIf, -550, i * 200)
            ifn.set_editor_property("const_b", 0.03)
            mel.connect_material_expressions(fr, "", ifn, "A")
            one, zero = const1(mat, 1.0, -700, 500 + i * 100), const1(mat, 0.0, -700, 550 + i * 100)
            mel.connect_material_expressions(one, "", ifn, "ALessThanB")
            mel.connect_material_expressions(zero, "", ifn, "AGreaterThanB")
            mel.connect_material_expressions(zero, "", ifn, "AEqualsB")
            lines.append(ifn)
        mx = mel.create_material_expression(mat, unreal.MaterialExpressionMax, -400, 100)
        mel.connect_material_expressions(lines[0], "", mx, "A")
        mel.connect_material_expressions(lines[1], "", mx, "B")
        lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -250, 0)
        mel.connect_material_expressions(const3(mat, "#E6E2D6", -400, -150), "", lerp, "A")   # tile
        mel.connect_material_expressions(const3(mat, "#9C988C", -400, -250), "", lerp, "B")   # grid
        mel.connect_material_expressions(mx, "", lerp, "Alpha")
        mel.connect_material_property(lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
        mel.connect_material_property(const1(mat, 0.95, -250, 250), "", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


# ------------------------------------------------------------------ geometry helpers
class OBox:
    """Oriented box of a static mesh actor (yaw only)."""
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

    def local(self, p):
        d = p - self.center
        return d.dot(self.fwd), d.dot(self.right)


def vec(x, y, z=0.0):
    return unreal.Vector(x, y, z)


def yaw_facing(n):
    """yaw that turns a model's front (-Y) to point along n"""
    return math.degrees(math.atan2(n.x, -n.y))


def rect_aabb(center, yaw, mn, mx, margin=0.0):
    """world AABB (xy) of a model footprint [mn,mx] (local) placed at center with yaw"""
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    xs, ys = [], []
    for lx in (mn[0], mx[0]):
        for ly in (mn[1], mx[1]):
            xs.append(center.x + lx * c - ly * s)
            ys.append(center.y + lx * s + ly * c)
    return (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


SKIP_CLASSES = ("GroupActor", "WorldDataLayers", "PostProcessVolume", "SkyAtmosphere", "SkyLight", "VolumetricCloud",
                "WorldPartitionMiniMap", "DirectionalLight", "RectLight", "PointLight", "SpotLight", "ExponentialHeightFog")


# ------------------------------------------------------------------ main
def run():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world.get_name() != "Office":
        raise RuntimeError("Open the Office map first")

    all_actors = actor_sub.get_all_level_actors()
    old = [a for a in all_actors if str(a.get_folder_path()).startswith(FOLDER)]

    floor_z, floor_box = 20.0, None
    walls, ceiling, desks, panels, lights = [], None, [], [], []
    obstacles, gameplay = [], []
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
            if label.startswith("Desk80s_"):
                desks.append(OBox(a))
            elif label.startswith("CubiclePanel80s_"):
                panels.append(OBox(a))
            elif mpath.startswith("/Game/LevelPrototyping/Meshes/SM_Cube."):
                ob = OBox(a)
                if ob.sz < 150 and ob.sx > 1000 and ob.sy > 1000:
                    if ob.bottom > 500:
                        ceiling = ob
                    continue          # floor slab / ceiling: not obstacles
                if ob.sz >= 300 or ob.bottom >= 300:
                    walls.append(ob)
        else:
            gameplay.append(aabb)    # blueprints, player start, volumes etc.
        if zmax > floor_z + 5 and zmin < floor_z + 400:
            obstacles.append((a, aabb))
    if floor_box is None:
        raise RuntimeError("couldn't find the floor plane")
    log("walls %d, desks %d, panels %d, ceiling lights %d" % (len(walls), len(desks), len(panels), len(lights)))

    def in_room(p):
        return floor_box[0] + 30 < p.x < floor_box[2] - 30 and floor_box[1] + 30 < p.y < floor_box[3] - 30

    def free(box, extra=(), ignore=None):
        for a, b in obstacles:
            if a != ignore and overlaps(box, b):
                return False
        for b in extra:
            if overlaps(box, b):
                return False
        for g in gameplay:
            gg = (g[0] - GAMEPLAY_CLEARANCE, g[1] - GAMEPLAY_CLEARANCE, g[2] + GAMEPLAY_CLEARANCE, g[3] + GAMEPLAY_CLEARANCE)
            if overlaps(box, gg):
                return False
        return True

    # ---------------- assets
    prop_names = ["SM_80s_FileBank", "SM_80s_FileCabinet4", "SM_80s_FileCabinet2", "SM_80s_Wastebasket",
                  "SM_80s_WaterCooler", "SM_80s_Ficus", "SM_80s_SnakePlant", "SM_80s_CoatRack", "SM_80s_Copier"]
    decor_names = ["SM_80s_Poster_Sunset", "SM_80s_Poster_Memphis", "SM_80s_Poster_Teamwork", "SM_80s_WallClock",
                   "SM_80s_BulletinBoard", "SM_80s_CubiclePinup_A", "SM_80s_CubiclePinup_B", "SM_80s_CubiclePinup_C",
                   "SM_80s_CeilingLight"]
    M = {}
    for n in prop_names:
        M[n] = import_mesh(n, True)
    for n in decor_names:
        M[n] = import_mesh(n, False)
    chair = None
    for p in unreal.EditorAssetLibrary.list_assets("/Game/Office80s/Meshes/SM_OfficeChair80s", recursive=True):
        if isinstance(unreal.load_asset(p), unreal.StaticMesh):
            chair = unreal.load_asset(p)
    if chair is None:
        raise RuntimeError("Chair mesh missing; run replace_blockout_80s.py first")
    cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    m_wall = wall_material(floor_z)
    m_ceil = ceiling_material()
    m_rail = flat_material("M_80s_WoodTrim", "#5B3B23", 0.45)
    m_base = flat_material("M_80s_Baseboard", "#2B2622", 0.6)

    count = {}

    def spawn(mesh, loc, yaw, sub, scale=None, collide=True, mat=None):
        a = actor_sub.spawn_actor_from_object(mesh, loc, unreal.Rotator(0, 0, yaw))
        if scale:
            a.set_actor_scale3d(scale)
        count[sub] = count.get(sub, 0) + 1
        a.set_actor_label("%s_%03d" % (sub, count[sub]))
        a.set_folder_path(FOLDER + "/" + sub)
        c = a.static_mesh_component
        c.set_mobility(unreal.ComponentMobility.STATIC)
        if not collide:
            c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            c.set_editor_property("can_character_step_up_on", unreal.CanBeCharacterBase.ECB_NO)
        if mat:
            c.set_material(0, mat)
        return a

    def size_of(n):
        s = SIZES[n]
        return s["min"], s["max"]

    placed = []   # AABBs of new floor props

    with unreal.ScopedEditorTransaction("Add 80s office life"):
        if old:
            actor_sub.destroy_actors(old)

        # ---------------- surfaces
        for w in walls:
            w.actor.static_mesh_component.set_material(0, m_wall)
        if ceiling:
            ceiling.actor.static_mesh_component.set_material(0, m_ceil)

        # wall faces that look into the office
        faces = []
        for w in walls:
            if w.bottom > floor_z + 30:
                continue                         # header above a doorway
            if w.sx >= w.sy:
                axis, L, T, nrm = w.fwd, w.sx, w.sy, w.right
            else:
                axis, L, T, nrm = w.right, w.sy, w.sx, w.fwd
            for s in (1.0, -1.0):
                n = nrm * s
                face_c = w.center + n * (T / 2)
                probe = face_c + n * 60
                if not in_room(probe):
                    continue
                if any(o is not w and abs(o.local(probe)[0]) < o.sx / 2 and abs(o.local(probe)[1]) < o.sy / 2 for o in walls):
                    continue
                faces.append((w, axis, L, n, face_c))

        # trim along each face
        for w, axis, L, n, fc in faces:
            yaw = math.degrees(math.atan2(axis.y, axis.x))
            for zc, h, d, mat, sub in ((floor_z + 8, 16, 2.0, m_base, "Baseboard"),
                                       (floor_z + RAIL_Z_ABOVE_FLOOR, 7, 3.0, m_rail, "ChairRail")):
                p = fc + n * (d / 2)
                spawn(cube, vec(p.x, p.y, zc), yaw, sub, unreal.Vector(L / 100, d / 100, h / 100), False, mat)

        # ---------------- ceiling fixtures
        if ceiling:
            for lp in lights:
                spawn(M["SM_80s_CeilingLight"], vec(lp.x, lp.y, ceiling.bottom), 0.0, "CeilingLight", collide=False)

        # ---------------- desks: chair, bin, side file, pin-ups
        for d in desks:
            a = d.actor
            s = a.get_actor_scale3d()
            L, D, H = 175 * s.x, 100 * s.y, 99 * s.z
            front = d.right * -1.0           # desk model faces -Y
            base = vec(d.center.x, d.center.y, d.bottom)
            # chair, pulled out a random amount and turned a bit
            off = rng.uniform(22, 48)
            cp = base + front * (D / 2 + off) + d.fwd * rng.uniform(-20, 20)
            cyaw = d.yaw + 180 + rng.uniform(-28, 28)
            spawn(chair, cp, cyaw, "Chair")
            # wastebasket at a front corner
            side = rng.choice((-1, 1))
            bp = base + front * (D / 2 + 22) + d.fwd * (side * (L / 2 - 20))
            spawn(M["SM_80s_Wastebasket"], bp, rng.uniform(0, 360), "Wastebasket")
            # 2-drawer file beside the desk, backs lined up, if it fits
            if rng.random() < 0.6:
                mn, mx = size_of("SM_80s_FileCabinet2")
                for sd in (side * -1, side):
                    fp = base + d.fwd * (sd * (L / 2 + 34)) - front * (D / 2 - mx[1])
                    box = rect_aabb(fp, d.yaw, mn, mx, 3)
                    if free(box, placed) and in_room(fp):
                        spawn(M["SM_80s_FileCabinet2"], fp, d.yaw, "DeskFile")
                        placed.append(box)
                        break
            # papers pinned on the cubicle wall behind the desk
            probe = d.center - front * (D / 2 + 15)
            best = None
            for p in panels:
                if abs(p.right.dot(front)) < 0.95 or p.sx < 150:
                    continue
                lx, ly = p.local(probe)
                if abs(lx) > p.sx / 2 or abs(ly) > p.sy / 2 + 120:
                    continue
                if best is None or abs(ly) < abs(best[1]):
                    best = (p, ly)
            if best:
                p = best[0]
                n = p.right * (1.0 if (d.center - p.center).dot(p.right) > 0 else -1.0)
                lx = max(-p.sx / 2 + 85, min(p.sx / 2 - 85, p.local(d.center)[0]))
                q = p.center + p.fwd * lx + n * (p.sy / 2 + 0.3)
                spawn(M[rng.choice(["SM_80s_CubiclePinup_A", "SM_80s_CubiclePinup_B", "SM_80s_CubiclePinup_C"])],
                      vec(q.x, q.y, floor_z + H + 80), yaw_facing(n), "Pinup", collide=False)

        # desk-area props count as obstacles for the wall pass
        for d in desks:
            front = d.right * -1.0
            c = d.center + front * 60
            placed.append((min(d.center.x, c.x) - 160, min(d.center.y, c.y) - 160, max(d.center.x, c.x) + 160, max(d.center.y, c.y) + 160))

        # ---------------- floor props along walls
        caps = {"SM_80s_WaterCooler": 4, "SM_80s_Copier": 3, "SM_80s_CoatRack": 4}
        weights = [("SM_80s_FileBank", 4), ("SM_80s_FileCabinet4", 2), ("SM_80s_Ficus", 3), ("SM_80s_SnakePlant", 2),
                   ("SM_80s_WaterCooler", 1.5), ("SM_80s_Copier", 1.2), ("SM_80s_CoatRack", 1.2)]
        used = {}
        rng.shuffle(faces)
        for w, axis, L, n, fc in faces:
            t = -L / 2 + 130
            while t < L / 2 - 130:
                if rng.random() < WALL_PROP_CHANCE:
                    pool = [(k, wt) for k, wt in weights if used.get(k, 0) < caps.get(k, 999)]
                    r = rng.uniform(0, sum(wt for _, wt in pool))
                    for name, wt in pool:
                        r -= wt
                        if r <= 0:
                            break
                    mn, mx = size_of(name)
                    width = mx[0] - mn[0]
                    if abs(t) + width / 2 < L / 2 - 90:
                        pos = fc + axis * t + n * (5 + mx[1])
                        yaw = yaw_facing(n)
                        box = rect_aabb(pos, yaw, mn, mx)
                        # walkway margin on the open sides; the host wall itself is ignored
                        boxm = rect_aabb(pos, yaw, mn, mx, CLEARANCE)
                        if in_room(pos) and free(boxm, placed, ignore=w.actor):
                            spawn(M[name], vec(pos.x, pos.y, floor_z), yaw + (rng.uniform(0, 360) if "Plant" in name or "Ficus" in name else 0),
                                  name.replace("SM_80s_", ""))
                            placed.append(box)
                            used[name] = used.get(name, 0) + 1
                            t += width + 60
                            continue
                t += 190

        # ---------------- wall decor
        decor_weights = [("SM_80s_Poster_Sunset", 2), ("SM_80s_Poster_Memphis", 2), ("SM_80s_Poster_Teamwork", 2),
                         ("SM_80s_BulletinBoard", 2), ("SM_80s_WallClock", 1)]
        decor_boxes = []
        clocks = 0
        for w, axis, L, n, fc in faces:
            t = -L / 2 + 150
            while t < L / 2 - 150:
                if rng.random() < WALL_DECOR_CHANCE:
                    pool = [(k, wt) for k, wt in decor_weights if not (k == "SM_80s_WallClock" and clocks >= 6)]
                    r = rng.uniform(0, sum(wt for _, wt in pool))
                    for name, wt in pool:
                        r -= wt
                        if r <= 0:
                            break
                    mn, mx = size_of(name)
                    width = mx[0] - mn[0]
                    zc = floor_z + (300 if name == "SM_80s_WallClock" else 275)
                    pos = fc + axis * t + n * 0.5
                    box = rect_aabb(pos, yaw_facing(n), mn, (mx[0], 40, mx[2]), 25)
                    if abs(t) + width / 2 < L / 2 - 60 and all(not overlaps(box, b) for b in decor_boxes):
                        spawn(M[name], vec(pos.x, pos.y, zc), yaw_facing(n), name.replace("SM_80s_", ""), collide=False)
                        decor_boxes.append(box)
                        clocks += name == "SM_80s_WallClock"
                        t += width + 120
                        continue
                t += 220

    log("office life added: " + ", ".join("%s %d" % kv for kv in sorted(count.items())))


run()
