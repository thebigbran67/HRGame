"""Swap the 'garbagedump' blockout cube for the 80s roll-off dumpster, same spot and footprint."""
import os, unreal
LABEL = "garbagedump"
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def log(m): unreal.log("[Office80s] " + m)
here = os.path.dirname(os.path.abspath(__file__))
t = unreal.AssetImportTask()
t.filename = os.path.join(here, "SM_80s_Dumpster.glb")
t.destination_path = "/Game/Office80s/Outdoor/SM_80s_Dumpster"
t.automated = True; t.replace_existing = True; t.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
mesh = None
for p in unreal.EditorAssetLibrary.list_assets("/Game/Office80s/Outdoor/SM_80s_Dumpster", recursive=True):
    x = unreal.load_asset(p)
    if isinstance(x, unreal.StaticMesh):
        mesh = x
ms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
ms.remove_collisions(mesh)
ms.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX)
unreal.EditorAssetLibrary.save_loaded_asset(mesh)

a = next(x for x in sub.get_all_level_actors() if x.get_actor_label() == LABEL)
comp = a.static_mesh_component
cur = comp.static_mesh
if cur and "SM_80s_Dumpster" in cur.get_path_name():
    log("garbagedump already has the dumpster model")
else:
    b = cur.get_bounding_box()
    s = a.get_actor_scale3d()
    ex = b.max - b.min
    sx, sy = abs(ex.x * s.x), abs(ex.y * s.y)
    center = a.get_actor_transform().transform_location((b.min + b.max) * 0.5)
    bottom = center.z - abs(ex.z * s.z) / 2
    yaw = a.get_actor_rotation().yaw + (0.0 if sx >= sy else 90.0)
    with unreal.ScopedEditorTransaction("Garbage dump model"):
        a.modify(); comp.modify()
        comp.set_editor_property("static_mesh", mesh)
        comp.set_editor_property("override_materials", [])
        a.set_actor_scale3d(unreal.Vector(1, 1, 1))
        a.set_actor_rotation(unreal.Rotator(0, 0, yaw), False)
        a.set_actor_location(unreal.Vector(center.x, center.y, bottom), False, False)
    log("garbagedump -> dumpster (footprint %.0f x %.0f, yaw %.1f)" % (max(sx, sy), min(sx, sy), yaw))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = [p.get_name() for p in list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())]
log("still unsaved: %d %s" % (len(left), left[:5]))
