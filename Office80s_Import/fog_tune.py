import unreal, sys
# usage: py fog_tune.py radial height albedo
radial, height, alb = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
n = 0
with unreal.ScopedEditorTransaction("Tune yard fog"):
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label().startswith("YardFog_"):
            c = a.get_component_by_class(unreal.LocalFogVolumeComponent)
            a.modify(); c.modify()
            c.set_editor_property("radial_fog_extinction", radial)
            c.set_editor_property("height_fog_extinction", height)
            c.set_editor_property("fog_albedo", unreal.LinearColor(alb, alb * 1.08, alb * 1.2, 1.0))
            n += 1
unreal.log("[Office80s] fog tuned on %d volumes: radial %.3f height %.3f albedo %.2f" % (n, radial, height, alb))
