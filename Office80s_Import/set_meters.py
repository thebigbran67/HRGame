"""Logs tasks 04-08, then sets the frustration meter monster on Remove Spiders (Gioh) and Fire Gus (Boss). Nothing else changes."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
EAL = unreal.EditorAssetLibrary
L = []
F = ("Title", "Type", "Target", "MeterMonster", "MeterSeconds", "CalmAmount", "AngryMonster")
try:
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    names = [str(a.get_editor_property("MonsterName")) for a in acts if a.get_class().get_name() == "BP_Monster_C"]
    L.append("monster names in level: %s" % names)
    for n in ("04_TalkToGioh", "05_RemoveSpiders", "06_ReturnToGioh", "07_BossFiringAssignment", "08_FireGus"):
        da = unreal.load_asset("/Game/_TASKS/Tasks/DA_Task_" + n)
        L.append("%s: %s" % (n, {f: str(da.get_editor_property(f)) for f in F}))
    for n, who in (("05_RemoveSpiders", "Receptionist Gioh"), ("08_FireGus", "Boss")):
        if who not in names:
            L.append("SKIP %s: no monster named %s in the level" % (n, who)); continue
        da = unreal.load_asset("/Game/_TASKS/Tasks/DA_Task_" + n)
        da.set_editor_property("MeterMonster", who)
        L.append("set %s MeterMonster=%s, saved=%s" % (n, who, EAL.save_loaded_asset(da)))
    lst = unreal.load_asset("/Game/_TASKS/DA_TaskManager")
    L.append("task order: %s" % [t.get_name() if t else None for t in lst.get_editor_property("Tasks")])
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "set_meters.log"), "w").write("\n".join(L))
