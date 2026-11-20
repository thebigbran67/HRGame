import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor
LOG = []
try:
    bp = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
    ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
    pts = [BEL.get_node_pos(n) for n in ed.list_all_nodes()]
    LOG.append("nodes %d" % len(pts))
    for c in ed.list_comment_nodes():
        p = BEL.get_node_pos(c)
        w = h = 0
        for a, b in (("node_width", "node_height"), ("NodeWidth", "NodeHeight")):
            try: w, h = c.get_editor_property(a), c.get_editor_property(b); break
            except Exception: pass
        inside = sum(1 for q in pts if p.x <= q.x <= p.x + w and p.y <= q.y <= p.y + h) if w else -1
        LOG.append("box at (%d,%d) %dx%d inside=%d %s" % (p.x, p.y, w, h, inside, str(BEL.get_node_title(c))[:40]))
    unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([bp])
except Exception:
    LOG.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "hud_inspect4.log"), "w").write("\n".join(LOG))
