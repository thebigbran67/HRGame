import unreal, json, os
bp = unreal.load_asset("/Game/Maps/BP_CubeDoor")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
out = {"components": [], "vars": [], "functions": []}
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    d = lib.get_data(h)
    o = lib.get_associated_object(d)
    if o is None:
        continue
    r = {"name": str(lib.get_variable_name(d)), "cls": o.get_class().get_name()}
    if isinstance(o, unreal.SceneComponent):
        for k in ("relative_location", "relative_rotation", "relative_scale3d"):
            v = o.get_editor_property(k)
            r[k] = [round(getattr(v, a), 3) for a in (("x", "y", "z") if k != "relative_rotation" else ("pitch", "yaw", "roll"))]
        try:
            r["parent"] = str(lib.get_variable_name(lib.get_data(lib.get_parent_handle(d)))) if hasattr(lib, "get_parent_handle") else None
        except Exception:
            pass
    if isinstance(o, unreal.StaticMeshComponent):
        sm = o.get_editor_property("static_mesh")
        r["mesh"] = sm.get_path_name() if sm else None
        if sm:
            b = sm.get_bounding_box()
            r["mesh_bounds"] = [round(b.min.x, 1), round(b.min.y, 1), round(b.min.z, 1), round(b.max.x, 1), round(b.max.y, 1), round(b.max.z, 1)]
        r["mats"] = [m.get_path_name() if m else None for m in o.get_editor_property("override_materials")]
        r["collision"] = str(o.get_collision_profile_name())
    out["components"].append(r)
# placed instance
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_class().get_name() == "BP_CubeDoor_C":
        t = a.get_actor_transform()
        out["instance"] = {"label": a.get_actor_label(), "loc": str(a.get_actor_location()), "rot": str(a.get_actor_rotation()), "scale": str(a.get_actor_scale3d())}
        out["instance_comps"] = []
        for c in a.get_components_by_class(unreal.SceneComponent):
            w = c.get_world_location()
            e = {"name": c.get_name(), "cls": c.get_class().get_name(), "world": [round(w.x), round(w.y), round(w.z)],
                 "rel_scale": str(c.get_editor_property("relative_scale3d"))}
            if isinstance(c, unreal.StaticMeshComponent) and c.static_mesh:
                e["mesh"] = c.static_mesh.get_path_name()
            out["instance_comps"].append(e)
# graph text: export the blueprint so we can see what moves
try:
    gen = bp.generated_class()
    cdo = unreal.get_default_object(gen)
    for p in dir(cdo):
        pass
except Exception:
    pass
p = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Office80s_Import", "door.json")
json.dump(out, open(p, "w"), indent=1, default=str)
# also export the blueprint as text (T3D) for the graph
try:
    task = unreal.AssetExportTask()
    task.object = bp
    task.filename = os.path.join(os.path.dirname(p), "BP_CubeDoor.t3d")
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    task.exporter = None
    unreal.Exporter.run_asset_export_task(task)
except Exception as ex:
    unreal.log_warning("[Office80s] export failed %s" % ex)
unreal.log("[Office80s] door inspected")
