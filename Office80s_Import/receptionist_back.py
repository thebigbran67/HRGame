"""The back button says "Fuck off" when talking to the receptionist, "Cower" for every other monster."""
import os, unreal
BEL = unreal.BlueprintEditorLibrary; PIN = unreal.BlueprintGraphPinLibrary; BGE = unreal.BlueprintGraphEditor
here = os.path.dirname(os.path.abspath(__file__))
WP = "/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk"
KSL = "/Script/Engine.KismetStringLibrary:"; KTL = "/Script/Engine.KismetTextLibrary:"; KML = "/Script/Engine.KismetMathLibrary:"
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))
try:
    w = unreal.load_asset(WP)
    tb = unreal.load_object(None, WP + ".W_MonsterTalk:WidgetTree.TextBlock_671")
    tb.set_editor_property("is_variable", True)
    BEL.compile_blueprint(w)
    ed = BGE.get_graph_editor(BEL.find_event_graph(w))
    tick = [n for n in ed.list_nodes_of_class(unreal.K2Node_Event) if "Tick" in str(BEL.get_node_title(n))][0]
    then = BEL.find_output_pin(tick, "then")
    nxt = list(PIN.list_connected_pins(then))
    if any("BackLabel" in str(BEL.get_node_title(PIN.get_owning_node(p))) for p in nxt):
        raise RuntimeError("already done")
    PIN.break_pin_links(then)
    def at(n, x, y):
        if n is None: raise RuntimeError("node failed %d,%d" % (x, y))
        BEL.set_node_pos(n, unreal.IntPoint(int(x), int(y))); return n
    def fn(path, x, y): return at(ed.add_call_function_node(path), x, y)
    def get(v, x, y): return at(ed.add_get_member_variable_node(v, ""), x, y)
    def link(a, ap, b, bp_):
        if not PIN.try_create_connection(BEL.find_output_pin(a, ap), BEL.find_input_pin(b, bp_)):
            log("ERR link %s.%s -> %s.%s" % (a.get_name(), ap, b.get_name(), bp_))
    def val(n, p, v):
        if not PIN.set_pin_value(BEL.find_input_pin(n, p), v): log("ERR val %s.%s" % (n.get_name(), p))
    pos = BEL.get_node_pos(tick); X, Y = pos.x, pos.y - 500
    nm = get("Name", X + 100, Y + 200)
    gt = fn("/Script/UMG.TextBlock:GetText", X + 250, Y + 200); link(nm, "Name", gt, "self")
    ts = fn(KTL + "Conv_TextToString", X + 400, Y + 200); link(gt, "ReturnValue", ts, "InText")
    ct = fn(KSL + "Contains", X + 550, Y + 200); link(ts, "ReturnValue", ct, "SearchIn"); val(ct, "Substring", "Receptionist"); val(ct, "bUseCase", "false")
    sel = fn(KML + "SelectString", X + 700, Y + 200); val(sel, "A", "Fuck off"); val(sel, "B", "Cower"); link(ct, "ReturnValue", sel, "bPickA")
    st2 = fn(KTL + "Conv_StringToText", X + 850, Y + 200); link(sel, "ReturnValue", st2, "InString")
    bk = get("TextBlock_671", X + 700, Y + 320)
    stx = fn("/Script/UMG.TextBlock:SetText", X + 300, Y); link(bk, "TextBlock_671", stx, "self"); link(st2, "ReturnValue", stx, "InText")
    BEL.set_node_pos(stx, unreal.IntPoint(int(X + 300), int(Y)))
    PIN.try_create_connection(then, BEL.find_input_pin(stx, "execute"))
    for p in nxt:
        if not PIN.try_create_connection(BEL.find_output_pin(stx, "then"), p):
            log("ERR relink to typewriter")
    c = ed.add_comment_node("BackLabel: 'Fuck off' for the receptionist, 'Cower' for everyone else", unreal.Vector2D(X + 80, Y - 80), unreal.Vector2D(950, 480))
    BEL.compile_blueprint(w)
    for n in ed.list_nodes_with_errors():
        log("COMPILE ERROR %s" % BEL.get_node_title(n))
    unreal.EditorAssetLibrary.save_loaded_asset(w)
    log("receptionist back label done (relinked %d)" % len(nxt))
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "receptionist_back.log"), "w").write("\n".join(LOG))
