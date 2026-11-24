"""Play only: jump to the spider task and stand next to spider 1 looking at it."""
import unreal, os, traceback, sys
here = os.path.dirname(os.path.abspath(__file__))
L = []
try:
    step = "2"
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    hud = pc.get_hud()
    if step == "1":
        hud.set_editor_property("TaskIdx", 4)
        L.append("TaskIdx -> %s" % hud.get_editor_property("TaskIdx"))
    else:
        cls = unreal.load_class(None, "/Game/_TASKS/BP_QuestSpider.BP_QuestSpider_C")
        sp = unreal.GameplayStatics.get_all_actors_of_class(gw, cls)
        L.append("spiders: %s" % [(round(s.get_actor_location().x), round(s.get_actor_location().y)) for s in sp])
        if sp:
            s = min(sp, key=lambda a: abs(a.get_actor_location().x - 4410) + abs(a.get_actor_location().y + 900))
            t = s.get_actor_location()
            pawn = pc.get_controlled_pawn() if hasattr(pc, "get_controlled_pawn") else unreal.GameplayStatics.get_player_pawn(gw, 0)
            pawn.set_actor_location(unreal.Vector(t.x + 160, t.y, t.z + 100), False, True)
            pc.set_control_rotation(unreal.Rotator(0, -38, 180))
            L.append("teleported next to %s" % t)
    open(os.path.join(here, "spider_step.txt"), "w").write("2" if step == "1" else "1")
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "spider_tp.log"), "a").write("\n".join(L) + "\n")
