import unreal, json, os
out = {}
bp = unreal.load_asset("/Game/TaskSystem/Tasks/BP_TrashBag")
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
comps = []
for h in sub.k2_gather_subobject_data_for_blueprint(bp):
    d = lib.get_data(h)
    o = lib.get_associated_object(d) if hasattr(lib, "get_associated_object") else lib.get_object(d)
    r = {"name": str(lib.get_variable_name(d)), "cls": o.get_class().get_name() if o else None}
    if isinstance(o, unreal.StaticMeshComponent):
        sm = o.get_editor_property("static_mesh")
        r["mesh"] = sm.get_path_name() if sm else None
        r["mats"] = [m.get_path_name() if m else None for m in o.get_editor_property("override_materials")]
        r["scale"] = str(o.get_editor_property("relative_scale3d"))
        r["loc"] = str(o.get_editor_property("relative_location"))
        r["coll"] = str(o.get_editor_property("body_instance").get_editor_property("collision_profile_name"))
    if isinstance(o, unreal.SceneComponent):
        r["rel_loc"] = str(o.get_editor_property("relative_location"))
    comps.append(r)
out["trashbag"] = comps
lights = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    for c in a.get_components_by_class(unreal.LightComponent):
        lights.append([a.get_actor_label(), c.get_class().get_name(), c.get_editor_property("intensity"),
                       str(c.get_editor_property("light_color")), str(a.get_editor_property("tags"))])
    if isinstance(a, unreal.SkyLight):
        c = a.get_component_by_class(unreal.SkyLightComponent)
        lights.append([a.get_actor_label(), "SkyLight", c.get_editor_property("intensity"), "", ""])
    if isinstance(a, unreal.PostProcessVolume):
        s = a.get_editor_property("settings")
        out["ppv"] = {"label": a.get_actor_label(), "unbound": a.get_editor_property("unbound"),
                      "bias_on": s.get_editor_property("override_auto_exposure_bias"),
                      "bias": s.get_editor_property("auto_exposure_bias"),
                      "method_on": s.get_editor_property("override_auto_exposure_method"),
                      "method": str(s.get_editor_property("auto_exposure_method"))}
out["lights"] = lights
p = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Office80s_Import", "inspect2.json")
json.dump(out, open(p, "w"), indent=1, default=str)
unreal.log("[Office80s] inspect written")
