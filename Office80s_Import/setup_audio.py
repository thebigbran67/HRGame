"""Imports the Office sound effects, places a looping 2D ambience, and tags the floating physics chairs."""
import os, unreal
here = os.path.dirname(os.path.abspath(__file__))
DEST = "/Game/Office80s/Audio"
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))
try:
    tasks = []
    for n in ("SFX_80s_OfficeAmbience", "SFX_80s_TrashPickup", "SFX_80s_DumpsterDrop", "SFX_80s_Footstep", "SFX_80s_ChairBonk"):
        t = unreal.AssetImportTask(); t.filename = os.path.join(here, n + ".wav"); t.destination_path = DEST
        t.destination_name = n; t.automated = True; t.replace_existing = True; t.save = True
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    amb = unreal.load_asset(DEST + "/SFX_80s_OfficeAmbience")
    amb.set_editor_property("looping", True)
    unreal.EditorAssetLibrary.save_loaded_asset(amb)
    for n in ("SFX_80s_TrashPickup", "SFX_80s_DumpsterDrop", "SFX_80s_Footstep", "SFX_80s_ChairBonk"):
        log("%s: %s" % (n, unreal.load_asset(DEST + "/" + n)))
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    old = [a for a in sub.get_all_level_actors() if a.get_actor_label() == "OfficeAmbience"]
    if old:
        sub.destroy_actors(old)
    a = sub.spawn_actor_from_class(unreal.AmbientSound, unreal.Vector(3500, -2000, 500))
    ac = a.get_component_by_class(unreal.AudioComponent)
    ac.set_editor_property("sound", amb)
    ac.set_editor_property("allow_spatialization", False)
    ac.set_editor_property("volume_multiplier", 0.6)
    ac.set_editor_property("auto_activate", True)
    a.set_actor_label("OfficeAmbience"); a.set_folder_path("Office80s/Audio")
    try:
        a.set_editor_property("is_spatially_loaded", False)
    except Exception as e:
        log("ambience spatial flag: %s" % e)
    n = 0
    for c in sub.get_all_level_actors():
        if isinstance(c, unreal.StaticMeshActor) and c.static_mesh_component.static_mesh and "Chair" in c.static_mesh_component.static_mesh.get_name():
            if c.static_mesh_component.get_editor_property("body_instance").get_editor_property("simulate_physics"):
                tags = list(c.get_editor_property("tags"))
                if "BonkChair" not in [str(x) for x in tags]:
                    c.modify(); tags.append(unreal.Name("BonkChair")); c.set_editor_property("tags", tags)
                n += 1
    log("tagged %d floating chairs" % n)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("audio setup done")
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "setup_audio.log"), "w").write("\n".join(LOG))
