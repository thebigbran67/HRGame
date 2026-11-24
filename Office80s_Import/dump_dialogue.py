"""Read-only: dumps the dialogue widget + monster blueprint graphs (nodes and links) to text."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
L = []
def dump(path):
    bp = unreal.load_asset(path)
    L.append("##### %s" % path)
    if not bp: L.append("missing"); return
    L.append("vars: %s" % [str(v) for v in BEL.list_member_variable_names(bp) if "/" not in str(v)])
    names = ["EventGraph"]
    try:
        for g in BEL.list_graphs(bp) if hasattr(BEL, "list_graphs") else []:
            names.append(g.get_name())
    except Exception: pass
    for fn in getattr(BGE, "list_function_graph_names", lambda b: [])(bp) if hasattr(BGE, "list_function_graph_names") else []:
        names.append(str(fn))
    seen = set()
    for gn in names:
        if gn in seen: continue
        seen.add(gn)
        try:
            ed = BGE.get_graph_editor(BEL.find_event_graph(bp)) if gn == "EventGraph" else BGE.get_graph_editor_by_name(bp, gn)
        except Exception as e:
            L.append("  graph %s: %s" % (gn, e)); continue
        if not ed: continue
        L.append("== graph %s" % gn)
        for n in ed.list_all_nodes():
            t = str(BEL.get_node_title(n)).replace("\n", " | ")
            outs = []
            for p in BEL.list_all_pins(n, unreal.EdGraphPinDirection.EGPD_OUTPUT):
                for q in PIN.list_connected_pins(p):
                    outs.append("%s->%s[%s].%s" % (PIN.get_pin_name(p), BEL.get_node_title(PIN.get_owning_node(q)).replace("\n", " "), PIN.get_owning_node(q).get_name(), PIN.get_pin_name(q)))
            vals = []
            for p in BEL.list_all_pins(n, unreal.EdGraphPinDirection.EGPD_INPUT):
                try:
                    v = PIN.get_pin_value(p) if hasattr(PIN, "get_pin_value") else ""
                    if v and not PIN.list_connected_pins(p): vals.append("%s=%s" % (PIN.get_pin_name(p), v))
                except Exception: pass
            L.append("  [%s] %s %s  OUT: %s" % (n.get_name(), t, vals, outs))
try:
    L.append("BEL graph fns: %s" % [a for a in dir(BEL) if "graph" in a.lower()])
    L.append("BGE graph fns: %s" % [a for a in dir(BGE) if "graph" in a.lower() or "function" in a.lower()])
    for p in ("/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk", "/Game/Blueprints/Dialogue/Blueprints/BP_Monster"):
        dump(p)
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "dump_dialogue.log"), "w").write("\n".join(L))
