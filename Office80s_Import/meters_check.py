import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
L = []
for c in ("DA_Task_03_TakeOutTrash", "DA_Task_05_RemoveSpiders", "DA_Task_08_FireGus"):
    d = unreal.load_asset("/Game/_TASKS/Tasks/" + c)
    L.append("%s: MeterMonster=%s MeterSeconds=%s" % (c, d.get_editor_property("MeterMonster"), d.get_editor_property("MeterSeconds")))
open(os.path.join(here, "meters_check.log"), "w").write("\n".join(L))
