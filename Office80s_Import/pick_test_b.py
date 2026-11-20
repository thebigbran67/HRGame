"""Run during Play: did the pickers tag the Play copies and rewrite the card?"""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
L = []
try:
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    L.append("game world: %s" % (gw.get_path_name() if gw else None))
    for tag in ("Picked_Items_2", "Picked_TurnIn_2", "Task_Trash", "Task_Dumpster"):
        a = unreal.GameplayStatics.get_all_actors_with_tag(gw, tag)
        L.append("%s: %d" % (tag, len(a)))
    da = unreal.load_asset("/Game/_TASKS/Tasks/DA_Task_03_TakeOutTrash")
    L.append("card Target/DeliverTo/Meter during play: %s / %s / %s" % (da.get_editor_property("Target"), da.get_editor_property("DeliverTo"), da.get_editor_property("MeterMonster")))
    d1 = unreal.load_asset("/Game/_TASKS/Tasks/DA_Task_01_TalkToBoss")
    L.append("card1 Target: %s" % d1.get_editor_property("Target"))
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "pick_test_b.log"), "w").write("\n".join(L))
