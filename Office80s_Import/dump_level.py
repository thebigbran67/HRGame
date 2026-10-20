import unreal, json, os
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in sub.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    r = {"label": a.get_actor_label(), "cls": a.get_class().get_name(), "folder": str(a.get_folder_path()),
         "loc": [round(v, 1) for v in (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z)],
         "yaw": round(a.get_actor_rotation().yaw, 2),
         "bmin": [round(o.x - e.x, 1), round(o.y - e.y, 1), round(o.z - e.z, 1)],
         "bmax": [round(o.x + e.x, 1), round(o.y + e.y, 1), round(o.z + e.z, 1)]}
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        c = a.static_mesh_component
        r["mesh"] = c.static_mesh.get_path_name()
        r["mats"] = [m.get_path_name() if m else None for m in c.get_materials()]
    comps = a.get_components_by_class(unreal.LightComponent)
    if comps:
        r["lights"] = [(l.get_class().get_name(), round(l.intensity, 2)) for l in comps]
    out.append(r)
p = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Office80s_Import", "level_dump.json")
json.dump(out, open(p, "w"), indent=0)
unreal.log("[Office80s] dumped %d actors to %s" % (len(out), p))
