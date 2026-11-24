import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
L = []
try:
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    cam = unreal.GameplayStatics.get_player_camera_manager(gw, 0)
    loc = cam.get_camera_location(); rot = cam.get_camera_rotation()
    fwd = unreal.MathLibrary.get_forward_vector(rot)
    p = unreal.Vector(loc.x + fwd.x * 150, loc.y + fwd.y * 150, loc.z + fwd.z * 150)
    cls = unreal.load_class(None, "/Game/_TASKS/BP_QuestSpider.BP_QuestSpider_C")
    a = gw.spawn_actor(cls, p, unreal.Rotator(0, 0, 0)) if hasattr(gw, "spawn_actor") else None
    if a is None:
        a = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, p) if False else None
    if a is None:
        t = unreal.Transform(location=p)
        a = unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(gw, cls, t, unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN)
        a = unreal.GameplayStatics.finish_spawning_actor(a, t)
    L.append("spawned %s at %s" % (a, p))
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "spawn_test_spider2.log"), "w").write("\n".join(L))
