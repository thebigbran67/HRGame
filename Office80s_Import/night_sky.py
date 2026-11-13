"""Turns the purple dusk into a dark night: sun dropped below the horizon, a dim cold moonlight from the
moon's direction, softer sky light. Originals are saved in actor tags (o80s_night_*)."""
import os, unreal
here = os.path.dirname(os.path.abspath(__file__))
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))
def remember(a, key, val):
    tags = list(a.get_editor_property("tags"))
    if not any(str(t).startswith(key + "=") for t in tags):
        tags.append(unreal.Name("%s=%s" % (key, val))); a.set_editor_property("tags", tags)
try:
    with unreal.ScopedEditorTransaction("Night sky"):
        old = [a for a in sub.get_all_level_actors() if a.get_actor_label() == "MoonLight"]
        if old:
            sub.destroy_actors(old)
        for a in sub.get_all_level_actors():
            if isinstance(a, unreal.DirectionalLight):
                c = a.get_component_by_class(unreal.DirectionalLightComponent)
                r = a.get_actor_rotation(); a.modify(); c.modify()
                remember(a, "o80s_night_rot", "%.2f,%.2f,%.2f" % (r.pitch, r.yaw, r.roll))
                remember(a, "o80s_night_int", "%.3f" % c.get_editor_property("intensity"))
                a.set_actor_rotation(unreal.Rotator(roll=r.roll, pitch=9.0, yaw=r.yaw), False)
                c.set_editor_property("intensity", 0.05)
                log("sun below the horizon (was pitch %.1f)" % r.pitch)
            elif isinstance(a, unreal.SkyLight):
                c = a.get_component_by_class(unreal.SkyLightComponent); a.modify(); c.modify()
                remember(a, "o80s_night_int", "%.3f" % c.get_editor_property("intensity"))
                c.set_editor_property("intensity", 0.35)
                try:
                    c.recapture_sky()
                except Exception as e:
                    log("recapture: %s" % e)
                log("sky light dimmed")
        m = sub.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(-2000, 14000, 3000), unreal.Rotator(roll=0, pitch=-32.0, yaw=-100.0))
        mc = m.get_component_by_class(unreal.DirectionalLightComponent)
        mc.set_editor_property("intensity", 0.35)
        mc.set_editor_property("light_color", unreal.Color(r=150, g=172, b=235, a=255))
        for p in ("atmosphere_sun_light", "b_atmosphere_sun_light"):
            try:
                mc.set_editor_property(p, False); break
            except Exception:
                pass
        mc.set_editor_property("cast_shadows", True)
        m.set_actor_label("MoonLight"); m.set_folder_path("Office80s/OutsideSpooky/Lights")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("night sky done")
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "night_sky.log"), "w").write("\n".join(LOG))
