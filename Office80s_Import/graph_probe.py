import unreal, os
BEL = unreal.BlueprintEditorLibrary; PIN = unreal.BlueprintGraphPinLibrary; BGE = unreal.BlueprintGraphEditor
out = []
path = "/Game/Office80s/Temp/BP_Probe"
if unreal.EditorAssetLibrary.does_asset_exist(path):
    unreal.EditorAssetLibrary.delete_asset(path)
bp = BEL.create_blueprint_asset_with_parent(path, unreal.HUD)
g = BEL.find_event_graph(bp)
ed = BGE.get_graph_editor(g)
n = ed.add_call_function_node("/Script/Engine.GameplayStatics:GetActorOfClass")
out.append("node: %s" % n)
for p in BEL.list_all_pins(n):
    out.append("  pin %s %s %s" % (PIN.get_pin_name(p), PIN.get_pin_direction(p), PIN.get_pin_type_display_string(p)))
cp = BEL.find_input_pin(n, "ActorClass")
out.append("set class: %s" % PIN.set_pin_value(cp, "/Game/TaskSystem/BP_QuestManager.BP_QuestManager_C"))
rv = BEL.find_output_pin(n, "ReturnValue")
out.append("rv type after: %s" % PIN.get_pin_type_display_string(rv))
avail = ed.list_available_nodes([rv])
out.append("avail with rv: %d" % len(avail))
out += ["  A " + a for a in avail if any(k in a.lower() for k in ("cast", "activetasks", "overlapping"))][:60]
avail2 = ed.list_available_nodes([])
out.append("avail no ctx: %d" % len(avail2))
out += ["  B " + a for a in avail2 if any(k in a.lower() for k in ("tab", "draw text", "drawtext", "draw rect", "get text size", "enable input", "for each", "select", "receive draw", "event draw", "sequence", "branch"))][:120]
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_probe.txt")
open(p, "w", encoding="utf-8").write("\n".join(str(x) for x in out))
unreal.log("[Office80s] graph probe done")
