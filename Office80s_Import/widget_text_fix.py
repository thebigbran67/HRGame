"""W_MonsterTalk: Gus fired line (text pin, proper text format), Back button designer text Cower -> Continue, note comment."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
L = []
def log(m): L.append(str(m))
try:
    w = unreal.load_asset("/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk")
    w.modify()
    ed = BGE.get_graph_editor(BEL.find_event_graph(w))
    hits = []
    for n in ed.list_all_nodes():
        p = BEL.find_input_pin(n, "InText")
        if p and PIN.is_valid(p):
            v = str(PIN.get_pin_value(p))
            if "computer password" in v or "FUCKKKK" in v: hits.append((n, p, v))
    log("gus nodes: %d %s" % (len(hits), [h[2][:60] for h in hits]))
    if len(hits) == 1:
        n, p, v = hits[0]
        for fmt in ('NSLOCTEXT("", "GusFiredLine", "FUCKKKK BRO WHY AM I FIRED FUCKKKK")', 'INVTEXT("FUCKKKK BRO WHY AM I FIRED FUCKKKK")'):
            ok = PIN.set_pin_value(p, fmt)
            log("set %s -> %s now %s" % (fmt[:9], ok, PIN.get_pin_value(p)))
            if ok: break
    # designer text on the Back button
    wt = w.get_editor_property("widget_tree")
    root = wt.get_editor_property("root_widget")
    found = []
    def walk(x, depth=0):
        if x is None: return
        nm = x.get_name()
        if isinstance(x, unreal.TextBlock):
            t = str(x.get_text())
            if t in ("Cower", "Fuck off"):
                x.modify(); x.set_text(unreal.Text("Continue")); found.append("%s: %s -> %s" % (nm, t, x.get_text()))
        if isinstance(x, unreal.ContentWidget):
            walk(x.get_content(), depth + 1)
        if isinstance(x, unreal.PanelWidget):
            for c in x.get_all_children(): walk(c, depth + 1)
    walk(root)
    log("designer texts changed: %s" % found)
    for c in ed.list_comment_nodes():
        try:
            t = str(c.get_editor_property("node_comment"))
            if "Cower" in t:
                c.set_editor_property("node_comment", "BackLabel: 'Continue' for everyone.")
                log("comment updated")
        except Exception as e:
            log("comment not editable: %s" % e)
    BEL.compile_blueprint(w)
    log("compile errors: %d" % len(list(ed.list_nodes_with_errors())))
    log("saved: %s" % unreal.EditorAssetLibrary.save_loaded_asset(w, False))
except Exception:
    log("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "widget_text_fix.log"), "w").write("\n".join(L))
