"""More classic monster dressing (round 2): web cocoons, slime puddles and drips, a clawed footprint
trail leading into the janitor closet, bats, a pile of bones, egg sacs. Re-runnable: clears Office80s/Monster2."""
import os, unreal
FOLDER = "Office80s/Monster2"
here = os.path.dirname(os.path.abspath(__file__))
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
def log(m): unreal.log("[Office80s] " + m)
CEIL, FLOOR = 994.5, 20.0

def imp(name):
    t = unreal.AssetImportTask()
    t.filename = os.path.join(here, name + ".glb"); t.destination_path = "/Game/Office80s/Props/Monster/" + name
    t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t])
    for p in unreal.EditorAssetLibrary.list_assets("/Game/Office80s/Props/Monster/" + name, recursive=True):
        x = unreal.load_asset(p)
        if isinstance(x, unreal.StaticMesh):
            unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).remove_collisions(x)
            unreal.EditorAssetLibrary.save_loaded_asset(x)
            return x
    raise RuntimeError("import failed " + name)

M = {n: imp("SM_80s_" + n) for n in ("Cocoon_A", "Cocoon_B", "Slime_A", "Slime_B", "SlimeDrip", "ClawTracks", "Bats", "Bones", "EggSacs")}
placed = []
def put(mesh, x, y, z, yaw, label, shadow=True):
    a = sub.spawn_actor_from_object(M[mesh], unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw))
    c = a.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.STATIC)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property("cast_shadow", shadow)
    a.set_actor_label(label); a.set_folder_path(FOLDER); placed.append(label)

with unreal.ScopedEditorTransaction("Office monster dressing 2"):
    old = [a for a in sub.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]
    if old:
        sub.destroy_actors(old)
    # web-wrapped victims hanging from the ceiling
    put("Cocoon_A", 3000, 800, CEIL, 20, "Cocoon_Conference")
    put("Cocoon_B", 5600, -1800, CEIL, -40, "Cocoon_SideRoom")
    # slime
    put("Slime_A", 4650, -4450, FLOOR, 20, "Slime_Closet", False)
    put("Slime_B", 4760, -1250, FLOOR, 75, "Slime_Office", False)
    put("Slime_A", 5900, 650, FLOOR, 160, "Slime_Boss", False)
    put("SlimeDrip", 4890.5, -1300, 700, -90, "SlimeDrip_Office", False)
    put("SlimeDrip", 4897.5, -5000, 650, -90, "SlimeDrip_Closet", False)
    # clawed footprints: down the aisle, along the south wall, into the janitor closet
    put("ClawTracks", 3450, -2650, FLOOR, -90, "ClawTracks_1", False)
    put("ClawTracks", 3500, -3950, FLOOR, 0, "ClawTracks_2", False)
    put("ClawTracks", 4676, -4000, FLOOR, -90, "ClawTracks_3", False)
    # bats roosting on the ceiling
    put("Bats", 950, -1950, CEIL, 0, "Bats_Reception")
    put("Bats", 1400, 800, CEIL, 120, "Bats_Cubicles")
    put("Bats", 5900, 900, CEIL, 240, "Bats_Boss")
    # what's left of the last janitor, and egg sacs
    put("Bones", 4520, -5620, FLOOR, 30, "Bones_Closet")
    put("EggSacs", 6150, -2760, FLOOR, 0, "EggSacs_SideRoom")
    put("EggSacs", 2740, 400, FLOOR, 140, "EggSacs_Conference")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
log("monster dressing 2: placed %d; still unsaved: %d" % (len(placed), len(left)))
