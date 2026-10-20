"""Dims the Office (lights, sky light, exposure) and gives BP_TrashBag a real bag mesh.
Safe to re-run: original light values are remembered in actor tags, so it never dims twice."""
import os
import unreal

LIGHT_SCALE = 0.6        # ceiling rect lights
SKY_SCALE = 0.5
EXPOSURE_BIAS = -1.0     # stops; negative = darker
VIGNETTE = 0.55

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(m):
    unreal.log("[Office80s] " + m)


def src_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Office80s_Import")


def original(actor, comp, key):
    tags = list(actor.get_editor_property("tags"))
    for t in tags:
        s = str(t)
        if s.startswith(key + "="):
            return float(s.split("=", 1)[1])
    v = comp.get_editor_property("intensity")
    tags.append(unreal.Name("%s=%s" % (key, v)))
    actor.set_editor_property("tags", tags)
    return v


with unreal.ScopedEditorTransaction("Office80s mood + trash bag"):
    # ---------------- lighting
    n = 0
    for a in sub.get_all_level_actors():
        if isinstance(a, unreal.RectLight):
            c = a.get_component_by_class(unreal.RectLightComponent)
            a.modify(); c.modify()
            c.set_editor_property("intensity", original(a, c, "o80s_int") * LIGHT_SCALE)
            n += 1
        elif isinstance(a, unreal.SkyLight):
            c = a.get_component_by_class(unreal.SkyLightComponent)
            a.modify(); c.modify()
            c.set_editor_property("intensity", original(a, c, "o80s_int") * SKY_SCALE)
        elif isinstance(a, unreal.PostProcessVolume) and a.get_editor_property("unbound"):
            a.modify()
            s = a.get_editor_property("settings")
            s.set_editor_property("override_auto_exposure_bias", True)
            s.set_editor_property("auto_exposure_bias", EXPOSURE_BIAS)
            s.set_editor_property("override_vignette_intensity", True)
            s.set_editor_property("vignette_intensity", VIGNETTE)
            a.set_editor_property("settings", s)
            log("post process: exposure bias %.1f, vignette %.2f" % (EXPOSURE_BIAS, VIGNETTE))
    log("dimmed %d ceiling lights to %.0f%%, sky light to %.0f%%" % (n, LIGHT_SCALE * 100, SKY_SCALE * 100))

    # ---------------- trash bag mesh
    task = unreal.AssetImportTask()
    task.filename = os.path.join(src_dir(), "SM_80s_TrashBag.glb")
    task.destination_path = "/Game/Office80s/Props/SM_80s_TrashBag"
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    bag = None
    for p in unreal.EditorAssetLibrary.list_assets("/Game/Office80s/Props/SM_80s_TrashBag", recursive=True):
        x = unreal.load_asset(p)
        if isinstance(x, unreal.StaticMesh):
            bag = x
    if bag is None:
        raise RuntimeError("trash bag import failed")
    ms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    ms.remove_collisions(bag)
    ms.add_simple_collisions(bag, unreal.ScriptCollisionShapeType.BOX)
    unreal.EditorAssetLibrary.save_loaded_asset(bag)

    bp = unreal.load_asset("/Game/TaskSystem/Tasks/BP_TrashBag")
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    done = set()
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        d = lib.get_data(h)
        o = lib.get_associated_object(d) if hasattr(lib, "get_associated_object") else lib.get_object(d)
        if isinstance(o, unreal.StaticMeshComponent) and o.get_path_name() not in done:
            sm = o.get_editor_property("static_mesh")
            if sm and sm.get_path_name() == "/Engine/BasicShapes/Cube.Cube":
                o.modify()
                o.set_editor_property("static_mesh", bag)
                o.set_editor_property("override_materials", [])
                done.add(o.get_path_name())
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    # placed bags that overrode the mesh per-instance
    fixed = 0
    for a in sub.get_all_level_actors():
        if a.get_class().get_name() == "BP_TrashBag_C":
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                if c.static_mesh and c.static_mesh.get_path_name() == "/Engine/BasicShapes/Cube.Cube":
                    a.modify(); c.modify()
                    c.set_editor_property("static_mesh", bag)
                    fixed += 1
    log("trash bag mesh set on BP_TrashBag (%d template, %d placed overrides)" % (len(done), fixed))

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
log("saved")
