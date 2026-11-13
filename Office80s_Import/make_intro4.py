"""Intro cinematic: the player's car drives in off the street, turns into the lot and parks by the
front door (wide shot, then the driver's-eye view), engine/blinker/door audio, fade in and out.
Auto-plays at the start, hides the HUD and player and blocks input while it runs.
Re-runnable: rebuilds /Game/Office80s/Intro/LS_Intro and the Office80s/Intro actors."""
import os, json, unreal
here = os.path.dirname(os.path.abspath(__file__))
FOLDER = "Office80s/Intro"
DEST = "/Game/Office80s/Intro"
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))
K = json.load(open(os.path.join(here, "intro_keys.json")))

def imp(fname, dest):
    t = unreal.AssetImportTask()
    t.filename = os.path.join(here, fname); t.destination_path = dest
    t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t])

def key_transform(binding, keys, f0, f1):
    tr = binding.add_track(unreal.MovieScene3DTransformTrack)
    sec = tr.add_section()
    sec.set_range(f0, f1)
    ch = sec.get_all_channels()
    names = [str(c.get_name()) for c in ch]
    idx = {}
    for want, i in (("Location.X", 0), ("Location.Y", 1), ("Location.Z", 2), ("Rotation.X", 3), ("Rotation.Y", 4), ("Rotation.Z", 5)):
        idx[i] = next((j for j, n in enumerate(names) if n == want), i)
    lin = unreal.MovieSceneKeyInterpolation.LINEAR
    for f in range(f0, f1):
        k = keys[f]
        for i in range(6):
            ch[idx[i]].add_key(unreal.FrameNumber(f), float(k[i]), 0.0, unreal.MovieSceneTimeUnit.DISPLAY_RATE, lin)
    return names

def binding_id(seq, b):
    for fn in (lambda: unreal.MovieSceneSequenceExtensions.get_portable_binding_id(seq, seq, b),
               lambda: seq.get_portable_binding_id(seq, b),
               lambda: unreal.MovieSceneSequenceExtensions.get_binding_id(seq, b),
               lambda: seq.get_binding_id(b)):
        try:
            r = fn()
            if r is not None:
                return r
        except Exception:
            pass
    raise RuntimeError("no binding id api")

def try_set(obj, names, value):
    for n in names:
        try:
            obj.set_editor_property(n, value); return n
        except Exception:
            pass
    return None

def main():
    # hearse windows were too neon; headlights a bit softer
    t = unreal.AssetImportTask()
    imp("SM_80s_Car_Hearse.glb", "/Game/Office80s/Front/SM_80s_Car_Hearse")
    imp("SM_80s_Car_Player.glb", "/Game/Office80s/Front/SM_80s_Car_Player")
    imp("SFX_80s_CarIntro.wav", DEST)
    snd = unreal.load_asset(DEST + "/SFX_80s_CarIntro")
    acts = sub.get_all_level_actors()
    car = next(a for a in acts if a.get_actor_label() == "Car_Player")
    for a in acts:
        if a.get_actor_label().startswith("Car_Player_Headlight"):
            a.spot_light_component.set_editor_property("intensity", 25.0)

    with unreal.ScopedEditorTransaction("Intro"):
        old = [a for a in sub.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]
        if old:
            sub.destroy_actors(old)
        seq = None
        for i in range(2, 30):
            name = "LS_Intro_v%d" % i
            if not unreal.EditorAssetLibrary.does_asset_exist(DEST + "/" + name):
                seq = tools.create_asset(name, DEST, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
                if seq:
                    log("new sequence " + name); break
        if seq is None:
            raise RuntimeError("could not create a level sequence asset")
        seq.set_display_rate(unreal.FrameRate(K["fps"], 1))
        N = K["frames"]
        seq.set_playback_start(0); seq.set_playback_end(N)

        def camera(label, focal):
            c = sub.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(0, 0, 200))
            cc = c.get_cine_camera_component()
            cc.set_editor_property("current_focal_length", focal)
            fs = cc.get_editor_property("focus_settings")
            fs.set_editor_property("focus_method", unreal.CameraFocusMethod.DISABLE)
            cc.set_editor_property("focus_settings", fs)
            c.set_actor_label(label); c.set_folder_path(FOLDER)
            return c
        wide = camera("IntroCam_Wide", 22.0)
        pov = camera("IntroCam_Driver", 16.0)
        wide.set_actor_location(unreal.Vector(*K["wide"][0][:3]), False, True)
        pov.set_actor_location(unreal.Vector(*K["pov"][-1][:3]), False, True)

        b_car = seq.add_possessable(car)
        names = key_transform(b_car, K["car"], 0, N)
        log("transform channels: %s" % names)
        b_w = seq.add_possessable(wide); key_transform(b_w, K["wide"], 0, K["cut"] + 1)
        b_p = seq.add_possessable(pov); key_transform(b_p, K["pov"], K["cut"], N)

        cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
        s1 = cut.add_section(); s1.set_range(0, K["cut"]); s1.set_camera_binding_id(binding_id(seq, b_w))
        s2 = cut.add_section(); s2.set_range(K["cut"], N); s2.set_camera_binding_id(binding_id(seq, b_p))

        fd = seq.add_track(unreal.MovieSceneFadeTrack)
        fs = fd.add_section(); fs.set_range(0, N)
        fch = fs.get_all_channels()[0]
        for f, v in K["fade"]:
            fch.add_key(unreal.FrameNumber(int(f)), float(v), 0.0, unreal.MovieSceneTimeUnit.DISPLAY_RATE, unreal.MovieSceneKeyInterpolation.LINEAR)

        au = seq.add_track(unreal.MovieSceneAudioTrack)
        asec = au.add_section(); asec.set_range(0, N)
        try:
            asec.set_sound(snd)
        except Exception as e:
            log("audio set_sound: %s" % e)
        unreal.EditorAssetLibrary.save_loaded_asset(seq)

        lsa = sub.spawn_actor_from_class(unreal.LevelSequenceActor, unreal.Vector(1750, -6800, 200))
        lsa.set_sequence(seq)
        lsa.set_actor_label("IntroSequence"); lsa.set_folder_path(FOLDER)
        lsa.set_editor_property("tags", [unreal.Name("IntroSeq")])
        ps = lsa.get_editor_property("playback_settings")
        done = {}
        for prop, names_ in (("autoplay", ("auto_play", "b_auto_play")), ("move", ("disable_movement_input", "b_disable_movement_input")),
                             ("look", ("disable_look_at_input", "b_disable_look_at_input")), ("hideplayer", ("hide_player", "b_hide_player")),
                             ("hidehud", ("hide_hud", "b_hide_hud"))):
            done[prop] = try_set(ps, names_, True)
        lsa.set_editor_property("playback_settings", ps)
        if not done["autoplay"]:
            done["autoplay_actor"] = try_set(lsa, ("auto_play", "b_auto_play"), True)
        log("playback settings: %s" % done)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("intro built: %d frames (%.1fs), cut at frame %d" % (N, N / K["fps"], K["cut"]))

try:
    main()
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "make_intro.log"), "w").write("\n".join(LOG))
