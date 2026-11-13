"""Moves the graveyard + garbage dump behind the building (mirrored to the north side) and builds a
parking lot with monster cars out front, a street, ground everywhere and invisible property walls.
Re-runnable: the move only happens once (checked by where the dumpster is); Office80s/Front is rebuilt."""
import os, json, unreal
here = os.path.dirname(os.path.abspath(__file__))
FOLDER = "Office80s/Front"
DEST = "/Game/Office80s/Front"
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))

MIRROR_C = -4661.0          # y' = C - y : the yard's building-side edge (-5816) lands on the north wall (+1155)
YARD_LABELS = ("grass", "garbagedump", "BP_TrashDropOff")
LOT = json.load(open(os.path.join(here, "lot.json")))

def imp(fname, dest):
    t = unreal.AssetImportTask()
    t.filename = os.path.join(here, fname); t.destination_path = dest
    t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t])

def mesh(name):
    dest = DEST + "/" + name
    imp(name + ".glb", dest)
    for p in unreal.EditorAssetLibrary.list_assets(dest, recursive=True):
        x = unreal.load_asset(p)
        if isinstance(x, unreal.StaticMesh):
            unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).remove_collisions(x)
            unreal.EditorAssetLibrary.save_loaded_asset(x)
            return x
    raise RuntimeError("import failed " + name)

def wa_material(name, tex, tile_cm, tint, rough):
    path = DEST + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.load_asset(path); mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    wp = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -1100, 0)
    mk = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -900, 0)
    mk.set_editor_property("r", True); mk.set_editor_property("g", True); mk.set_editor_property("b", False); mk.set_editor_property("a", False)
    dv = mel.create_material_expression(mat, unreal.MaterialExpressionDivide, -700, 0); dv.set_editor_property("const_b", tile_cm)
    ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, 0); ts.set_editor_property("texture", tex)
    dv2 = mel.create_material_expression(mat, unreal.MaterialExpressionDivide, -700, 300); dv2.set_editor_property("const_b", tile_cm * 6.3)
    ts2 = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, 300); ts2.set_editor_property("texture", tex)
    mel.connect_material_expressions(wp, "", mk, "")
    mel.connect_material_expressions(mk, "", dv, "A"); mel.connect_material_expressions(dv, "", ts, "UVs")
    mel.connect_material_expressions(mk, "", dv2, "A"); mel.connect_material_expressions(dv2, "", ts2, "UVs")
    macro = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -300, 300)
    mel.connect_material_expressions(ts2, "G", macro, "A"); macro.set_editor_property("const_b", 1.0 / 0.5)
    tn = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 150); tn.set_editor_property("constant", tint)
    m1 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -150, 0)
    mel.connect_material_expressions(ts, "RGB", m1, "A"); mel.connect_material_expressions(tn, "", m1, "B")
    m2 = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -50, 100)
    mel.connect_material_expressions(m1, "", m2, "A"); mel.connect_material_expressions(macro, "", m2, "B")
    mel.connect_material_property(m2, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -150, 250); r.set_editor_property("r", rough)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat); unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

def find_tex(folder, key):
    for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.Texture2D) and key in a.get_name():
            return a
    return None

def mirror_yard():
    acts = sub.get_all_level_actors()
    dump = next(a for a in acts if a.get_actor_label() == "garbagedump")
    if dump.get_actor_location().y > 0:
        log("yard already behind the building, not moving it again")
        return
    yard = [a for a in acts if str(a.get_folder_path()).startswith("Office80s/Outdoor") or a.get_actor_label() in YARD_LABELS]
    for a in yard:
        o, e = a.get_actor_bounds(False)
        target = unreal.Vector(o.x, MIRROR_C - o.y, o.z)
        a.modify()
        r = a.get_actor_rotation()
        a.set_actor_rotation(unreal.Rotator(r.roll, r.pitch, -r.yaw), True)
        o2, e2 = a.get_actor_bounds(False)
        if e2.x + e2.y + e2.z < 1.0:      # lights / fog without real bounds: just mirror the location
            l = a.get_actor_location()
            a.set_actor_location(unreal.Vector(l.x, MIRROR_C - l.y, l.z), False, True)
        else:
            a.set_actor_location(a.get_actor_location() + (target - o2), False, True)
    log("moved %d yard actors behind the building; dump now at %s" % (len(yard), dump.get_actor_location()))

def main():
    acts = sub.get_all_level_actors()
    lamp_mesh = next(a for a in acts if a.get_actor_label().startswith("LampPost")).static_mesh_component.static_mesh
    tree_meshes = sorted({a.static_mesh_component.static_mesh.get_path_name() for a in acts if str(a.get_folder_path()) == "Office80s/Outdoor/DeadTree"})
    trees = [unreal.load_asset(p.split(".")[0]) for p in tree_meshes]
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    imp("T_80s_Asphalt.png", DEST + "/Textures")
    asphalt_tex = find_tex(DEST + "/Textures", "Asphalt")
    grass_tex = find_tex("/Game/Office80s/Outdoor/Textures", "Grass")
    m_asph = wa_material("M_80s_AsphaltWA", asphalt_tex, 400.0, unreal.LinearColor(1.0, 1.0, 1.0), 0.7)
    m_ground = wa_material("M_80s_GroundWA", grass_tex, 300.0, unreal.LinearColor(0.55, 0.55, 0.5), 0.95)
    m_conc = wa_material("M_80s_ConcreteWA", asphalt_tex, 250.0, unreal.LinearColor(2.1, 2.05, 1.95), 0.85)
    paint = mesh("SM_80s_LotPaint")
    cars = {k: mesh("SM_80s_Car_" + k) for k in ("Player", "Hearse", "SwampWagon", "FurHatch", "EyeballVan", "BatSedan", "WebPickup")}

    with unreal.ScopedEditorTransaction("Front lot + yard move"):
        mirror_yard()
        old = [a for a in sub.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]
        if old:
            sub.destroy_actors(old)

        def slab(label, x0, y0, x1, y1, top, thick, mat, folder=FOLDER + "/Ground"):
            a = sub.spawn_actor_from_object(cube, unreal.Vector((x0 + x1) / 2, (y0 + y1) / 2, top - thick / 2), unreal.Rotator(0, 0, 0))
            a.set_actor_scale3d(unreal.Vector((x1 - x0) / 100.0, (y1 - y0) / 100.0, thick / 100.0))
            c = a.static_mesh_component; c.set_mobility(unreal.ComponentMobility.STATIC)
            c.set_editor_property("override_materials", [mat])
            a.set_actor_label(label); a.set_folder_path(folder)
            return a
        def wall(label, x0, y0, x1, y1):
            a = sub.spawn_actor_from_object(cube, unreal.Vector((x0 + x1) / 2, (y0 + y1) / 2, 300.0), unreal.Rotator(0, 0, 0))
            a.set_actor_scale3d(unreal.Vector(max(x1 - x0, 50) / 100.0, max(y1 - y0, 50) / 100.0, 7.0))
            c = a.static_mesh_component; c.set_mobility(unreal.ComponentMobility.STATIC)
            c.set_collision_profile_name("BlockAll"); c.set_editor_property("visible", False)
            a.set_actor_hidden_in_game(True)
            a.set_actor_label(label); a.set_folder_path(FOLDER + "/Blockers")
        def put(m, x, y, yaw, label, z=0.0, folder=FOLDER):
            a = sub.spawn_actor_from_object(m, unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw))
            c = a.static_mesh_component; c.set_mobility(unreal.ComponentMobility.STATIC)
            c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            a.set_actor_label(label); a.set_folder_path(folder)
            return a
        def light(label, x, y, z, inten, radius, color, shadows):
            lt = sub.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, z))
            pl = lt.point_light_component; pl.set_mobility(unreal.ComponentMobility.MOVABLE)
            pl.set_editor_property("intensity", inten); pl.set_editor_property("attenuation_radius", radius)
            pl.set_editor_property("light_color", color); pl.set_editor_property("cast_shadows", shadows)
            lt.set_actor_label(label); lt.set_folder_path(FOLDER + "/Lights")

        slab("Ground_All", -30000, -40000, 37000, 40000, 19.0, 20.0, m_ground)
        slab("Lot_Asphalt", 200, -9350, 7300, -5830, 21.0, 4.0, m_asph)
        slab("Lot_Driveway", 2450, -9800, 2950, -9350, 21.0, 4.0, m_asph)
        slab("Street", -30000, -10700, 30000, -9800, 20.8, 4.0, m_asph)
        slab("Lot_Sidewalk", 200, -6170, 7300, -5830, 28.0, 10.0, m_conc)
        put(paint, 0, 0, 0, "Lot_Paint", 0.0)

        # cars: the player's in the first spot by the door, monster cars around the lot
        pc = put(cars["Player"], 1750, -6420, 90, "Car_Player", 0.0)
        pc.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        for y in (-1, 1):   # headlights that ride along in the intro
            hl = sub.spawn_actor_from_class(unreal.SpotLight, unreal.Vector(1750 + y * 55, -6420 + 245, 66), unreal.Rotator(0, -6, 90))
            sc = hl.spot_light_component; sc.set_mobility(unreal.ComponentMobility.MOVABLE)
            sc.set_editor_property("intensity", 40.0); sc.set_editor_property("attenuation_radius", 2600.0)
            sc.set_editor_property("outer_cone_angle", 32.0); sc.set_editor_property("inner_cone_angle", 18.0)
            sc.set_editor_property("light_color", unreal.Color(r=255, g=236, b=200, a=255))
            sc.set_editor_property("cast_shadows", y > 0)
            hl.attach_to_actor(pc, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
            hl.set_actor_label("Car_Player_Headlight%d" % (y + 1)); hl.set_folder_path(FOLDER + "/Lights")
        A, BC = LOT["x_A"], LOT["x_BC"]
        layout = [("Hearse", A[4], -6420, 90), ("EyeballVan", A[7], -6420, 90), ("BatSedan", A[11], -6420, 90), ("WebPickup", A[14], -6420, 90),
                  ("SwampWagon", BC[2], -7720, -90), ("FurHatch", BC[10], -7720, -90), ("BatSedan", BC[4], -8220, 90),
                  ("Hearse", BC[14], -8220, 90), ("FurHatch", BC[17], -7720, -90)]
        for i, (k, x, y, yaw) in enumerate(layout):
            put(cars[k], x, y, yaw, "Car_%s_%d" % (k, i))
            L = 600.0 if k in ("Hearse", "EyeballVan") else 500.0
            wall_b = sub.spawn_actor_from_object(cube, unreal.Vector(x, y, 95.0), unreal.Rotator(0, 0, yaw))
            wall_b.set_actor_scale3d(unreal.Vector(L / 100.0, 1.85, 1.5))
            c = wall_b.static_mesh_component; c.set_mobility(unreal.ComponentMobility.STATIC)
            c.set_collision_profile_name("BlockAll"); c.set_editor_property("visible", False); wall_b.set_actor_hidden_in_game(True)
            wall_b.set_actor_label("CarBlock_%d" % i); wall_b.set_folder_path(FOLDER + "/Blockers")
        wall_p = sub.spawn_actor_from_object(cube, unreal.Vector(1750, -6420, 95.0), unreal.Rotator(0, 0, 90))
        wall_p.set_actor_scale3d(unreal.Vector(4.9, 1.85, 1.5))
        c = wall_p.static_mesh_component; c.set_mobility(unreal.ComponentMobility.STATIC)
        c.set_collision_profile_name("BlockAll"); c.set_editor_property("visible", False); wall_p.set_actor_hidden_in_game(True)
        wall_p.set_actor_label("CarBlock_Player"); wall_p.set_folder_path(FOLDER + "/Blockers")

        # lamps: lot perimeter, the median, and along the far side of the street
        warm = unreal.Color(r=255, g=196, b=130, a=255)
        for i, (x, y, yaw) in enumerate(((300, -7070, 0), (7150, -7070, 180), (300, -8885, 0), (7150, -8885, 180), (2250, -7970, 0), (3150, -7970, 180))):
            put(lamp_mesh, x, y, yaw, "LotLamp_%d" % i, 21.0)
            light("LotLampLight_%d" % i, x, y, 470, 6.0, 2200.0, warm, i < 2)
        for i, x in enumerate(range(-4500, 9001, 2700)):
            put(lamp_mesh, x, -10860, 180, "StreetLamp_%d" % i, 20.8)
            light("StreetLampLight_%d" % i, x, -10860, 470, 4.0, 1800.0, warm, False)
        import random
        rng = random.Random(77)
        for i, x in enumerate(range(-5000, 9500, 1300)):
            if 2200 < x < 3300:
                continue
            put(rng.choice(trees), x + rng.uniform(-200, 200), -11500 - rng.uniform(0, 600), rng.uniform(0, 360), "StreetTree_%d" % i, 19.0)
            if not (-200 < x < 7700):
                continue
            put(rng.choice(trees), x + rng.uniform(-150, 150), -9550 + rng.uniform(-60, 60), rng.uniform(0, 360), "LotTree_%d" % i, 19.0)

        # property walls: you can walk all the way around the building but not off into the night
        wall("PropertyWall_S", -1400, -9500, 8600, -9450)
        wall("PropertyWall_W", -1450, -9500, -1400, 12000)
        wall("PropertyWall_E", 8600, -9500, 8650, 12000)
        wall("PropertyWall_N", -1450, 12000, 8650, 12050)

        # player starts next to the car, facing the front door
        for a in sub.get_all_level_actors():
            if isinstance(a, unreal.PlayerStart):
                a.modify(); a.set_actor_location(unreal.Vector(1500, -6420, 125), False, True)
                a.set_actor_rotation(unreal.Rotator(0, 0, 136.0), True)
                log("PlayerStart moved next to the car")
            if isinstance(a, unreal.NavMeshBoundsVolume):
                a.modify(); a.set_actor_location(unreal.Vector(3600, 1250, 740), False, True)
                o, e = a.get_actor_bounds(False)
                s = a.get_actor_scale3d()
                a.set_actor_scale3d(unreal.Vector(s.x * 10200.0 / (2 * e.x), s.y * 21600.0 / (2 * e.y), s.z))
                log("navmesh bounds now %s" % (a.get_actor_bounds(False),))
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("front lot built")

try:
    main()
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "front_and_back.log"), "w").write("\n".join(LOG))
