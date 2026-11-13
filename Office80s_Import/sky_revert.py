"""Undoes night_sky.py: restores the sun angle/intensity and sky light from the saved tags, removes MoonLight."""
import os, unreal
here = os.path.dirname(os.path.abspath(__file__))
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))
def pop(a, key):
    tags = list(a.get_editor_property("tags")); val = None; keep = []
    for t in tags:
        s = str(t)
        if s.startswith(key + "="):
            val = s.split("=", 1)[1]
        else:
            keep.append(t)
    a.set_editor_property("tags", keep)
    return val
try:
    with unreal.ScopedEditorTransaction("Restore sky"):
        for a in sub.get_all_level_actors():
            if a.get_actor_label() == "MoonLight":
                sub.destroy_actor(a); log("moonlight removed"); continue
            if isinstance(a, unreal.DirectionalLight):
                c = a.get_component_by_class(unreal.DirectionalLightComponent); a.modify(); c.modify()
                r = pop(a, "o80s_night_rot"); i = pop(a, "o80s_night_int")
                if r:
                    p, y, rl = [float(v) for v in r.split(",")]
                    a.set_actor_rotation(unreal.Rotator(roll=rl, pitch=p, yaw=y), False)
                if i:
                    c.set_editor_property("intensity", float(i))
                log("sun restored: rot %s int %s" % (r, i))
            elif isinstance(a, unreal.SkyLight):
                c = a.get_component_by_class(unreal.SkyLightComponent); a.modify(); c.modify()
                i = pop(a, "o80s_night_int")
                if i:
                    c.set_editor_property("intensity", float(i))
                try:
                    c.recapture_sky()
                except Exception:
                    pass
                log("sky light restored: %s" % i)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "sky_revert.log"), "w").write("\n".join(LOG))
