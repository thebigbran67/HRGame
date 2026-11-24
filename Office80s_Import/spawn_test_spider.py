"""Play only: put one quest spider right in front of the camera to see the prompt."""
import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
L = []
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(gw, 0)
cam = unreal.GameplayStatics.get_player_camera_manager(gw, 0)
loc = cam.get_camera_location(); fwd = cam.get_actor_forward_vector()
p = unreal.Vector(loc.x + fwd.x * 160, loc.y + fwd.y * 160, loc.z + fwd.z * 160 - 20)
cls = unreal.load_class(None, "/Game/_TASKS/BP_QuestSpider.BP_QuestSpider_C")
a = unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(gw, cls, unreal.Transform(p, unreal.Rotator(0, 0, 0), unreal.Vector(1, 1, 1)), unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN)
unreal.GameplayStatics.finish_spawning_actor(a, unreal.Transform(p, unreal.Rotator(0, 0, 0), unreal.Vector(1, 1, 1)))
L.append("spawned %s at %s" % (a, p))
open(os.path.join(here, "spawn_test_spider.log"), "w").write("\n".join(L))
