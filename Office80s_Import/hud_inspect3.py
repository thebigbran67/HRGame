"""Read-only: lists BP_TaskHUD comment boxes and how many nodes sit inside each."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor
LOG = []
try:
    bp = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
    ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
    nodes = list(ed.list_all_nodes())
    LOG.append("node count %d" % len(nodes))
    coms, others = [], []
    for n in nodes:
        p_ = BEL.get_node_pos(n); x, y = p_.x, p_.y
        if isinstance(n, unreal.EdGraphNode_Comment):
            w = h = 0
            for a, b in (("node_width", "node_height"), ("NodeWidth", "NodeHeight")):
                try: w, h = n.get_editor_property(a), n.get_editor_property(b); break
                except Exception: pass
            try: t = str(n.get_editor_property("node_comment"))
            except Exception: t = str(BEL.get_node_title(n))
            coms.append((n.get_name(), x, y, w, h, t))
        else:
            others.append((x, y, n.get_name()))
    if others:
        LOG.append("non-comment nodes %d, x %d..%d y %d..%d" % (len(others), min(o[0] for o in others), max(o[0] for o in others), min(o[1] for o in others), max(o[1] for o in others)))
    for nm, x, y, w, h, t in sorted(coms, key=lambda c: (c[2], c[1])):
        inside = sum(1 for (a, b, _) in others if x <= a <= x + w and y <= b <= y + h)
        LOG.append("COMMENT %s at (%d,%d) size %dx%d inside=%d | %s" % (nm, x, y, w, h, inside, t[:60]))
    LOG.append("graphs: %s" % [g.get_name() for g in bp.get_editor_property("ubergraph_pages")] if True else "")
except Exception:
    LOG.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "hud_inspect3.log"), "w").write("\n".join(LOG))
