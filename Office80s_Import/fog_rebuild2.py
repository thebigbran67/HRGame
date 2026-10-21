"""Rebuild the yard fog as a grid of smaller volumes that never reach the building."""
import unreal
RADIUS = 1900.0          # cm, each volume
KEEP_OFF = 900.0         # cm, gap between the fog edge and the building wall
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def log(m): unreal.log("[Office80s] " + m)
actors = sub.get_all_level_actors()
old = [a for a in actors if a.get_actor_label().startswith("YardFog_")]
grass = next(a for a in actors if a.get_actor_label() == "grass")
o, e = grass.get_actor_bounds(False)
G = (o.x - e.x, o.y - e.y, o.x + e.x, o.y + e.y)
gz = o.z + e.z
with unreal.ScopedEditorTransaction("Rebuild yard fog"):
    if old:
        sub.destroy_actors(old)
    # a LocalFogVolume at scale 1 is a 5 m radius sphere; read it back if the engine exposes it
    unit = 500.0
    probe = sub.spawn_actor_from_class(unreal.LocalFogVolume, unreal.Vector(0, 0, -100000))
    pc = probe.get_component_by_class(unreal.LocalFogVolumeComponent)
    try:
        lb = pc.get_local_bounds()
        unit = max(lb[1].x, lb[1].y) or unit
    except Exception as ex:
        log("using default fog size (%s)" % ex)
    sub.destroy_actor(probe)
    scale = RADIUS / unit
    ymax = G[3] - KEEP_OFF - RADIUS
    n = 0
    y = ymax
    while y > G[1] + RADIUS * 0.4:
        x = G[0] + RADIUS * 0.7
        while x < G[2] - RADIUS * 0.4:
            f = sub.spawn_actor_from_class(unreal.LocalFogVolume, unreal.Vector(x, y, gz))
            f.set_actor_scale3d(unreal.Vector(scale, scale, scale))
            fc = f.get_component_by_class(unreal.LocalFogVolumeComponent)
            fc.set_editor_property("radial_fog_extinction", 0.12)
            fc.set_editor_property("height_fog_extinction", 0.5)
            fc.set_editor_property("height_fog_falloff", 1000.0)
            fc.set_editor_property("fog_albedo", unreal.LinearColor(0.32, 0.34, 0.37, 1.0))
            n += 1
            f.set_actor_label("YardFog_%02d" % n)
            f.set_folder_path("Office80s/Outdoor/Fog")
            x += RADIUS * 1.3
        y -= RADIUS * 1.3
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
log("yard fog rebuilt: %d volumes, radius %.0f cm (unit %.0f, scale %.2f), nearest edge %.0f cm from the building" % (n, RADIUS, unit, scale, KEEP_OFF))
