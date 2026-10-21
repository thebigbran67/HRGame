"""Give BP_CubeDoor a real door. Keeps the hinge and the E-to-open swing exactly as before."""
import os, unreal
def log(m): unreal.log("[Office80s] " + m)
here = os.path.dirname(os.path.abspath(__file__))
t = unreal.AssetImportTask()
t.filename = os.path.join(here, "SM_80s_EntranceDoor.glb")
t.destination_path = "/Game/Office80s/Props/SM_80s_EntranceDoor"
t.automated = True; t.replace_existing = True; t.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
door = None
for p in unreal.EditorAssetLibrary.list_assets("/Game/Office80s/Props/SM_80s_EntranceDoor", recursive=True):
    x = unreal.load_asset(p)
    if isinstance(x, unreal.StaticMesh):
        door = x
ms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
ms.remove_collisions(door)
ms.add_simple_collisions(door, unreal.ScriptCollisionShapeType.BOX)
unreal.EditorAssetLibrary.save_loaded_asset(door)

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
inst = [a for a in sub.get_all_level_actors() if a.get_class().get_name() == "BP_CubeDoor_C"]
S = inst[0].get_actor_scale3d() if inst else unreal.Vector(1, 1, 1)
log("placed door scale was %s" % S)

bp = unreal.load_asset("/Game/Maps/BP_CubeDoor")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
seen = set()
with unreal.ScopedEditorTransaction("Entrance door model"):
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        o = lib.get_associated_object(lib.get_data(h))
        if o is None or o.get_path_name() in seen:
            continue
        seen.add(o.get_path_name())
        if isinstance(o, unreal.StaticMeshComponent) and o.get_editor_property("static_mesh") and \
                o.get_editor_property("static_mesh").get_path_name() == "/Engine/BasicShapes/Cube.Cube":
            o.modify()
            o.set_editor_property("static_mesh", door)
            o.set_editor_property("override_materials", [])
            o.set_editor_property("relative_location", unreal.Vector(0, 0, 0))
            o.set_editor_property("relative_scale3d", unreal.Vector(1, 1, 1))
            log("door mesh set on the blueprint")
        elif isinstance(o, unreal.TextRenderComponent):
            o.modify()
            l = o.get_editor_property("relative_location")
            sc = o.get_editor_property("relative_scale3d")
            o.set_editor_property("relative_location", unreal.Vector(l.x * S.x, l.y * S.y, l.z * S.z))
            o.set_editor_property("relative_scale3d", unreal.Vector(sc.x * S.x, sc.y * S.y, sc.z * S.z))
            log("prompt text kept in place")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    for a in inst:
        a.modify()
        a.set_actor_scale3d(unreal.Vector(1, 1, 1))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = [p.get_name() for p in list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())]
log("door done; still unsaved: %d %s" % (len(left), left[:5]))
