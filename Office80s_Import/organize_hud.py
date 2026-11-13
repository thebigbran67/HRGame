"""Tidies BP_TaskHUD's event graph: every system gets its own area, nodes flow left to right, and each area is
wrapped in a color-coded, labeled comment box. Only moves nodes / adds comments; logic is untouched."""
import os, re, unreal
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))

SECTIONS = [  # key, title, color, what it does
    ("setup",  "SETUP & KEYS", (0.55, 0.55, 0.6), "BeginPlay (walking sound), TAB list toggle, E turn-in, Shift sprint, Space skips the intro"),
    ("intro",  "INTRO GATE + DIALOGUE LINE", (0.2, 0.5, 1.0), "While the intro plays only the driver's line is drawn; otherwise everything below runs"),
    ("then_0", "TASK RUNNER", (1.0, 0.55, 0.1), "Reads DA_TaskManager: starts each task card, checks Talk / Collect / GoTo, finishes it, moves to the next"),
    ("then_1", "TASK MEMO UI", (0.95, 0.85, 0.2), "The slime memo in the top-left, stamps, item counter, TAB note and the turn-in prompt"),
    ("then_2", "FRUSTRATION METER + KILL", (0.9, 0.1, 0.1), "Fills the card's meter monster bar over time; full bar = jumpscare and restart"),
    ("then_3", "DEATH SCREEN", (0.55, 0.0, 0.05), "Red vignette, claw slash and YOU DIED"),
    ("then_4", "FOOTSTEPS", (0.4, 0.75, 0.4), "Plays / pauses the walking loop"),
    ("then_5", "CHAIR BONK", (0.6, 0.4, 0.9), "Goofy bonk when a chair tagged BonkChair is shoved"),
    ("then_6", "PRESS E TO INTERACT", (0.2, 0.85, 0.85), "Prompt while the crosshair is on a monster"),
    ("then_7", "GAME OVER SCREEN", (0.3, 0.3, 0.3), "TempOverScreen fades in after the last task"),
    ("then_8", "HEAD BOB", (0.85, 0.5, 0.65), "Camera dips up and down while walking"),
    ("then_9", "SPRINT + STAMINA", (0.1, 0.8, 0.3), "Shift to sprint, stamina drain / regen, slime stamina bar"),
    ("then_10", "BATHROOM SLIPPERY FLOOR", (0.3, 0.6, 0.95), "Low friction in the bathroom + caution sign"),
    ("then_11", "MIRROR LINE", (1.0, 0.4, 0.8), "\"Dayummmm...\" when you walk up to the bathroom mirror"),
]
EXEC_IN = {"execute", "Exec"}
EXEC_OUT_RE = re.compile(r"^(then(_\d+)?|else|LoopBody|Completed|Pressed|Released|CastFailed|OutputDelegate)$")

def pins(n, d):
    return list(BEL.list_all_pins(n, d))
def pname(p):
    return str(PIN.get_pin_name(p))
def conns(p):
    return [x for x in PIN.list_connected_pins(p)]

def main():
    bp = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
    ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
    nodes = list(ed.list_all_nodes())
    old = [n for n in nodes if isinstance(n, unreal.EdGraphNode_Comment)]
    if old:
        ed.remove_nodes(old)
    nodes = [n for n in nodes if not isinstance(n, unreal.EdGraphNode_Comment)]
    IN, OUT = unreal.EdGraphPinDirection.EGPD_INPUT, unreal.EdGraphPinDirection.EGPD_OUTPUT
    key = {n.get_name(): n for n in nodes}
    # edges
    exec_succ, data_pred, all_succ = {}, {}, {}
    for n in nodes:
        nm = n.get_name()
        for p in pins(n, OUT):
            for q in conns(p):
                m = PIN.get_owning_node(q).get_name()
                all_succ.setdefault(nm, set()).add(m)
                if EXEC_OUT_RE.match(pname(p)) and pname(q) in EXEC_IN:
                    exec_succ.setdefault(nm, []).append(m)
                else:
                    data_pred.setdefault(m, set()).add(nm)
    # roots
    seq = None; dh = None; events = []
    for n in nodes:
        t = str(BEL.get_node_title(n))
        if isinstance(n, unreal.K2Node_Event) or "Keyboard" in n.get_class().get_name() or n.get_class().get_name() == "K2Node_InputKey":
            if "DrawHUD" in t: dh = n
            else: events.append(n)
    for n in nodes:
        if "ExecutionSequence" in n.get_class().get_name() and dh and n.get_name() in [x for x in exec_succ.get(dh.get_name(), [])] + []:
            seq = n
    if seq is None:   # the sequence is reached through the intro gate
        for n in nodes:
            if "ExecutionSequence" in n.get_class().get_name():
                seq = n
    log("roots: drawhud=%s seq=%s events=%d" % (dh and dh.get_name(), seq and seq.get_name(), len(events)))
    owner = {}
    def flood(start_names, sec):
        stack = list(start_names)
        while stack:
            s = stack.pop()
            if s in owner: continue
            owner[s] = sec
            stack.extend(exec_succ.get(s, []))
    # sequence branches first (so the intro gate doesn't swallow them)
    owner[seq.get_name()] = "intro"
    for p in pins(seq, OUT):
        pn = pname(p)
        flood([PIN.get_owning_node(q).get_name() for q in conns(p)], pn)
    for e in events:
        flood([e.get_name()], "setup")
    flood([dh.get_name()], "intro")
    # pure nodes join the section of the node they feed (walk back through data inputs)
    changed = True
    while changed:
        changed = False
        for n in nodes:
            nm = n.get_name()
            if nm in owner: continue
            users = [owner[s] for s in all_succ.get(nm, []) if s in owner]
            if users:
                owner[nm] = users[0]; changed = True
    for n in nodes:
        owner.setdefault(n.get_name(), "setup")
    # layout each section: longest-path layering, barycenter ordering
    y_cursor = 0
    counts = {}
    for skey, title, color, desc in SECTIONS:
        sec = [n for n in nodes if owner[n.get_name()] == skey]
        if not sec:
            continue
        counts[skey] = len(sec)
        names = {n.get_name() for n in sec}
        preds = {nm: [p for p in (data_pred.get(nm, set()) | {a for a, b in exec_succ.items() for x in b if x == nm and a in names} ) if p in names] for nm in names}
        depth = {nm: 0 for nm in names}
        for _ in range(60):
            moved = False
            for nm in names:
                for p in preds[nm]:
                    if depth[nm] < depth[p] + 1 and depth[p] + 1 < 400:
                        depth[nm] = depth[p] + 1; moved = True
            if not moved: break
        cols = {}
        for nm in names:
            cols.setdefault(depth[nm], []).append(nm)
        ypos = {}
        def height(nm):
            n = key[nm]; return 70 + 26 * max(len(pins(n, IN)), len(pins(n, OUT)))
        max_bottom = y_cursor
        for d in sorted(cols):
            col = cols[d]
            col.sort(key=lambda nm: (sum(ypos.get(p, 0) for p in preds[nm]) / max(1, len([p for p in preds[nm] if p in ypos]))) if any(p in ypos for p in preds[nm]) else 0)
            y = y_cursor + 140
            for nm in col:
                ypos[nm] = y
                BEL.set_node_pos(key[nm], unreal.IntPoint(int(d * 380), int(y)))
                y += height(nm) + 40
            max_bottom = max(max_bottom, y)
        width = (max(cols) + 1) * 380 + 120
        c = ed.add_comment_node("%s  -  %s" % (title, desc), unreal.Vector2D(-80, y_cursor), unreal.Vector2D(width, max_bottom - y_cursor + 60))
        try:
            BEL.set_comment_color(c, unreal.LinearColor(color[0], color[1], color[2], 1.0))
        except Exception as e:
            log("color: %s" % e)
        for prop, v in (("font_size", 48), ("b_color_comment_bubble", True)):
            try: c.set_editor_property(prop, v)
            except Exception: pass
        y_cursor = max_bottom + 400
    log("sections: %s" % counts)
    BEL.compile_blueprint(bp)
    errs = list(ed.list_nodes_with_errors())
    log("compile errors: %d" % len(errs))
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    log("organized")

try:
    main()
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "organize_hud.log"), "w").write("\n".join(LOG))
