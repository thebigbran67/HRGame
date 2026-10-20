"""
HRGame: swap the Office level's blockout desks and cubicle walls for 1980s office models.

How to run (Unreal Editor, with the Office map open):
    Tools > Execute Python Script...  and pick this file
or in the Output Log, switch the box from "Cmd" to "Python" and run:
    exec(open(r"C:/Users/rbrannig/Documents/GitHub/HRGame/Office80s_Import/replace_blockout_80s.py").read())

What it does:
  1. Imports the .glb models sitting next to this script into /Game/Office80s/Meshes
  2. Finds the blockout pieces in the open level:
       - thin slabs of SM_Cube about desk size (the 175 x 100 desktops)  -> 80s steel desk
       - the SM_Cylinder legs under those slabs                         -> removed (the desk has its own body)
       - tall thin SM_Cube walls about cubicle size (100/262/318 long)  -> fabric cubicle panels
     Outer room walls, floors, ceilings and anything that isn't SM_Cube/SM_Cylinder are left alone.
  3. Puts the new models exactly where the blockout pieces were (same footprint and height)
     and deletes the blockout pieces. It is one undo step, so Ctrl+Z puts everything back.
Nothing is saved automatically. Look it over, then File > Save All.
"""
import os
import zlib
import unreal

# ------------------------------------------------------------------ settings
DRY_RUN = False          # True = only print what would be replaced
ADD_CHAIRS = False       # True = also roll an 80s office chair up to each desk
DEST = "/Game/Office80s/Meshes"
EXPECTED_MAP = "Office"

DESK_VARIANTS = [         # (mesh name, weight)
    ("SM_Desk80s_Terminal", 45),
    ("SM_Desk80s_Clerical", 40),
    ("SM_Desk80s_Plain", 15),
]
PANEL_LENGTHS = [100, 262, 318]
DESK_NOMINAL = (175.0, 100.0, 99.0)     # footprint X, Y and top height the desk meshes were built at
PANEL_NOMINAL_T, PANEL_NOMINAL_H = 25.0, 253.0

# ------------------------------------------------------------------ helpers
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def log(msg):
    unreal.log("[Office80s] " + str(msg))


def source_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Office80s_Import")


def import_models():
    folder = source_dir()
    meshes = {}
    names = [n for n, _ in DESK_VARIANTS] + ["SM_CubiclePanel80s_%d" % L for L in PANEL_LENGTHS] + ["SM_OfficeChair80s"]
    for name in names:
        path = os.path.join(folder, name + ".glb")
        if not os.path.exists(path):
            raise RuntimeError("Missing model file: " + path)
        dest = DEST + "/" + name
        task = unreal.AssetImportTask()
        task.filename = path
        task.destination_path = dest
        task.automated = True
        task.replace_existing = True
        task.save = True
        asset_tools.import_asset_tasks([task])
        sm = None
        for p in list(task.imported_object_paths or []):
            a = unreal.load_asset(p)
            if isinstance(a, unreal.StaticMesh):
                sm = a
        if sm is None:  # fall back to looking in the folder
            for p in unreal.EditorAssetLibrary.list_assets(dest, recursive=True):
                a = unreal.load_asset(p)
                if isinstance(a, unreal.StaticMesh):
                    sm = a
        if sm is None:
            raise RuntimeError("Import produced no static mesh for " + name)
        set_box_collision(sm)
        meshes[name] = sm
        log("imported %s -> %s" % (name, sm.get_path_name()))
    return meshes


def set_box_collision(sm):
    try:
        sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        sub.remove_collisions(sm)
        sub.add_simple_collisions(sm, unreal.ScriptCollisionShapeType.BOX)
    except Exception:
        lib = unreal.EditorStaticMeshLibrary
        lib.remove_collisions(sm)
        lib.add_simple_collisions(sm, unreal.ScriptingCollisionShapeType.BOX)
    unreal.EditorAssetLibrary.save_loaded_asset(sm)


def detect_axis_fix(meshes):
    """The models are authored with +X along the desk and the sitting side at -Y.
    Check the imported bounds in case the glTF importer flipped or rotated anything."""
    b = meshes["SM_Desk80s_Terminal"].get_bounding_box()
    mn, mx = b.min, b.max
    fix = {"yaw": 0.0, "mirror_y": False}
    if abs(mx.y - 53.56) < 1.5 and abs(mn.y + 50.8) < 1.5:
        pass
    elif abs(mn.y + 53.56) < 1.5 and abs(mx.y - 50.8) < 1.5:
        # front ended up at +Y; a half turn puts the drawers back on the sitting side
        fix["yaw"] = 180.0
    elif abs(mx.x - 53.56) < 1.5:
        fix["yaw"] = 90.0
    elif abs(mn.x + 53.56) < 1.5:
        fix["yaw"] = -90.0
    else:
        log("WARNING: unexpected desk bounds %s .. %s, placing without correction" % (mn, mx))
    zsize = mx.z - mn.z
    if zsize < 100:
        log("WARNING: desk mesh looks lying down (height %.1f). Check the import." % zsize)
    if fix["yaw"]:
        log("importer rotated the models; correcting by %.0f deg" % fix["yaw"])
    return fix


class Piece:
    def __init__(self, actor):
        self.actor = actor
        comp = actor.static_mesh_component
        self.mesh_path = comp.static_mesh.get_path_name() if comp.static_mesh else ""
        xf = actor.get_actor_transform()
        box = comp.static_mesh.get_bounding_box()
        local_c = (box.min + box.max) * 0.5
        s = actor.get_actor_scale3d()
        e = box.max - box.min
        self.sx, self.sy, self.sz = abs(e.x * s.x), abs(e.y * s.y), abs(e.z * s.z)
        self.center = xf.transform_location(local_c)
        self.rot = actor.get_actor_rotation()
        self.fwd = self.rot.get_forward_vector()
        self.right = self.rot.get_right_vector()
        self.top = self.center.z + self.sz / 2
        self.bottom = self.center.z - self.sz / 2
        self.level_ok = abs(self.rot.pitch) < 1.0 and abs(self.rot.roll) < 1.0

    def is_cube(self):
        return self.mesh_path.startswith("/Game/LevelPrototyping/Meshes/SM_Cube.")

    def is_cylinder(self):
        return self.mesh_path.startswith("/Game/LevelPrototyping/Meshes/SM_Cylinder.")

    def local_xy(self, p):
        d = p - self.center
        return d.dot(self.fwd), d.dot(self.right)

    def contains_xy(self, p, margin=0.0):
        lx, ly = self.local_xy(p)
        return abs(lx) <= self.sx / 2 + margin and abs(ly) <= self.sy / 2 + margin

    def dist_xy(self, p):
        lx, ly = self.local_xy(p)
        dx = max(0.0, abs(lx) - self.sx / 2)
        dy = max(0.0, abs(ly) - self.sy / 2)
        return (dx * dx + dy * dy) ** 0.5


def yaw_rot(base, add):
    return unreal.Rotator(roll=0.0, pitch=0.0, yaw=base.yaw + add)


def pick_variant(key):
    h = zlib.crc32(key.encode()) % sum(w for _, w in DESK_VARIANTS)
    for name, w in DESK_VARIANTS:
        if h < w:
            return name
        h -= w
    return DESK_VARIANTS[0][0]


def spawn(mesh, loc, rot, scale, label, folder):
    a = actor_sub.spawn_actor_from_object(mesh, loc, rot)
    a.set_actor_scale3d(scale)
    a.set_actor_label(label)
    a.set_folder_path(folder)
    a.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
    return a


# ------------------------------------------------------------------ main
def run():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world is None or world.get_name() != EXPECTED_MAP:
        raise RuntimeError("Open the '%s' map first (currently: %s)" % (EXPECTED_MAP, world.get_name() if world else None))

    pieces = []
    for a in actor_sub.get_all_level_actors():
        if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
            p = Piece(a)
            if (p.is_cube() or p.is_cylinder()) and p.level_ok:
                pieces.append(p)

    desks, panels, walls, cyls = [], [], [], []
    for p in pieces:
        if p.is_cylinder():
            cyls.append(p)
            continue
        thin, long_ = min(p.sx, p.sy), max(p.sx, p.sy)
        if p.sz <= 15 and 50 <= thin and long_ <= 300:
            desks.append(p)
        elif 5 <= thin <= 45 and 50 <= long_ <= 450 and 120 <= p.sz <= 320:
            panels.append(p)
        elif p.sz > 200:
            walls.append(p)

    legs_for = {}
    used_legs = set()
    for d in desks:
        legs = [c for c in cyls if id(c) not in used_legs and d.contains_xy(c.center, 5)
                and abs(c.top - d.bottom) < 20 and c.sz > 30]
        for c in legs:
            used_legs.add(id(c))
        legs_for[id(d)] = legs

    log("found %d desktops (%d legs) and %d cubicle panels" % (len(desks), len(used_legs), len(panels)))
    if DRY_RUN:
        for d in desks:
            log("  desk  %s  %.0fx%.0fx%.0f at %s, legs: %s" % (d.actor.get_actor_label(), d.sx, d.sy, d.sz, d.center,
                [c.actor.get_actor_label() for c in legs_for[id(d)]]))
        for p in panels:
            log("  panel %s  %.0fx%.0fx%.0f" % (p.actor.get_actor_label(), p.sx, p.sy, p.sz))
        return
    if not desks and not panels:
        log("Nothing to replace.")
        return

    meshes = import_models()
    fix = detect_axis_fix(meshes)
    obstacles = panels + walls
    to_delete = []
    made = {"desk": 0, "panel": 0, "chair": 0}

    with unreal.ScopedEditorTransaction("Replace blockout with 80s office furniture"):
        # ---------------- cubicle panels
        for p in panels:
            if p.sx >= p.sy:
                L, T, add = p.sx, p.sy, 0.0
            else:
                L, T, add = p.sy, p.sx, 90.0
            nominal = min(PANEL_LENGTHS, key=lambda n: abs(n - L))
            mesh = meshes["SM_CubiclePanel80s_%d" % nominal]
            loc = unreal.Vector(p.center.x, p.center.y, p.bottom)
            scale = unreal.Vector(L / nominal, T / PANEL_NOMINAL_T, p.sz / PANEL_NOMINAL_H)
            made["panel"] += 1
            spawn(mesh, loc, yaw_rot(p.rot, add + fix["yaw"]), scale,
                  "CubiclePanel80s_%02d" % made["panel"], "Office80s/Cubicles")
            to_delete.append(p.actor)

        # ---------------- desks
        for d in desks:
            if d.sx >= d.sy:
                L, D, add = d.sx, d.sy, 0.0
            else:
                L, D, add = d.sy, d.sx, 90.0
            legs = legs_for[id(d)]
            if legs:
                floor = min(c.bottom for c in legs)
            else:
                near = [o for o in panels if o.dist_xy(d.center) < 300]
                floor = min(o.bottom for o in near) if near else d.top - DESK_NOMINAL[2]
            H = d.top - floor
            # the side you sit on (model -Y) should face away from the nearest cubicle wall
            rot = yaw_rot(d.rot, add)
            front = rot.get_right_vector() * -1.0
            probe = D / 2 + 45
            pf = d.center + front * probe
            pb = d.center - front * probe
            df = min([o.dist_xy(pf) for o in obstacles] or [1e9])
            db = min([o.dist_xy(pb) for o in obstacles] or [1e9])
            if df < db:
                add += 180.0
                rot = yaw_rot(d.rot, add)
                front = front * -1.0
            name = pick_variant(d.actor.get_actor_label())
            loc = unreal.Vector(d.center.x, d.center.y, floor)
            scale = unreal.Vector(L / DESK_NOMINAL[0], D / DESK_NOMINAL[1], H / DESK_NOMINAL[2])
            made["desk"] += 1
            spawn(meshes[name], loc, yaw_rot(d.rot, add + fix["yaw"]), scale,
                  "Desk80s_%02d" % made["desk"], "Office80s/Desks")
            to_delete.append(d.actor)
            to_delete += [c.actor for c in legs]

            if ADD_CHAIRS:
                k = H / DESK_NOMINAL[2]
                cl = d.center + front * (D / 2 + 25 * k)
                made["chair"] += 1
                spawn(meshes["SM_OfficeChair80s"], unreal.Vector(cl.x, cl.y, floor),
                      yaw_rot(d.rot, add + fix["yaw"] + (zlib.crc32(name.encode() + bytes([made["chair"]])) % 30 - 15)),
                      unreal.Vector(k, k, k), "OfficeChair80s_%02d" % made["chair"], "Office80s/Chairs")

        actor_sub.destroy_actors(to_delete)

    log("done: %d desks, %d cubicle panels, %d chairs placed; %d blockout actors removed. "
        "Ctrl+Z undoes it, File > Save All keeps it." % (made["desk"], made["panel"], made["chair"], len(to_delete)))


run()
