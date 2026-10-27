import unreal, os
BEL = unreal.BlueprintEditorLibrary; PIN = unreal.BlueprintGraphPinLibrary; BGE = unreal.BlueprintGraphEditor
out = []
bp = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
enable = None
for n in ed.list_all_nodes():
    t = str(BEL.get_node_title(n))
    if "Enable Input" in t:
        enable = n
evs = list(ed.list_nodes_of_class(unreal.K2Node_Event))
for n in evs:
    t = str(BEL.get_node_title(n)); pos = BEL.get_node_pos(n)
    conn = any(len(PIN.list_connected_pins(p)) for p in BEL.list_all_pins(n))
    out.append("event %s '%s' pos %s connected %s" % (n.get_name(), t, pos, conn))
kill = [n for n in evs if ("Begin Play" in str(BEL.get_node_title(n))) or ("Tick" in str(BEL.get_node_title(n))) or ("Overlap" in str(BEL.get_node_title(n)))]
ed.remove_nodes(kill)
out.append("removed %d" % len(kill))
bpl = BEL.add_event_override(bp, "ReceiveBeginPlay", unreal.IntPoint(0, -600))
BEL.set_node_pos(bpl, unreal.IntPoint(0, -600))
ok = PIN.try_create_connection(BEL.find_output_pin(bpl, "then"), BEL.find_input_pin(enable, "execute"))
out.append("new beginplay %s linked %s" % (bpl.get_name(), ok))
BEL.compile_blueprint(bp)
out += ["ERR " + str(BEL.get_node_title(n)) for n in ed.list_nodes_with_errors()]
out += ["WARN " + str(BEL.get_node_title(n)) for n in ed.list_nodes_with_warnings()]
unreal.EditorAssetLibrary.save_loaded_asset(bp)
BEL.refresh_open_editors_for_blueprint(bp)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix_hud_ghosts.log"), "w").write("\n".join(out))
