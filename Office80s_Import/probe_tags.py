"""Read-only: node names for Tags from an Actor pin, removal functions, and what the Level BP has now."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
L = []
try:
    lsb = unreal.load_object(None, "/Game/Maps/Office.Office:PersistentLevel.Office")
    ed = BGE.get_graph_editor(BEL.find_event_graph(lsb))
    nodes = list(ed.list_all_nodes())
    for n in nodes:
        p = BEL.get_node_pos(n)
        L.append("node %-45s (%d,%d) %s" % (str(BEL.get_node_title(n)).replace("\n", " ")[:45], p.x, p.y, n.get_name()))
    L.append("vars: %s" % [str(v) for v in BEL.list_member_variable_names(lsb)])
    L.append("BEL remove fns: %s" % [a for a in dir(BEL) if "remove" in a.lower() or "delete" in a.lower()])
    L.append("BGE remove fns: %s" % [a for a in dir(BGE) if "remove" in a.lower()])
    ref = [n for n in nodes if "IntroSequence" in str(BEL.get_node_title(n))]
    if ref:
        outs = list(BEL.list_all_pins(ref[0], unreal.EdGraphPinDirection.EGPD_OUTPUT))
        L.append("ref pins: %s" % [str(PIN.get_pin_name(p)) for p in outs])
        av = list(ed.list_available_nodes([outs[0]]))
        L.append("available count %d" % len(av))
        L.append("tags: %s" % [a for a in av if "tag" in a.lower()][:40])
        L.append("add unique: %s" % [a for a in av if "unique" in a.lower()][:10])
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "probe_tags.log"), "w").write("\n".join(L))
