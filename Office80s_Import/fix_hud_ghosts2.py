import unreal, os
BEL = unreal.BlueprintEditorLibrary; PIN = unreal.BlueprintGraphPinLibrary; BGE = unreal.BlueprintGraphEditor
bp = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
kill = [n for n in ed.list_nodes_of_class(unreal.K2Node_Event) if not any(len(PIN.list_connected_pins(p)) for p in BEL.list_all_pins(n))]
ed.remove_nodes(kill)
BEL.compile_blueprint(bp)
errs = [str(BEL.get_node_title(n)) for n in ed.list_nodes_with_errors()] + [str(BEL.get_node_title(n)) for n in ed.list_nodes_with_warnings()]
unreal.EditorAssetLibrary.save_loaded_asset(bp)
BEL.refresh_open_editors_for_blueprint(bp)
unreal.log("[Office80s] ghosts removed %d, issues %s" % (len(kill), errs))
