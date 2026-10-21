"""No sky haze indoors, gray overcast instead of orange dusk, cold gray yard fog kept off the building."""
import unreal
SUN_PITCH = -28.0          # afternoon sun hidden behind overcast
SUN_INTENSITY = 2.0
SUN_COLOR = unreal.Color(r=190, g=200, b=215, a=255)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def log(m): unreal.log("[Office80s] " + m)
def try_set(c, prop, val):
    try:
        c.set_editor_property(prop, val); return True
    except Exception as ex:
        log("could not set %s (%s)" % (prop, ex)); return False
with unreal.ScopedEditorTransaction("Office80s overcast sky"):
    for a in sub.get_all_level_actors():
        if isinstance(a, unreal.SkyAtmosphere):
            c = a.get_component_by_class(unreal.SkyAtmosphereComponent)
            a.modify(); c.modify()
            try_set(c, "aerial_perspective_view_distance_scale", 0.0)   # no distance haze on the office interior
            try_set(c, "rayleigh_scattering_scale", 0.012)              # less blue
            try_set(c, "mie_scattering_scale", 0.02)                    # more gray haze in the sky
            try_set(c, "mie_anisotropy", 0.6)
            log("sky atmosphere: haze off, overcast scattering")
        elif isinstance(a, unreal.DirectionalLight):
            c = a.get_component_by_class(unreal.DirectionalLightComponent)
            a.modify(); c.modify()
            r = a.get_actor_rotation()
            a.set_actor_rotation(unreal.Rotator(roll=r.roll, pitch=SUN_PITCH, yaw=r.yaw), False)
            c.set_editor_property("intensity", SUN_INTENSITY)
            c.set_editor_property("light_color", SUN_COLOR)
            log("sun: pitch %.0f, intensity %.1f" % (SUN_PITCH, SUN_INTENSITY))
        elif a.get_actor_label().startswith("YardFog_"):
            c = a.get_component_by_class(unreal.LocalFogVolumeComponent)
            a.modify(); c.modify()
            loc = a.get_actor_location()
            if loc.y > -10000:            # front row: push it further from the building
                a.set_actor_location(unreal.Vector(loc.x, -10400.0, loc.z), False, False)
            try_set(c, "fog_albedo", unreal.LinearColor(0.32, 0.34, 0.37, 1.0))
            try_set(c, "radial_fog_extinction", 0.05)
            try_set(c, "height_fog_extinction", 0.3)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
log("saved")
