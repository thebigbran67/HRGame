"""Open doors in every interior/room doorway of the Office map.
Finds doorways from the header beams above them (blockout cubes that start high up),
fills the space above a 330 cm door with wall, adds wood casing, and places door leaves
swung open ~95 deg on whichever side doesn't hit furniture or gameplay actors.
Re-runnable: clears Office80s/Doors first."""
import os, math, json, unreal
FOLDER = "Office80s/Doors"
DEST = "/Game/Office80s/Props/RoomDoors"
OPEN_DEG = 95.0
MAX_OPENING = 600.0
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
here = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(here, "room_doors.json")))
DH, DT = CFG["height"], CFG["thickness"]
def log(m): unreal.log("[Office80s] " + m)

_mesh = {}
def door_mesh(w):
    w = min(CFG["widths"], key=lambda x: abs(x - w))
    if w in _mesh:
        return w, _mesh[w]
    name = "SM_80s_RoomDoor_%d" % w
    t = unreal.AssetImportTask()
    t.filename = os.path.join(here, name + ".glb"); t.destination_path = DEST + "/" + name
    t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t])
    sm = None
    for p in unreal.EditorAssetLibrary.list_assets(DEST + "/" + name, recursive=True):
        x = unreal.load_asset(p)
        if isinstance(x, unreal.StaticMesh):
            sm = x
    ms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    ms.remove_collisions(sm); ms.add_simple_collisions(sm, unreal.ScriptCollisionShapeType.BOX)
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
    _mesh[w] = sm
    return w, sm

def aabb(a):
    o, e = a.get_actor_bounds(False)
    return (o.x - e.x, o.y - e.y, o.z - e.z, o.x + e.x, o.y + e.y, o.z + e.z)

def ov2(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

actors = sub.get_all_level_actors()
old = [a for a in actors if str(a.get_folder_path()).startswith(FOLDER)]
floor_z = 20.0
walls, headers, obstacles, doors_bp = [], [], [], []
ceiling_like = set()
for a in actors:
    if a in old:
        continue
    cls = a.get_class().get_name()
    if cls in ("GroupActor", "WorldDataLayers", "PostProcessVolume", "SkyAtmosphere", "SkyLight", "VolumetricCloud",
               "WorldPartitionMiniMap", "DirectionalLight", "RectLight", "PointLight", "LocalFogVolume"):
        continue
    b = aabb(a)
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        mp = a.static_mesh_component.static_mesh.get_path_name()
        if mp.endswith("SM_Plane.SM_Plane") and (b[3] - b[0]) > 1000:
            floor_z = b[5]; continue
        if mp.startswith("/Game/LevelPrototyping/Meshes/SM_Cube."):
            dx, dy, dz = b[3] - b[0], b[4] - b[1], b[5] - b[2]
            if dz < 150 and dx > 1000 and dy > 1000:
                continue                                   # floor slab / ceiling
            if b[2] > 300 and min(dx, dy) < 150:
                headers.append((a, b)); continue
            if dz > 300 and b[2] < 40:
                walls.append((a, b)); continue
        c = a.static_mesh_component
        if c.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION:
            continue
        if b[5] < floor_z + 5:
            continue
        obstacles.append(b)
    else:
        if cls == "BP_CubeDoor_C":
            p = a.get_actor_location()
            doors_bp.append((p.x - 200, p.y - 200, p.x + 200, p.y + 200))
        obstacles.append(b)

openings = []
for h, hb in headers:
    along_x = (hb[3] - hb[0]) >= (hb[4] - hb[1])
    lo, hi = (hb[0], hb[3]) if along_x else (hb[1], hb[4])
    plo, phi = (hb[1], hb[4]) if along_x else (hb[0], hb[3])
    cuts = []
    for w, wb in walls:
        wlo, whi = (wb[0], wb[3]) if along_x else (wb[1], wb[4])
        wplo, wphi = (wb[1], wb[4]) if along_x else (wb[0], wb[3])
        if wplo < phi + 15 and wphi > plo - 15 and whi > lo and wlo < hi:
            cuts.append((wlo, whi))
    cuts.sort()
    gaps, cur = [], lo
    for a0, a1 in cuts:
        if a0 > cur:
            gaps.append((cur, a0))
        cur = max(cur, a1)
    if cur < hi:
        gaps.append((cur, hi))
    for g0, g1 in gaps:
        wdt = g1 - g0
        if wdt < 120:
            continue
        # only real doorways: bounded by walls on both sides, not the main entrance, not giant archways
        if not any(abs(c[1] - g0) < 2 for c in cuts) or not any(abs(c[0] - g1) < 2 for c in cuts):
            continue
        # wall thickness / centre line from the walls on either side (the header can be thinner)
        side = []
        for w2, wb in walls:
            wlo, whi = (wb[0], wb[3]) if along_x else (wb[1], wb[4])
            wplo, wphi = (wb[1], wb[4]) if along_x else (wb[0], wb[3])
            if (whi - wlo) > (wphi - wplo) and (abs(whi - g0) < 2 or abs(wlo - g1) < 2) and wplo < phi + 15 and wphi > plo - 15:
                side.append((wplo, wphi))
        if side:
            th = min(p1 - p0 for p0, p1 in side)
            perp_c = sum((p0 + p1) / 2 for p0, p1 in side) / len(side)
        else:
            th = phi - plo
            perp_c = (plo + phi) / 2
        gb = (g0, perp_c - 60, g1, perp_c + 60) if along_x else (perp_c - 60, g0, perp_c + 60, g1)
        if any(ov2(gb, d) for d in doors_bp):
            continue
        if wdt > MAX_OPENING:
            log("skipping %.0f cm wide archway under %s" % (wdt, h.get_actor_label()))
            continue
        openings.append({"along_x": along_x, "g0": g0, "g1": g1, "perp": perp_c, "thick": max(th, phi - plo),
                         "top": hb[2], "header": h.get_actor_label()})

wall_mat = unreal.load_asset("/Game/Office80s/Materials/M_80s_WallTwoTone")
trim_mat = unreal.load_asset("/Game/Office80s/Materials/M_80s_WoodTrim")
cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
count = {"leaf": 0, "infill": 0, "casing": 0}

def spawn_box(cx, cy, cz, sx, sy, sz, mat, kind, collide):
    a = sub.spawn_actor_from_object(cube, unreal.Vector(cx, cy, cz), unreal.Rotator(0, 0, 0))
    a.set_actor_scale3d(unreal.Vector(sx / 100, sy / 100, sz / 100))
    c = a.static_mesh_component
    c.set_material(0, mat); c.set_mobility(unreal.ComponentMobility.STATIC)
    if not collide:
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    count[kind] += 1
    a.set_actor_label("Door%s_%02d" % (kind.capitalize(), count[kind]))
    a.set_folder_path(FOLDER)
    return a

def P(o, t, p):
    """point from (along t, perp p) for opening o"""
    return (t, p) if o["along_x"] else (p, t)

with unreal.ScopedEditorTransaction("Room doors"):
    if old:
        sub.destroy_actors(old)
    for o in openings:
        g0, g1, pc, T = o["g0"], o["g1"], o["perp"], o["thick"]
        w = g1 - g0
        n = 1 if w <= 330 else 2
        top = floor_z + DH
        # infill above the door + casing on both faces
        if o["top"] - top > 5:
            cx, cy = P(o, (g0 + g1) / 2, pc)
            sx, sy = (w, T) if o["along_x"] else (T, w)
            spawn_box(cx, cy, (top + o["top"]) / 2, sx, sy, o["top"] - top + 2, wall_mat, "infill", True)
        for s in (-1, 1):
            face = pc + s * (T / 2 + 1.2)
            for t in (g0 - 5, g1 + 5):
                cx, cy = P(o, t, face)
                sx, sy = (10, 2.5) if o["along_x"] else (2.5, 10)
                spawn_box(cx, cy, floor_z + (DH + 12) / 2, sx, sy, DH + 12, trim_mat, "casing", False)
            cx, cy = P(o, (g0 + g1) / 2, face)
            sx, sy = (w + 20, 2.5) if o["along_x"] else (2.5, w + 20)
            spawn_box(cx, cy, top + 6, sx, sy, 12, trim_mat, "casing", False)
        # leaves
        leaf_w = w / n - 1.0
        mw, mesh = door_mesh(leaf_w)
        yscale = leaf_w / mw
        ends = [(g0, 1.0), (g1, -1.0)] if n == 2 else None
        best = None
        hinge_opts = [[(g0, 1.0)], [(g1, -1.0)]] if n == 1 else [ends]
        for hinges in hinge_opts:
            for s in (-1, 1):
                hits, plans = 0, []
                for (ht, adir) in hinges:
                    ang = math.radians(OPEN_DEG)
                    # direction of the opened leaf in (along, perp) space
                    da, dp = adir * math.cos(ang), s * math.sin(ang)
                    hp = pc + s * (T / 2 - DT / 2)
                    hx, hy = P(o, ht + adir * 1.0, hp)
                    dx, dy = P(o, da, dp)
                    ex, ey = hx + dx * leaf_w, hy + dy * leaf_w
                    fb = (min(hx, ex) - 6, min(hy, ey) - 6, max(hx, ex) + 6, max(hy, ey) + 6)
                    hits += sum(1 for b in obstacles if ov2(fb, (b[0], b[1], b[3], b[4])))
                    yaw = math.degrees(math.atan2(dy, dx)) - 90.0
                    plans.append((hx, hy, yaw))
                if best is None or hits < best[0]:
                    best = (hits, plans)
        for hx, hy, yaw in best[1]:
            a = sub.spawn_actor_from_object(mesh, unreal.Vector(hx, hy, floor_z), unreal.Rotator(0, 0, yaw))
            if abs(yscale - 1.0) > 0.002:
                a.set_actor_scale3d(unreal.Vector(1, yscale, 1))
            a.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
            count["leaf"] += 1
            a.set_actor_label("RoomDoor_%02d" % count["leaf"])
            a.set_folder_path(FOLDER)
        log("doorway under %s: %.0f cm wide, %d leaf(s)%s" % (o["header"], w, n, "" if best[0] == 0 else " (touches %d thing(s), least-bad side)" % best[0]))

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = [p.get_name() for p in list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())]
log("doors placed in %d doorways (%d leaves); still unsaved: %d %s" % (len(openings), count["leaf"], len(left), left[:4]))
