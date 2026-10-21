"""Glass storefront + open glass double doors in the conference room's wide opening."""
import os, math, json, unreal
FOLDER = "Office80s/Doors/Conference"
DEST = "/Game/Office80s/Props/GlassFront"
OPEN_DEG = 95.0
here = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(here, "glass_front.json")))
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
def log(m): unreal.log("[Office80s] " + m)

def glass_material():
    path = "/Game/Office80s/Materials/M_80s_ClearGlass"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.load_asset(path); mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset("M_80s_ClearGlass", "/Game/Office80s/Materials", unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)
    try:
        mat.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    except Exception as ex:
        log("lighting mode not set (%s)" % ex)
    def c(v, x, y, vec=False):
        if vec:
            e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, x, y)
            e.set_editor_property("constant", unreal.LinearColor(*v, 1.0))
        else:
            e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, x, y)
            e.set_editor_property("r", v)
        return e
    mel.connect_material_property(c((0.55, 0.66, 0.66), -400, 0, True), "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(c(0.14, -400, 150), "", unreal.MaterialProperty.MP_OPACITY)
    mel.connect_material_property(c(0.04, -400, 250), "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(c(1.0, -400, 350), "", unreal.MaterialProperty.MP_SPECULAR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

def import_mesh(name, glass, complex_collision):
    t = unreal.AssetImportTask()
    t.filename = os.path.join(here, name + ".glb"); t.destination_path = DEST + "/" + name
    t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t])
    sm = None
    for p in unreal.EditorAssetLibrary.list_assets(DEST + "/" + name, recursive=True):
        x = unreal.load_asset(p)
        if isinstance(x, unreal.StaticMesh):
            sm = x
    mats = sm.get_editor_property("static_materials")
    for sm_mat in mats:
        if "ClearGlass" in str(sm_mat.get_editor_property("material_slot_name")):
            sm_mat.set_editor_property("material_interface", glass)
    sm.set_editor_property("static_materials", mats)
    ms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    ms.remove_collisions(sm)
    if complex_collision:
        bs = sm.get_editor_property("body_setup")
        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    else:
        ms.add_simple_collisions(sm, unreal.ScriptCollisionShapeType.BOX)
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
    return sm

def bb(a):
    o, e = a.get_actor_bounds(False)
    return (o.x - e.x, o.y - e.y, o.z - e.z, o.x + e.x, o.y + e.y, o.z + e.z)

actors = sub.get_all_level_actors()
old = [a for a in actors if str(a.get_folder_path()).startswith(FOLDER)]
floor_z = 20.0
walls, headers, conf = [], [], []
for a in actors:
    if a in old or not isinstance(a, unreal.StaticMeshActor) or not a.static_mesh_component.static_mesh:
        if a.get_actor_label().startswith("ConfTable"):
            conf.append(a.get_actor_location())
        continue
    if a.get_actor_label().startswith("ConfTable"):
        conf.append(a.get_actor_location())
    mp = a.static_mesh_component.static_mesh.get_path_name()
    b = bb(a)
    if mp.endswith("SM_Plane.SM_Plane") and b[3] - b[0] > 1000:
        floor_z = b[5]
    if mp.startswith("/Game/LevelPrototyping/Meshes/SM_Cube."):
        dx, dy, dz = b[3] - b[0], b[4] - b[1], b[5] - b[2]
        if dz < 150 and dx > 1000 and dy > 1000:
            continue
        if b[2] > 300 and min(dx, dy) < 150:
            headers.append((a, b))
        elif dz > 300 and b[2] < 40:
            walls.append((a, b))

best = None
for h, hb in headers:
    ax = (hb[3] - hb[0]) >= (hb[4] - hb[1])
    lo, hi = (hb[0], hb[3]) if ax else (hb[1], hb[4])
    plo, phi = (hb[1], hb[4]) if ax else (hb[0], hb[3])
    cuts = sorted(((wb[0], wb[3]) if ax else (wb[1], wb[4])) for w, wb in walls
                  if ((wb[1], wb[4]) if ax else (wb[0], wb[3]))[0] < phi + 15 and ((wb[1], wb[4]) if ax else (wb[0], wb[3]))[1] > plo - 15
                  and ((wb[3] if ax else wb[4]) > lo) and ((wb[0] if ax else wb[1]) < hi))
    cur = lo
    for a0, a1 in cuts + [(hi, hi)]:
        if a0 - cur > 600 and any(abs(c[1] - cur) < 2 for c in cuts) and any(abs(c[0] - a0) < 2 for c in cuts):
            side = [((wb[1], wb[4]) if ax else (wb[0], wb[3])) for w, wb in walls
                    if abs(((wb[3] if ax else wb[4])) - cur) < 2 or abs(((wb[0] if ax else wb[1])) - a0) < 2]
            pc = sum((p0 + p1) / 2 for p0, p1 in side) / len(side) if side else (plo + phi) / 2
            best = {"ax": ax, "g0": cur, "g1": a0, "pc": pc, "top": hb[2], "header": h.get_actor_label()}
        cur = max(cur, a1)
if not best:
    raise RuntimeError("no wide archway found")
o = best
w = o["g1"] - o["g0"]
Hh = o["top"] - floor_z
sx, sz = w / CFG["W"], Hh / CFG["H"]
mid = (o["g0"] + o["g1"]) / 2
def P(t, p):
    return (t, p) if o["ax"] else (p, t)
# swing into the room that holds the conference table
side = 1.0
if conf:
    cp = conf[0]
    side = 1.0 if ((cp.y if o["ax"] else cp.x) - o["pc"]) > 0 else -1.0

glass = glass_material()
front = import_mesh("SM_80s_GlassFront", glass, True)
leaf = import_mesh("SM_80s_GlassDoor", glass, False)
with unreal.ScopedEditorTransaction("Conference glass doors"):
    if old:
        sub.destroy_actors(old)
    cx, cy = P(mid, o["pc"])
    yaw = 0.0 if o["ax"] else 90.0
    a = sub.spawn_actor_from_object(front, unreal.Vector(cx, cy, floor_z), unreal.Rotator(0, 0, yaw))
    a.set_actor_scale3d(unreal.Vector(sx, 1, sz))
    a.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
    a.set_actor_label("GlassFront_Conference"); a.set_folder_path(FOLDER)
    half = CFG["door_w"] * sx
    lw = CFG["door_w"] * sx
    for i, (ht, adir) in enumerate(((mid - half, 1.0), (mid + half, -1.0))):
        ang = math.radians(OPEN_DEG)
        da, dp = adir * math.cos(ang), side * math.sin(ang)
        hx, hy = P(ht + adir * 2.0, o["pc"] + side * 4.0)
        dx, dy = P(da, dp)
        yaw = math.degrees(math.atan2(dy, dx)) - 90.0
        d = sub.spawn_actor_from_object(leaf, unreal.Vector(hx, hy, floor_z), unreal.Rotator(0, 0, yaw))
        d.set_actor_scale3d(unreal.Vector(1, lw / CFG["door_w"], 1))
        d.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
        d.set_actor_label("GlassDoor_Conference_%d" % (i + 1)); d.set_folder_path(FOLDER)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = [p.get_name() for p in list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())]
log("glass front in %.0f cm opening under %s (%.0f cm tall), doors swing %s; still unsaved: %d %s" % (w, o["header"], Hh, "+" if side > 0 else "-", len(left), left[:4]))
