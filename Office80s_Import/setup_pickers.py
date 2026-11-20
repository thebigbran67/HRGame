"""Adds the level pickers to BPD_Task (copying TalkTo's Actor soft-reference type), sets categories.
Only adds variables / changes categories; existing card values stay."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; EAL = unreal.EditorAssetLibrary
LOG = []
def log(m): LOG.append(str(m)); unreal.log("[Pickers] " + str(m))
CATS = {
    "Title": "Task Basics", "Type": "Task Basics", "MustAccept": "Task Basics", "Count": "Task Basics",
    "DeliverTitle": "Task Basics", "DeliverPrompt": "Task Basics",
    "TalkTo": "Pick From Level", "ItemsToPickUp": "Pick From Level", "BringItemsTo": "Pick From Level",
    "GoToPlace": "Pick From Level", "AngryMonster": "Pick From Level",
    "MeterSeconds": "Frustration Meter", "CalmAmount": "Frustration Meter",
    "Target": "Old Way (typed tags)", "DeliverTo": "Old Way (typed tags)", "MeterMonster": "Old Way (typed tags)",
}
try:
    bp = unreal.load_asset("/Game/_TASKS/BPD_Task")
    t = BEL.get_member_variable_type(bp, "TalkTo")
    log("TalkTo type json: %s" % BEL.pin_type_to_json_schema(t))
    have = [str(x) for x in BEL.list_member_variable_names(bp)]
    for name, arr in (("ItemsToPickUp", True), ("BringItemsTo", False), ("GoToPlace", False), ("AngryMonster", False)):
        if name not in have:
            log("add %s: %s" % (name, BEL.add_member_variable(bp, name, BEL.get_array_type(t) if arr else t)))
    for name, cat in CATS.items():
        BEL.set_blueprint_variable_instance_editable(bp, name, True)
        BEL.set_blueprint_variable_category(bp, name, cat)
    try:
        nv = bp.get_editor_property("new_variables"); log("new_variables readable: %d" % len(nv))
    except Exception as e:
        log("new_variables not readable: %s" % e)
    BEL.compile_blueprint(bp)
    log("vars now: %s" % [str(x) for x in BEL.list_member_variable_names(bp)])
    for name in ("ItemsToPickUp", "AngryMonster"):
        log("%s type json: %s" % (name, BEL.pin_type_to_json_schema(BEL.get_member_variable_type(bp, name))))
    log("saved: %s" % EAL.save_loaded_asset(bp))
except Exception:
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "setup_pickers.log"), "w").write("\n".join(LOG))
