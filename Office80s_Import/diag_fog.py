import unreal
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in sub.get_all_level_actors():
    cls = a.get_class().get_name()
    if "Fog" in cls or "Atmosphere" in cls or "Cloud" in cls or a.get_actor_label().startswith("YardFog") or isinstance(a, unreal.DirectionalLight):
        o, e = a.get_actor_bounds(False)
        unreal.log("[Office80s] %s (%s) rot=%s scale=%s bounds=%s" % (a.get_actor_label(), cls, a.get_actor_rotation(), a.get_actor_scale3d(),
                   [round(v) for v in (o.x - e.x, o.y - e.y, o.z - e.z, o.x + e.x, o.y + e.y, o.z + e.z)]))
