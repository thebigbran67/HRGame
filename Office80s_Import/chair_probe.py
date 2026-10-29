import unreal, os
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in sub.get_all_level_actors():
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh and "Chair" in a.static_mesh_component.static_mesh.get_name():
        c = a.static_mesh_component
        l = a.get_actor_location()
        out.append("%s|%s|%.0f,%.0f,%.0f|sim=%s|grav=%s|mob=%s|folder=%s|lin_damp=%.2f" % (
            a.get_actor_label(), c.static_mesh.get_name(), l.x, l.y, l.z,
            c.get_editor_property("body_instance").get_editor_property("simulate_physics"),
            c.get_editor_property("body_instance").get_editor_property("enable_gravity"),
            c.get_editor_property("mobility"), a.get_folder_path(),
            c.get_editor_property("body_instance").get_editor_property("linear_damping")))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "chair_probe.txt"), "w").write("\n".join(out))
unreal.log("[Office80s] chair probe %d" % len(out))
