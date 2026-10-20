import unreal, sys
# usage: py sun_tune.py pitch   (positive = sun below the horizon)
pitch = float(sys.argv[1])
with unreal.ScopedEditorTransaction("Tune sun angle"):
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if isinstance(a, unreal.DirectionalLight):
            tags = list(a.get_editor_property("tags"))
            if not any(str(t).startswith("o80s_rot=") for t in tags):
                r = a.get_actor_rotation()
                tags.append(unreal.Name("o80s_rot=%.2f,%.2f,%.2f" % (r.pitch, r.yaw, r.roll)))
                a.set_editor_property("tags", tags)
            a.modify()
            r = a.get_actor_rotation()
            a.set_actor_rotation(unreal.Rotator(roll=r.roll, pitch=pitch, yaw=r.yaw), False)
            unreal.log("[Office80s] sun pitch set to %.1f" % pitch)
