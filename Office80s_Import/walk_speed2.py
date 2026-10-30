"""Slow the player down everywhere: character default + every blueprint node that restores the walk speed."""
import unreal, os
BEL = unreal.BlueprintEditorLibrary; PIN = unreal.BlueprintGraphPinLibrary; BGE = unreal.BlueprintGraphEditor
NEW = 650.0
out = []
bp = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    o = lib.get_associated_object(lib.get_data(h)) if hasattr(lib, "get_associated_object") else lib.get_object(lib.get_data(h))
    if isinstance(o, unreal.CharacterMovementComponent):
        out.append("character template %s -> %s" % (o.get_editor_property("max_walk_speed"), NEW))
        o.modify(); o.set_editor_property("max_walk_speed", NEW)
cdo = unreal.get_default_object(BEL.generated_class(bp))
cdo.get_editor_property("character_movement").set_editor_property("max_walk_speed", NEW)
BEL.compile_blueprint(bp); unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
for wp in ("/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk", "/Game/Dialogue/Widgets/W_MonsterTalk"):
    if not unreal.EditorAssetLibrary.does_asset_exist(wp):
        continue
    w = unreal.load_asset(wp)
    if not isinstance(w, unreal.Blueprint):
        continue
    changed = 0
    for g in BEL.list_graphs(w):
        ed = BGE.get_graph_editor(g)
        for n in ed.list_all_nodes():
            for pin in BEL.list_all_pins(n):
                if str(PIN.get_pin_name(pin)) == "MaxWalkSpeed" and PIN.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_INPUT and not PIN.list_connected_pins(pin):
                    v = float(PIN.get_pin_value(pin) or 0)
                    if v > 1.0:   # leave the 0 'freeze while talking' nodes alone
                        PIN.set_pin_value(pin, str(NEW)); changed += 1
                        out.append("%s %s %s -> %s" % (wp, n.get_name(), v, NEW))
    if changed:
        BEL.compile_blueprint(w); unreal.EditorAssetLibrary.save_loaded_asset(w, False)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "walk_speed2.log"), "w").write("\n".join(out))
unreal.log("[Office80s] walk speed done")
