"""
HRGame / Office: dress the outside "grass" platform.
- grass texture on the actor labelled "grass"
- grass tufts, rocks (no collision), dead trees, crooked iron fence on the open edges,
  old lamp posts with dim lights along the walk from the door to the trash drop-off
- local fog volumes over the yard only (kept away from the building), colder dimmer sun
Re-runnable: clears Office80s/Outdoor first; light originals are kept in actor tags.
"""
import os, math, json, random
import unreal

SEED = 1313
FOLDER = "Office80s/Outdoor"
DEST = "/Game/Office80s/Outdoor"
GRASS_LABEL = "grass"
GRASS_TILE_CM = 300.0
SUN_SCALE = 0.25
SUN_COLOR = unreal.Color(r=170, g=186, b=225, a=255)
PATH_HALF_WIDTH = 450.0

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
rng = random.Random(SEED)


def log(m):
    unreal.log("[Office80s] " + m)


def src_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Office80s_Import")


SIZES = json.load(open(os.path.join(src_dir(), "outdoor_sizes.json")))
_cache = {}


def import_file(fname, dest):
    t = unreal.AssetImportTask()
    t.filename = os.path.join(src_dir(), fname)
    t.destination_path = dest
    t.automated = True
    t.replace_existing = True
    t.save = True
    tools.import_asset_tasks([t])


def mesh(short, collide):
    name = "SM_80s_" + short
    if name in _cache:
        return _cache[name]
    dest = DEST + "/" + name
    import_file(name + ".glb", dest)
    sm = None
    for p in unreal.EditorAssetLibrary.list_assets(dest, recursive=True):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            sm = a
    if sm is None:
        raise RuntimeError("import failed " + name)
    ms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    ms.remove_collisions(sm)
    if collide:
        ms.add_simple_collisions(sm, unreal.ScriptCollisionShapeType.BOX)
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
    _cache[name] = sm
    return sm


def grass_material(tiles_u, tiles_v):
    import_file("T_80s_Grass.png", DEST + "/Textures")
    tex = None
    for p in unreal.EditorAssetLibrary.list_assets(DEST + "/Textures", recursive=True):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.Texture2D) and "Grass" in a.get_name():
            tex = a
    path = DEST + "/M_80s_Grass"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.load_asset(path)
        mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset("M_80s_Grass", DEST, unreal.Material, unreal.MaterialFactoryNew())
    uv1 = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    uv1.set_editor_property("u_tiling", tiles_u); uv1.set_editor_property("v_tiling", tiles_v)
    uv2 = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -900, 300)
    uv2.set_editor_property("u_tiling", tiles_u / 6.7); uv2.set_editor_property("v_tiling", tiles_v / 6.7)
    t1 = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -650, 0)
    t2 = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -650, 300)
    for t in (t1, t2):
        t.set_editor_property("texture", tex)
    mel.connect_material_expressions(uv1, "", t1, "UVs")
    mel.connect_material_expressions(uv2, "", t2, "UVs")
    macro = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -400, 300)
    mel.connect_material_expressions(t2, "G", macro, "A")
    macro.set_editor_property("const_b", 4.2)
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -250, 0)
    mel.connect_material_expressions(t1, "RGB", mul, "A")
    mel.connect_material_expressions(macro, "", mul, "B")
    mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -250, 200)
    r.set_editor_property("r", 0.92)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def orig(actor, comp, key, prop):
    tags = list(actor.get_editor_property("tags"))
    for t in tags:
        s = str(t)
        if s.startswith(key + "="):
            return s.split("=", 1)[1]
    v = comp.get_editor_property(prop)
    if isinstance(v, unreal.Color):
        v = "%d,%d,%d" % (v.r, v.g, v.b)
    tags.append(unreal.Name("%s=%s" % (key, v)))
    actor.set_editor_property("tags", tags)
    return str(v)


def V(x, y, z=0.0):
    return unreal.Vector(x, y, z)


def dist_to_seg(px, py, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def run():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world.get_name() != "Office":
        raise RuntimeError("Open the Office map first")
    actors = sub.get_all_level_actors()
    old = [a for a in actors if str(a.get_folder_path()).startswith(FOLDER)]
    grass = next((a for a in actors if a.get_actor_label() == GRASS_LABEL), None)
    if grass is None:
        raise RuntimeError("no actor labelled '%s'" % GRASS_LABEL)
    o, e = grass.get_actor_bounds(False)
    G = (o.x - e.x, o.y - e.y, o.x + e.x, o.y + e.y)
    gz = o.z + e.z
    # the building is whatever floor plane sits north of the yard
    building_edge = G[3]
    gameplay, door, dropoff = [], None, None
    for a in actors:
        if a in old:
            continue
        cls = a.get_class().get_name()
        if cls.startswith("BP_") or cls == "PlayerStart" or a.get_actor_label() == "SM_Cube220":
            ao, ae = a.get_actor_bounds(False)
            box = (ao.x - ae.x, ao.y - ae.y, ao.x + ae.x, ao.y + ae.y)
            cx, cy = ao.x, ao.y
            if G[0] - 200 < cx < G[2] + 200 and G[1] - 200 < cy < G[3] + 400:
                gameplay.append(box)
            if cls == "BP_CubeDoor_C":
                door = (cx, cy)
            if cls == "BP_TrashDropOff_C":
                dropoff = (cx, cy)
    door = door or (G[0] + 300, G[3])
    dropoff = dropoff or ((G[0] + G[2]) / 2, G[1] + 1200)
    path_a = (door[0], door[1] - 150)
    path_b = (dropoff[0], dropoff[1] + 250)

    def near_gameplay(x, y, m):
        return any(b[0] - m < x < b[2] + m and b[1] - m < y < b[3] + m for b in gameplay)

    def in_path(x, y, extra=0.0):
        return dist_to_seg(x, y, path_a, path_b) < PATH_HALF_WIDTH + extra

    count = {}

    def spawn(short, x, y, yaw, collide, scale=1.0, z=None):
        a = sub.spawn_actor_from_object(mesh(short, collide), V(x, y, gz if z is None else z), unreal.Rotator(0, 0, yaw))
        if scale != 1.0:
            a.set_actor_scale3d(V(scale, scale, scale))
        sh = short.split("_")[0]
        count[sh] = count.get(sh, 0) + 1
        a.set_actor_label("%s_%03d" % (sh, count[sh]))
        a.set_folder_path(FOLDER + "/" + sh)
        c = a.static_mesh_component
        c.set_mobility(unreal.ComponentMobility.STATIC)
        if not collide:
            c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            c.set_editor_property("cast_shadow", short.startswith("Rocks"))
        return a

    with unreal.ScopedEditorTransaction("Office80s spooky yard"):
        if old:
            sub.destroy_actors(old)

        # ---------------- grass surface
        gb = grass.static_mesh_component.static_mesh.get_bounding_box()
        s = grass.get_actor_scale3d()
        su, sv = abs((gb.max.x - gb.min.x) * s.x), abs((gb.max.y - gb.min.y) * s.y)
        mat = grass_material(su / GRASS_TILE_CM, sv / GRASS_TILE_CM)
        grass.modify()
        grass.static_mesh_component.modify()
        grass.static_mesh_component.set_editor_property("override_materials", [mat])

        # ---------------- fence on the open edges (north side is the building)
        def fence_run(x0, y0, x1, y1):
            L = math.hypot(x1 - x0, y1 - y0)
            n = int(L // 300)
            yaw = math.degrees(math.atan2(y1 - y0, x1 - x0))
            for i in range(n):
                t = (i + 0.5) / n
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                if rng.random() < 0.1 or near_gameplay(x, y, 150):
                    continue  # broken gap
                spawn(rng.choice(["IronFence", "IronFence_B"]), x, y, yaw + rng.uniform(-2.5, 2.5), True)
        inset = 30
        fence_run(G[0] + inset, G[1] + inset, G[2] - inset, G[1] + inset)              # south
        fence_run(G[0] + inset, G[1] + inset, G[0] + inset, building_edge - 650)        # west
        fence_run(G[2] - inset, G[1] + inset, G[2] - inset, building_edge - 650)        # east

        # ---------------- lamp posts along the walk to the drop-off
        lamps = 0
        for i, t in enumerate((0.12, 0.37, 0.62, 0.87)):
            x = path_a[0] + (path_b[0] - path_a[0]) * t
            y = path_a[1] + (path_b[1] - path_a[1]) * t
            dx, dy = path_b[0] - path_a[0], path_b[1] - path_a[1]
            L = math.hypot(dx, dy)
            side = 1 if i % 2 == 0 else -1
            x += -dy / L * (PATH_HALF_WIDTH + 80) * side
            y += dx / L * (PATH_HALF_WIDTH + 80) * side
            if near_gameplay(x, y, 120):
                continue
            spawn("LampPost", x, y, rng.uniform(0, 90), True)
            light = sub.spawn_actor_from_class(unreal.PointLight, V(x, y, gz + 450))
            lc = light.get_component_by_class(unreal.PointLightComponent)
            lc.set_editor_property("intensity", 2.5 if i != 2 else 0.8)   # one nearly dead bulb
            lc.set_editor_property("attenuation_radius", 1300.0)
            lc.set_editor_property("light_color", unreal.Color(r=255, g=220, b=140, a=255))
            lc.set_editor_property("cast_shadows", i % 2 == 0)
            light.set_actor_label("LampLight_%02d" % (i + 1))
            light.set_folder_path(FOLDER + "/LampLight")
            lamps += 1

        # ---------------- dead trees
        trees = []
        tries = 0
        while len(trees) < 11 and tries < 600:
            tries += 1
            x, y = rng.uniform(G[0] + 250, G[2] - 250), rng.uniform(G[1] + 250, building_edge - 500)
            if in_path(x, y, 250) or near_gameplay(x, y, 400):
                continue
            if any(math.hypot(x - a, y - b) < 950 for a, b in trees):
                continue
            trees.append((x, y))
            spawn(rng.choice(["DeadTree_A", "DeadTree_B", "DeadTree_C"]), x, y, rng.uniform(0, 360), True, rng.uniform(0.85, 1.2), z=gz - 4)

        # ---------------- grass tufts and rocks (visual only)
        for i in range(230):
            x, y = rng.uniform(G[0] + 120, G[2] - 120), rng.uniform(G[1] + 120, G[3] - 60)
            if near_gameplay(x, y, -20) or (in_path(x, y, -200) and rng.random() < 0.7):
                continue
            spawn(rng.choice(["GrassPatch_A", "GrassPatch_B"]), x, y, rng.uniform(0, 360), False, rng.uniform(0.8, 1.3))
        for i in range(26):
            x, y = rng.uniform(G[0] + 150, G[2] - 150), rng.uniform(G[1] + 150, G[3] - 300)
            if in_path(x, y) or near_gameplay(x, y, 150):
                continue
            spawn(rng.choice(["Rocks_A", "Rocks_B"]), x, y, rng.uniform(0, 360), False, rng.uniform(0.7, 1.6))

        # ---------------- fog over the yard only
        fog_ok = hasattr(unreal, "LocalFogVolume")
        nf = 0
        if fog_ok:
            xs = [G[0] + (G[2] - G[0]) * f for f in (0.2, 0.5, 0.8)]
            ys = []
            y = building_edge - 3300
            while y > G[1] - 500:
                ys.append(y)
                y -= 2800
            for fy in ys:
                for fx in xs:
                    f = sub.spawn_actor_from_class(unreal.LocalFogVolume, V(fx, fy, gz))
                    f.set_actor_scale3d(V(32, 32, 32))
                    fc = f.get_component_by_class(unreal.LocalFogVolumeComponent)
                    for prop, val in (("radial_fog_extinction", 0.25), ("height_fog_extinction", 1.2),
                                      ("height_fog_falloff", 1200.0), ("height_fog_offset", 0.0),
                                      ("fog_albedo", unreal.LinearColor(0.55, 0.6, 0.66, 1.0)),
                                      ("fog_emissive", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))):
                        try:
                            fc.set_editor_property(prop, val)
                        except Exception as ex:
                            log("fog property %s not set (%s)" % (prop, ex))
                    nf += 1
                    f.set_actor_label("YardFog_%02d" % nf)
                    f.set_folder_path(FOLDER + "/Fog")
        else:
            log("LocalFogVolume not available in this engine build; no fog added")

        # ---------------- colder, dimmer sun
        for a in actors:
            if isinstance(a, unreal.DirectionalLight):
                c = a.get_component_by_class(unreal.DirectionalLightComponent)
                a.modify(); c.modify()
                base = float(orig(a, c, "o80s_int", "intensity"))
                orig(a, c, "o80s_col", "light_color")
                c.set_editor_property("intensity", base * SUN_SCALE)
                c.set_editor_property("light_color", SUN_COLOR)

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("yard dressed: " + ", ".join("%s %d" % kv for kv in sorted(count.items())) + ", lamps %d, fog volumes %d" % (lamps, nf))


run()
