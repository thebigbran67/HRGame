import unreal, sys
x, y, z, yaw = [float(v) for v in sys.argv[1:5]]
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if isinstance(a, unreal.PlayerStart):
        a.set_actor_location(unreal.Vector(x, y, z), False, True); a.set_actor_rotation(unreal.Rotator(0, 0, yaw), True)
        unreal.log("[Office80s] PlayerStart at %s" % a.get_actor_location())
