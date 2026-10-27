"""Classic monster dressing: cobwebs in ceiling corners, big spiders, spiders dangling on threads,
claw marks gouged into walls. Re-runnable: clears Office80s/Monster first."""
import os, unreal
FOLDER = "Office80s/Monster"
here = os.path.dirname(os.path.abspath(__file__))
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
def log(m): unreal.log("[Office80s] " + m)
CEIL = 994.5

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

M = {n: imp("SM_80s_" + n) for n in ("CornerWeb_A", "CornerWeb_B", "SpiderBig", "SpiderDangle_A", "SpiderDangle_B", "ClawMarks")}
placed = []
def put(mesh, x, y, z, roll, pitch, yaw, label):
    a = sub.spawn_actor_from_object(M[mesh], unreal.Vector(x, y, z), unreal.Rotator(roll, pitch, yaw))
    c = a.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.STATIC)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property("cast_shadow", mesh.startswith("Spider"))
    a.set_actor_label(label); a.set_folder_path(FOLDER); placed.append(label)

# ceiling corners: (corner x, corner y, yaw for the room quadrant, web)
WEBS = [(730, 1055, -90, "A"), (2680, 1055, -90, "B"), (4865, 1055, 180, "A"), (730, -1704, -90, "B"),
        (1901, -5748, 90, "A"), (4413, -5730, 0, "A"), (4898, -4203, 180, "B"), (6244, 1055, 180, "A"),
        (6244, -2831, 90, "B"), (4883, -1, 180, "B"), (1937, -4139, 0, "A"), (6244, -5800, 90, "A"),
        (1937, -5730, 0, "B")]
with unreal.ScopedEditorTransaction("Office monster dressing"):
    old = [a for a in sub.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]
    if old:
        sub.destroy_actors(old)
    for i, (x, y, yaw, v) in enumerate(WEBS):
        put("CornerWeb_" + v, x, y, CEIL, 0, 0, yaw, "Cobweb_%02d" % (i + 1))
    # big spiders: one on the conference ceiling, one crawling down the main office wall, one in the janitor closet
    put("SpiderBig", 4700, 900, CEIL, 180, 0, 200, "BigSpider_1")
    put("SpiderBig", 1938, -3000, 520, 0, -90, 0, "BigSpider_2")
    put("SpiderBig", 4650, -5000, CEIL, 180, 0, 30, "BigSpider_3")
    # spiders dangling on threads
    put("SpiderDangle_A", 3560, -2850, CEIL, 0, 0, 0, "DanglingSpider_1")
    put("SpiderDangle_B", 2350, 400, CEIL, 0, 0, 40, "DanglingSpider_2")
    put("SpiderDangle_A", 1250, -2620, CEIL, 0, 0, 110, "DanglingSpider_3")
    put("SpiderDangle_B", 5600, 300, CEIL, 0, 0, -30, "DanglingSpider_4")
    # claw marks: main office east wall, next to the janitor door, reception
    put("ClawMarks", 4890.5, -1100, 330, 0, 0, -90, "ClawMarks_1")
    put("ClawMarks", 4330, -4139.5, 300, 0, 0, 180, "ClawMarks_2")
    put("ClawMarks", 1900.5, -2550, 310, 0, 0, -90, "ClawMarks_3")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
log("monster dressing: placed %d; still unsaved: %d" % (len(placed), len(left)))
