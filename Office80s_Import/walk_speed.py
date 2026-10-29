import unreal, os
BEL = unreal.BlueprintEditorLibrary; PIN = unreal.BlueprintGraphPinLibrary; BGE = unreal.BlueprintGraphEditor
SPEED = 850.0
out = []
# character movement template
bp = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    o = lib.get_object(lib.get_data(h))
    if isinstance(o, unreal.CharacterMovementComponent):
        out.append("template walk speed was %s" % o.get_editor_property("max_walk_speed"))
        o.set_editor_property("max_walk_speed", SPEED)
cdo = unreal.get_default_object(BEL.generated_class(bp))
cm = cdo.get_editor_property("character_movement")
out.append("cdo walk speed was %s" % cm.get_editor_property("max_walk_speed"))
cm.set_editor_property("max_walk_speed", SPEED)
BEL.compile_blueprint(bp); unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
# dialogue widget restores the speed when it closes
w = unreal.load_asset("/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk")
ed = BGE.get_graph_editor(BEL.find_event_graph(w))
for n in ed.list_nodes_of_class(unreal.K2Node_VariableSet):
    p = BEL.find_input_pin(n, "MaxWalkSpeed")
    if PIN.is_valid(p):
        out.append("dialogue set node %s was %s -> %s" % (n.get_name(), PIN.get_pin_value(p), PIN.set_pin_value(p, str(SPEED))))
BEL.compile_blueprint(w); unreal.EditorAssetLibrary.save_loaded_asset(w, False)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "walk_speed.log"), "w").write("\n".join(out))
