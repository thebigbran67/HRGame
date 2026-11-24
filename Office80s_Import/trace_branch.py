import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
L = []
try:
    hud = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
    ed = BGE.get_graph_editor(BEL.find_event_graph(hud))
    call = [n for n in ed.list_all_nodes() if "DrawSquishPrompt" in str(BEL.get_node_title(n)).replace(" ", "")][0]
    seen = set()
    def up(n, depth, maxd=7):
        if depth > maxd or n.get_name() in seen: return
        seen.add(n.get_name())
        vals = []
        for p in BEL.list_all_pins(n, unreal.EdGraphPinDirection.EGPD_INPUT):
            c = list(PIN.list_connected_pins(p))
            if not c:
                v = PIN.get_pin_value(p)
                if v: vals.append("%s=%s" % (PIN.get_pin_name(p), v))
        L.append("%s%s [%s] %s" % ("  " * depth, str(BEL.get_node_title(n)).replace("\n", " "), n.get_name(), vals))
        for p in BEL.list_all_pins(n, unreal.EdGraphPinDirection.EGPD_INPUT):
            for q in PIN.list_connected_pins(p):
                L.append("%s  <- %s from %s.%s" % ("  " * depth, PIN.get_pin_name(p), str(BEL.get_node_title(PIN.get_owning_node(q))).replace("\n", " "), PIN.get_pin_name(q)))
                up(PIN.get_owning_node(q), depth + 1, maxd)
    up(call, 0)
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "trace_branch.log"), "w").write("\n".join(L[:400]))
