"""One-shot: outdoor-only fog, no sky haze indoors, gray afternoon sun. Reports anything that fails to save."""
import unreal
RADIUS = 1900.0           # cm per fog volume
KEEP_OFF = 900.0          # cm between the fog edge and the building
UNIT = 500.0              # LocalFogVolume radius at scale 1
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def log(m): unreal.log("[Office80s] " + m)
def try_set(c, p, v):
    try:
        c.set_editor_property(p, v); return True
    except Exception as ex:
        log("could not set %s: %s" % (p, ex)); return False

actors = sub.get_all_level_actors()
grass = next(a for a in actors if a.get_actor_label() == "grass")
o, e = grass.get_actor_bounds(False)
G = (o.x - e.x, o.y - e.y, o.x + e.x, o.y + e.y)
gz = o.z + e.z
with unreal.ScopedEditorTransaction("Office80s outdoor-only fog"):
    fogs = [a for a in actors if isinstance(a, unreal.LocalFogVolume) or a.get_class().get_name() == "ExponentialHeightFog"]
    sub.destroy_actors(fogs)
    log("removed %d old fog actors" % len(fogs))
    scale = RADIUS / UNIT
    n = 0
    y = G[3] - KEEP_OFF - RADIUS
    while y > G[1] + RADIUS * 0.4:
        x = G[0] + RADIUS * 0.7
        while x < G[2] - RADIUS * 0.4:
            f = sub.spawn_actor_from_class(unreal.LocalFogVolume, unreal.Vector(x, y, gz))
            f.set_actor_scale3d(unreal.Vector(scale, scale, scale))
            c = f.get_component_by_class(unreal.LocalFogVolumeComponent)
            try_set(c, "radial_fog_extinction", 0.12)
            try_set(c, "height_fog_extinction", 0.5)
            try_set(c, "height_fog_falloff", 1000.0)
            try_set(c, "fog_albedo", unreal.LinearColor(0.32, 0.34, 0.37, 1.0))
            n += 1
            f.set_actor_label("YardFog_%02d" % n)
            f.set_folder_path("Office80s/Outdoor/Fog")
            x += RADIUS * 1.3
        y -= RADIUS * 1.3
    log("built %d outdoor fog volumes (radius %.0f cm, edge %.0f cm from the building)" % (n, RADIUS, KEEP_OFF))
    for a in actors:
        if isinstance(a, unreal.SkyAtmosphere):
            c = a.get_component_by_class(unreal.SkyAtmosphereComponent)
            a.modify(); c.modify()
            try_set(c, "aerial_pespective_view_distance_scale", 0.0)
            try_set(c, "aerial_perspective_start_depth", 2.0)
            log("sky haze off")
        elif isinstance(a, unreal.DirectionalLight):
            c = a.get_component_by_class(unreal.DirectionalLightComponent)
            a.modify(); c.modify()
            r = a.get_actor_rotation()
            a.set_actor_rotation(unreal.Rotator(roll=r.roll, pitch=-28.0, yaw=r.yaw), False)
            c.set_editor_property("intensity", 2.0)
            c.set_editor_property("light_color", unreal.Color(r=190, g=200, b=215, a=255))
            log("sun: afternoon angle, dim, cool")

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = [p.get_name() for p in list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())]
log("still unsaved after save: %d %s" % (len(left), left[:6]))
