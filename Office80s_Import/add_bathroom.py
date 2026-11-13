"""Turns the empty room south of the main floor (door on its north wall) into an 80s bathroom:
wet checker tile floor, stalls, sinks, urinals, puddles and wet-floor signs. BP_TrashBag5 moves into the
last stall. The slippery floor itself lives in BP_TaskHUD (it lowers friction while you're in here).
Re-runnable: clears Office80s/Bathroom first."""
import os, math, unreal
here = os.path.dirname(os.path.abspath(__file__))
FOLDER = "Office80s/Bathroom"
O = unreal.Vector(1937.0, -5730.0, 20.0)     # room's south-west floor corner
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))
CLEAR = ("Copier_002", "FileBank_003", "FileBank_005", "FileBank_006", "FileBank_007", "FileBank_008")

def imp(name):
    dest = "/Game/Office80s/Props/Bathroom/" + name
    t = unreal.AssetImportTask()
    t.filename = os.path.join(here, name + ".glb"); t.destination_path = dest
    t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t])
    for p in unreal.EditorAssetLibrary.list_assets(dest, recursive=True):
        x = unreal.load_asset(p)
        if isinstance(x, unreal.StaticMesh):
            unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).remove_collisions(x)
            unreal.EditorAssetLibrary.save_loaded_asset(x)
            return x
    raise RuntimeError("import failed " + name)

def W(x, y, z=0.0):
    return unreal.Vector(O.x + x, O.y + y, O.z + z)

def main():
    M = {n: imp("SM_80s_" + n) for n in ("BathShell", "BathStalls", "BathSinks", "BathUrinals", "BathPuddles", "WetFloorSign")}
    mop = unreal.load_asset("/Game/Office80s/Props/SM_80s_MopBucket/SM_80s_MopBucket/StaticMeshes/SM_80s_MopBucket")
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    with unreal.ScopedEditorTransaction("Bathroom"):
        old = [a for a in sub.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]
        if old:
            sub.destroy_actors(old)
        gone = [a for a in sub.get_all_level_actors() if a.get_actor_label() in CLEAR]
        log("removed: %s" % sorted(a.get_actor_label() for a in gone))
        sub.destroy_actors(gone)

        def put(mesh, x, y, z, yaw, label, shadow=True):
            a = sub.spawn_actor_from_object(mesh, W(x, y, z), unreal.Rotator(0, 0, yaw))
            c = a.static_mesh_component
            c.set_mobility(unreal.ComponentMobility.STATIC)
            c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            c.set_editor_property("cast_shadow", shadow)
            a.set_actor_label(label); a.set_folder_path(FOLDER)
            return a
        def block(x0, y0, x1, y1, h, label, yaw=0.0):
            b = sub.spawn_actor_from_object(cube, W((x0 + x1) / 2, (y0 + y1) / 2, h / 2), unreal.Rotator(0, 0, yaw))
            b.set_actor_scale3d(unreal.Vector((x1 - x0) / 100.0, (y1 - y0) / 100.0, h / 100.0))
            c = b.static_mesh_component
            c.set_mobility(unreal.ComponentMobility.STATIC)
            c.set_collision_profile_name("BlockAll")
            c.set_editor_property("visible", False)
            b.set_actor_hidden_in_game(True)
            b.set_actor_label("BathBlock_" + label); b.set_folder_path(FOLDER + "/Blockers")
        def block_rot(cx, cy, L, T, h, yaw, label):
            b = sub.spawn_actor_from_object(cube, W(cx, cy, h / 2), unreal.Rotator(0, 0, yaw))
            b.set_actor_scale3d(unreal.Vector(L / 100.0, T / 100.0, h / 100.0))
            c = b.static_mesh_component
            c.set_mobility(unreal.ComponentMobility.STATIC)
            c.set_collision_profile_name("BlockAll")
            c.set_editor_property("visible", False)
            b.set_actor_hidden_in_game(True)
            b.set_actor_label("BathBlock_" + label); b.set_folder_path(FOLDER + "/Blockers")

        put(M["BathShell"], 0, 0, 0.05, 0, "Bath_Floor_and_Tiles", False)
        put(M["BathPuddles"], 0, 0, 0.05, 0, "Bath_Puddles", False)
        put(M["BathStalls"], 0, 0, 0, 0, "Bath_Stalls")
        put(M["BathSinks"], 0, 0, 0, 0, "Bath_Sinks")
        put(M["BathUrinals"], 0, 0, 0, 0, "Bath_Urinals")
        signs = ((470, 1180, 25), (640, 640, -15), (935, 420, 40))
        for i, (x, y, yaw) in enumerate(signs):
            put(M["WetFloorSign"], x, y, 0, yaw, "Bath_WetFloorSign_%d" % i)
            block_rot(x, y, 40, 34, 75, yaw, "Sign%d" % i)
        put(mop, 330, 330, 0, 35, "Bath_MopBucket")
        block_rot(330, 330, 70, 55, 90, 35, "Mop")

        # fixtures
        block(0, 500, 68, 1150, 100, "Sinks")
        X0, SW, SD = 640.0, 140.0, 165.0
        for i in range(5):
            x = X0 + i * SW
            if x < 1205:
                block(x - 3, 0, x + 3, SD + 3, 200, "Partition%d" % i)
        for i in range(4):
            x0 = X0 + i * SW
            block(x0, SD - 3, x0 + 27, SD + 3, 200, "PilasterL%d" % i)
            block(x0 + 113, SD - 3, min(x0 + SW, 1207), SD + 3, 200, "PilasterR%d" % i)
            block(x0 + SW / 2 - 24, 0, x0 + SW / 2 + 24, 64, 85, "Toilet%d" % i)
            if i in (0, 2):
                block(x0 + 27, SD - 3, x0 + 113, SD + 3, 200, "Door%d" % i)
            elif i == 1:
                a = math.radians(35)
                block_rot(x0 + 27 + 43 * math.cos(a), SD + 43 * math.sin(a), 86, 6, 200, 35, "Door1")
        for y in (430.0, 610.0, 790.0):
            block(1170, y - 24, 1211, y + 24, 125, "Urinal%d" % int(y))
        for y in (520.0, 700.0):
            block(1150, y - 3, 1211, y + 3, 165, "Divider%d" % int(y))

        lt = sub.spawn_actor_from_class(unreal.PointLight, W(620, 760, 640))
        pl = lt.point_light_component
        pl.set_mobility(unreal.ComponentMobility.MOVABLE)
        pl.set_editor_property("intensity", 5.0)
        pl.set_editor_property("light_color", unreal.Color(r=200, g=255, b=225, a=255))
        pl.set_editor_property("attenuation_radius", 1300.0)
        lt.set_actor_label("Bath_Light"); lt.set_folder_path(FOLDER)

        for a in sub.get_all_level_actors():
            if a.get_actor_label() == "BP_TrashBag5":
                a.modify(); z = a.get_actor_location().z
                a.set_actor_location(W(1130, 108, 0) + unreal.Vector(0, 0, z - O.z), False, True)
                log("BP_TrashBag5 moved into the last stall: %s" % a.get_actor_location())
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("bathroom built")

try:
    main()
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "bathroom.log"), "w").write("\n".join(LOG))
