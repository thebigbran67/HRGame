import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
L = []
try:
    hud = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
    L.append("graphs: %s" % [str(g) for g in BEL.list_graph_names(hud)])
    for gn in [str(g) for g in BEL.list_graph_names(hud)]:
        ed = BGE.get_graph_editor_by_name(hud, gn)
        if not ed: continue
        for n in ed.list_all_nodes():
            if "DrawText" in str(BEL.get_node_title(n)):
                tp = BEL.find_input_pin(n, "Text")
                if tp and "SQUASH" in str(PIN.get_pin_value(tp)).upper():
                    L.append("FOUND in %s: %s pos %s" % (gn, n.get_name(), BEL.get_node_pos(n)))
                    for d in (unreal.EdGraphPinDirection.EGPD_INPUT, unreal.EdGraphPinDirection.EGPD_OUTPUT):
                        for p in BEL.list_all_pins(n, d):
                            cons = [("%s[%s].%s" % (str(BEL.get_node_title(PIN.get_owning_node(q))).replace("\n", " "), PIN.get_owning_node(q).get_name(), PIN.get_pin_name(q))) for q in PIN.list_connected_pins(p)]
                            L.append("   %s %s = %s  links %s" % ("IN " if d == unreal.EdGraphPinDirection.EGPD_INPUT else "OUT", PIN.get_pin_name(p), PIN.get_pin_value(p), cons))
        L.append("graph %s nodes %d" % (gn, len(list(ed.list_all_nodes()))))
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "inspect_squash.log"), "w").write("\n".join(L))
