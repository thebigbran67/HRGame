"""Test setup (card NOT saved): fill DA_Task_03's pickers with the real bags / dumpster / janitor; check FindPickedActor wiring."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
L = []
try:
    lsb = unreal.load_object(None, "/Game/Maps/Office.Office:PersistentLevel.Office")
    fed = BGE.get_graph_editor_by_name(lsb, "FindPickedActor")
    for n in fed.list_all_nodes():
        cons = []
        for p in BEL.list_all_pins(n, unreal.EdGraphPinDirection.EGPD_OUTPUT):
            for q in PIN.list_connected_pins(p):
                cons.append("%s->%s.%s" % (PIN.get_pin_name(p), BEL.get_node_title(PIN.get_owning_node(q)), PIN.get_pin_name(q)))
        L.append("FN %s: %s" % (str(BEL.get_node_title(n)).replace("\n", " "), cons))
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    bags = [a for a in acts if a.get_class().get_name() == "BP_TrashBag_C"]
    dump = [a for a in acts if a.get_class().get_name() == "BP_TrashDropOff_C"]
    mons = [a for a in acts if a.get_class().get_name() == "BP_Monster_C"]
    jan = [m for m in mons if "janitor" in str(m.get_editor_property("MonsterName")).lower()]
    L.append("bags %d, dumpsters %d, monsters %s" % (len(bags), len(dump), [str(m.get_editor_property("MonsterName")) for m in mons]))
    da = unreal.load_asset("/Game/_TASKS/Tasks/DA_Task_03_TakeOutTrash")
    da.set_editor_property("ItemsToPickUp", bags)
    if dump: da.set_editor_property("BringItemsTo", dump[0])
    if jan: da.set_editor_property("AngryMonster", jan[0])
    L.append("card items: %d bring: %s angry: %s" % (len(da.get_editor_property("ItemsToPickUp")), da.get_editor_property("BringItemsTo"), da.get_editor_property("AngryMonster")))
    L.append("card Target/DeliverTo/Meter: %s / %s / %s" % (da.get_editor_property("Target"), da.get_editor_property("DeliverTo"), da.get_editor_property("MeterMonster")))
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "pick_test_a.log"), "w").write("\n".join(L))
