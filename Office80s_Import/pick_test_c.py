"""After Play: typed values back? then clear the test picks so the card is exactly as before."""
import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
L = []
da = unreal.load_asset("/Game/_TASKS/Tasks/DA_Task_03_TakeOutTrash")
L.append("after play Target/DeliverTo/Meter: %s / %s / %s" % (da.get_editor_property("Target"), da.get_editor_property("DeliverTo"), da.get_editor_property("MeterMonster")))
da.set_editor_property("ItemsToPickUp", []); da.set_editor_property("BringItemsTo", None); da.set_editor_property("AngryMonster", None)
L.append("test picks cleared: %d items" % len(da.get_editor_property("ItemsToPickUp")))
L.append("saved card: %s" % unreal.EditorAssetLibrary.save_loaded_asset(da))
open(os.path.join(here, "pick_test_c.log"), "w").write("\n".join(L))
