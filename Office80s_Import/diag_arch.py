import unreal, json, os
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in sub.get_all_level_actors():
    if not isinstance(a, unreal.StaticMeshActor) or not a.static_mesh_component.static_mesh:
        continue
    mp = a.static_mesh_component.static_mesh.get_path_name()
    o, e = a.get_actor_bounds(False)
    b = [round(v, 1) for v in (o.x - e.x, o.y - e.y, o.z - e.z, o.x + e.x, o.y + e.y, o.z + e.z)]
    lab = a.get_actor_label()
    if mp.startswith("/Game/LevelPrototyping/Meshes/SM_Cube.") or lab.startswith("ConfTable") or "Arch" in lab:
        out.append([lab, mp.split("/")[-1], b, str(a.get_folder_path())])
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diag_arch.json")
json.dump(out, open(p, "w"), indent=0)
unreal.log("[Office80s] diag_arch %d" % len(out))
