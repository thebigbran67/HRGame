"""Read-only: lists BP_TaskHUD graphs, comment boxes and how many nodes sit inside each."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
LOG = []
try:
    bp = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
    BGE = unreal.BlueprintGraphEditor
    LOG.append("BGE fns: %s" % [a for a in dir(BGE) if not a.startswith("_")][:200])
    graphs = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    LOG.append("event graph: %s" % graphs)
    nodes = graphs.get_editor_property("nodes") if graphs else []
    LOG.append("node count %d" % len(nodes))
    coms, others = [], []
    for n in nodes:
        x, y = n.get_editor_property("node_pos_x"), n.get_editor_property("node_pos_y")
        if n.get_class().get_name() == "EdGraphNode_Comment":
            coms.append((n, x, y, n.get_editor_property("node_width"), n.get_editor_property("node_height"), str(n.get_editor_property("node_comment"))))
        else:
            others.append((x, y))
    xs = [o[0] for o in others]; ys = [o[1] for o in others]
    if others: LOG.append("non-comment bounds x %d..%d y %d..%d" % (min(xs), max(xs), min(ys), max(ys)))
    for n, x, y, w, h, t in sorted(coms, key=lambda c: (c[2], c[1])):
        inside = sum(1 for (a, b) in others if x <= a <= x + w and y <= b <= y + h)
        LOG.append("COMMENT %s at (%d,%d) size %dx%d nodes inside=%d | %s" % (n.get_name(), x, y, w, h, inside, t[:70]))
except Exception:
    LOG.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "hud_inspect.log"), "w").write("\n".join(LOG))
