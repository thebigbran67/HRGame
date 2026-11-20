"""Office Level Blueprint: turns the task cards' "Pick From Level" choices into what BP_TaskHUD already reads.
On BeginPlay (after the existing chain):  for every card in DA_TaskManager
    ItemsToPickUp  -> each picked item gets tag Picked_Items_<n>, card Target  = that tag
    BringItemsTo   -> picked spot gets tag Picked_TurnIn_<n>,     card DeliverTo = that tag
    GoToPlace      -> picked place gets tag Picked_Place_<n>,     card Target  = that tag
    TalkTo         -> card Target       = the picked monster's MonsterName
    AngryMonster   -> card MeterMonster = the picked monster's MonsterName
On EndPlay the cards' typed fields are put back, so stopping Play leaves your cards as you wrote them.
FindPickedActor finds the Play copy of a picked actor by name. Adds nodes only; existing nodes are not changed."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
LOG = []
def log(m): LOG.append(str(m)); unreal.log("[LevelPickers] " + str(m))

TASK_C = "/Game/_TASKS/BPD_Task.BPD_Task_C"
LIST_C = "/Game/_TASKS/BPD_TaskList.BPD_TaskList_C"
MON_C = "/Game/Blueprints/Dialogue/Blueprints/BP_Monster.BP_Monster_C"
KSYS = "/Script/Engine.KismetSystemLibrary:"; KSTR = "/Script/Engine.KismetStringLibrary:"
KMATH = "/Script/Engine.KismetMathLibrary:"; KTXT = "/Script/Engine.KismetTextLibrary:"
OUT_D = unreal.EdGraphPinDirection.EGPD_OUTPUT

class G:
    """small helper around one graph"""
    def __init__(self, ed, ox, oy):
        self.ed, self.ox, self.oy = ed, ox, oy
    def at(self, n, x, y):
        BEL.set_node_pos(n, unreal.IntPoint(int(self.ox + x), int(self.oy + y))); return n
    def fn(self, path, x, y):
        n = self.ed.add_call_function_node(path)
        if n is None: raise RuntimeError("could not add " + path)
        return self.at(n, x, y)
    def get(self, var, cls, x, y): return self.at(self.ed.add_get_member_variable_node(var, cls), x, y)
    def set(self, var, cls, x, y): return self.at(self.ed.add_set_member_variable_node(var, cls), x, y)
    def branch(self, x, y): return self.at(self.ed.add_branch_node(), x, y)
    def named(self, name, x, y, ctx=()):
        n = self.ed.create_node_from_name(name, unreal.Vector2D(self.ox + x, self.oy + y), list(ctx))
        if n is None: raise RuntimeError("could not add " + name)
        return n
    def foreach(self, arr_node, arr_pin, x, y):
        p = outp(arr_node, arr_pin)
        n = self.named("Utilities|Array|ForEachLoop", x, y, [p]); link(arr_node, arr_pin, n, "Array"); return n

def outp(n, name):
    p = BEL.find_output_pin(n, name)
    if p is None or not PIN.is_valid(p): raise RuntimeError("no output pin %s on %s" % (name, BEL.get_node_title(n)))
    return p
def inp(n, name):
    p = BEL.find_input_pin(n, name)
    if p is None or not PIN.is_valid(p): raise RuntimeError("no input pin %s on %s" % (name, BEL.get_node_title(n)))
    return p
BAD = []
def link(a, ap, b, bp_):
    if not PIN.try_create_connection(outp(a, ap), inp(b, bp_)):
        BAD.append("%s.%s -> %s.%s" % (BEL.get_node_title(a), ap, BEL.get_node_title(b), bp_))
def ex(a, b, ap="then", bp_="execute"): link(a, ap, b, bp_)
def val(n, p, v):
    if not PIN.set_pin_value(inp(n, p), v): BAD.append("value %s=%s on %s" % (p, v, BEL.get_node_title(n)))
def first_out_starting(n, prefix):
    for p in BEL.list_all_pins(n, OUT_D):
        if str(PIN.get_pin_name(p)).replace(" ", "").startswith(prefix): return str(PIN.get_pin_name(p))
    raise RuntimeError("no %s pin on %s" % (prefix, BEL.get_node_title(n)))

try:
    lsb = unreal.load_object(None, "/Game/Maps/Office.Office:PersistentLevel.Office")
    task_bp = unreal.load_asset("/Game/_TASKS/BPD_Task")
    soft_t = BEL.get_member_variable_type(task_bp, "TalkTo")
    actor_t = BEL.get_object_reference_type(unreal.Actor.static_class())
    list_cls = unreal.load_class(None, LIST_C)
    have_fn = bool(BEL.find_graph(lsb, "FindPickedActor"))
    ed0 = BGE.get_graph_editor(BEL.find_event_graph(lsb))
    def cleanup():
        junk = [n for n in ed0.list_all_nodes() if BEL.get_node_pos(n).y >= 500]
        ed0.remove_nodes(junk); log("removed %d leftover nodes" % len(junk))
    cleanup()
    if not have_fn:
        BEL.add_member_variable(lsb, "TaskManager", BEL.get_object_reference_type(list_cls))
        str_arr = BEL.get_array_type(BEL.get_basic_type_by_name("string"))
        for v in ("OrigTarget", "OrigDeliverTo", "OrigMeterMonster"):
            BEL.add_member_variable(lsb, v, str_arr)
        BEL.set_blueprint_variable_category(lsb, "TaskManager", "Task Pickers")
        for v in ("OrigTarget", "OrigDeliverTo", "OrigMeterMonster"):
            BEL.set_blueprint_variable_category(lsb, v, "Task Pickers")

        # ---------------------------------------------------------------- FindPickedActor(Pick) -> Found
        fed = BGE.create_and_edit_function_graph(lsb, "FindPickedActor")
        fed.add_graph_input_parameter("Pick", soft_t)
        ret0 = fed.add_graph_output_parameter("Found", actor_t)
        entry_then = fed.find_graph_entry_pin()
        entry = PIN.get_owning_node(entry_then)
        F = G(fed, 0, 0)
        BEL.set_node_pos(entry, unreal.IntPoint(0, 0))
        iv = F.fn(KSYS + "IsValidSoftObjectReference", 200, 150); link(entry, "Pick", iv, "SoftObjectReference")
        b1 = F.branch(450, 0); PIN.try_create_connection(entry_then, inp(b1, "execute")); link(iv, "ReturnValue", b1, "Condition")
        F.at(ret0, 700, 250); ex(b1, ret0, "else")
        ga = F.fn("/Script/Engine.GameplayStatics:GetAllActorsOfClass", 700, 0); ex(b1, ga); val(ga, "ActorClass", "/Script/Engine.Actor")
        fe = F.foreach(ga, "OutActors", 1050, 0); ex(ga, fe, "then", "Exec")
        ts = F.fn(KSYS + "Conv_SoftObjectReferenceToString", 1050, 350); link(entry, "Pick", ts, "SoftObjectReference")
        on = F.fn(KSYS + "GetObjectName", 1350, 450); link(fe, "Array Element", on, "Object")
        cat = F.fn(KSTR + "Concat_StrStr", 1600, 400); val(cat, "A", "."); link(on, "ReturnValue", cat, "B")
        ew = F.fn(KSTR + "EndsWith", 1850, 300); link(ts, "ReturnValue", ew, "SourceString"); link(cat, "ReturnValue", ew, "InSuffix")
        b2 = F.branch(2100, 0); ex(fe, b2, "LoopBody"); link(ew, "ReturnValue", b2, "Condition")
        r1 = F.at(fed.add_return_node(), 2400, 0); ex(b2, r1); link(fe, "Array Element", r1, "Found")
        r2 = F.at(fed.add_return_node(), 1400, -200); ex(fe, r2, "Completed")
        fed.add_comment_node("Finds the Play copy of an actor picked on a task card (matches by name). Returns nothing if no pick.",
                             unreal.Vector2D(-60, -280), unreal.Vector2D(2700, 900))
    BEL.compile_blueprint(lsb)
    FIND = BEL.generated_class(lsb).get_path_name() + ":FindPickedActor"
    log("function: " + FIND)

    # ---------------------------------------------------------------- BeginPlay part
    ed = BGE.get_graph_editor(BEL.find_event_graph(lsb))
    nodes = list(ed.list_all_nodes())
    stop = [n for n in nodes if "On Stop" in str(BEL.get_node_title(n)) or "OnStop" in str(BEL.get_node_title(n)).replace(" ", "")]
    if not stop: raise RuntimeError("could not find Bind Event to On Stop")
    stop = stop[0]
    sp = BEL.get_node_pos(stop)
    later = list(PIN.list_connected_pins(outp(stop, "then")))
    PIN.break_pin_links(outp(stop, "then"))
    E = G(ed, sp.x - 1400, sp.y + 900)
    tm = E.get("TaskManager", "", 0, 150)
    tasks = E.get("Tasks", LIST_C, 220, 150); link(tm, "TaskManager", tasks, "self")
    prev = None
    for i, v in enumerate(("OrigTarget", "OrigDeliverTo", "OrigMeterMonster")):
        g = E.get(v, "", 0, 400 + i * 120)
        c = E.named("Utilities|Array|Clear", 250, 380 + i * 120, [outp(g, v)]); link(g, v, c, "TargetArray")
        if prev is None: PIN.try_create_connection(outp(stop, "then"), inp(c, "execute"))
        else: ex(prev, c)
        prev = c
    loop = E.foreach(tasks, "Tasks", 600, 0); ex(prev, loop, "then", "Exec")
    for q in later:
        PIN.try_create_connection(outp(loop, "Completed"), q)
    seq = E.at(ed.create_node_from_name("Utilities|FlowControl|Sequence", unreal.Vector2D(0, 0), []), 950, 0)
    for _ in range(4): ed.add_node_pin(seq)
    ex(loop, seq, "LoopBody")
    seq_pins = [str(PIN.get_pin_name(p)) for p in BEL.list_all_pins(seq, OUT_D)]
    log("sequence pins: %s" % seq_pins)
    CARD = (loop, "Array Element"); IDX = (loop, "Array Index")

    def card_get(var, x, y):
        n = E.get(var, TASK_C, x, y); link(CARD[0], CARD[1], n, "self"); return n
    def card_set(var, x, y, src):
        n = E.set(var, TASK_C, x, y); link(CARD[0], CARD[1], n, "self"); link(src[0], src[1], n, var); return n
    def tag_str(prefix, x, y):
        i2s = E.fn(KSTR + "Conv_IntToString", x, y + 60); link(IDX[0], IDX[1], i2s, "InInt")
        c = E.fn(KSTR + "Concat_StrStr", x + 220, y); val(c, "A", prefix); link(i2s, "ReturnValue", c, "B"); return (c, "ReturnValue")
    def find(src_var, x, y):
        g = card_get(src_var, x, y + 120)
        f = E.fn(FIND, x + 250, y); link(g, src_var, f, "Pick")
        ok = E.fn(KSYS + "IsValid", x + 500, y + 140); link(f, "Found", ok, "Object")
        b = E.branch(x + 750, y); ex(f, b); link(ok, "ReturnValue", b, "Condition")
        return f, b
    def add_tag(found, b, s, x, y):
        tg = E.named("Variables|Actor|GetTags", x, y + 150, [outp(found, "Found")])
        selfp = [str(PIN.get_pin_name(p)) for p in BEL.list_all_pins(tg, unreal.EdGraphPinDirection.EGPD_INPUT)]
        if "self" in selfp and not PIN.list_connected_pins(inp(tg, "self")): link(found, "Found", tg, "self")
        nm = E.fn(KSTR + "Conv_StringToName", x, y + 260); link(s[0], s[1], nm, "InString")
        au = E.named("Utilities|Array|AddUnique", x + 300, y, [outp(tg, "Tags")]); link(tg, "Tags", au, "TargetArray")
        link(nm, "ReturnValue", au, "NewItem"); ex(b, au); return au

    # remember the typed values first (Then 0)
    Y = 0
    for k, (v, orig) in enumerate((("Target", "OrigTarget"), ("DeliverTo", "OrigDeliverTo"), ("MeterMonster", "OrigMeterMonster"))):
        g = card_get(v, 1250, Y + 150 + k * 110)
        arr = E.get(orig, "", 1250, Y + 100 + k * 110)
        a = E.named("Utilities|Array|Add", 1550 + k * 300, Y, [outp(arr, orig)]); link(arr, orig, a, "TargetArray"); link(g, v, a, "NewItem")
        if k == 0: ex(seq, a, seq_pins[0])
        else: ex(last, a)
        last = a

    # Then 1: items to pick up
    Y = 600
    ip = card_get("ItemsToPickUp", 1250, Y + 150)
    ln = E.named("Utilities|Array|Length", 1500, Y + 150, [outp(ip, "ItemsToPickUp")]); link(ip, "ItemsToPickUp", ln, "TargetArray")
    gt = E.fn(KMATH + "Greater_IntInt", 1750, Y + 150); link(ln, "ReturnValue", gt, "A"); val(gt, "B", "0")
    bi = E.branch(2000, Y); ex(seq, bi, seq_pins[1]); link(gt, "ReturnValue", bi, "Condition")
    ip2 = card_get("ItemsToPickUp", 2000, Y + 250)
    il = E.foreach(ip2, "ItemsToPickUp", 2250, Y); ex(bi, il, "then", "Exec")
    s_items = tag_str("Picked_Items_", 2250, Y + 450)
    f = E.fn(FIND, 2550, Y); link(il, "Array Element", f, "Pick"); ex(il, f, "LoopBody")
    ok = E.fn(KSYS + "IsValid", 2800, Y + 140); link(f, "Found", ok, "Object")
    b = E.branch(3050, Y); ex(f, b); link(ok, "ReturnValue", b, "Condition")
    add_tag(f, b, s_items, 3300, Y)
    st = card_set("Target", 2650, Y + 600, s_items)
    ex(il, st, "Completed")

    # Then 2: bring items to
    Y = 1500
    f, b = find("BringItemsTo", 1250, Y)
    ex(seq, f, seq_pins[2], "execute")
    s_turn = tag_str("Picked_TurnIn_", 1750, Y + 350)
    au = add_tag(f, b, s_turn, 2300, Y)
    ex(au, card_set("DeliverTo", 2800, Y, s_turn))

    # Then 3: go to place
    Y = 2300
    f, b = find("GoToPlace", 1250, Y)
    ex(seq, f, seq_pins[3], "execute")
    s_place = tag_str("Picked_Place_", 1750, Y + 350)
    au = add_tag(f, b, s_place, 2300, Y)
    ex(au, card_set("Target", 2800, Y, s_place))

    # Then 4 / 5: talk to / angry monster  -> MonsterName
    for k, (pick, field) in enumerate((("TalkTo", "Target"), ("AngryMonster", "MeterMonster"))):
        Y = 3100 + k * 800
        f, b = find(pick, 1250, Y)
        ex(seq, f, seq_pins[4 + k], "execute")
        cst = E.named("Utilities|Casting|CastToBP_Monster", 2300, Y, [outp(f, "Found")]); link(f, "Found", cst, "Object"); ex(b, cst)
        asp = first_out_starting(cst, "As")
        mn = E.get("MonsterName", MON_C, 2600, Y + 200); link(cst, asp, mn, "self")
        t2s = E.fn(KTXT + "Conv_TextToString", 2850, Y + 200); link(mn, "MonsterName", t2s, "InText")
        ex(cst, card_set(field, 3100, Y, (t2s, "ReturnValue")))

    ed.add_comment_node("TASK PICKERS - turns each task card's 'Pick From Level' choices into the tags/names BP_TaskHUD reads "
                        "(items/turn-in/place get a Picked_... tag, talk/angry monster use its MonsterName). Typed values are saved first.",
                        unreal.Vector2D(E.ox - 80, E.oy - 160), unreal.Vector2D(4000, 4700))

    # ---------------------------------------------------------------- EndPlay: put the typed values back
    ends = [n for n in ed.list_all_nodes() if isinstance(n, unreal.K2Node_Event) and "EndPlay" in str(BEL.get_node_title(n)).replace(" ", "")]
    end_later = []
    if ends:
        endp = ends[0]; end_later = list(PIN.list_connected_pins(outp(endp, "then"))); PIN.break_pin_links(outp(endp, "then"))
        log("using existing EndPlay (%d links kept after ours)" % len(end_later))
    else:
        endp = BEL.add_event_override(lsb, "ReceiveEndPlay", unreal.IntPoint(int(E.ox), int(E.oy + 4900)))
    R = G(ed, E.ox, E.oy + 4900)
    tm2 = R.get("TaskManager", "", 0, 200)
    tk2 = R.get("Tasks", LIST_C, 220, 200); link(tm2, "TaskManager", tk2, "self")
    rl = R.foreach(tk2, "Tasks", 500, 0); ex(endp, rl, "then", "Exec")
    prev = None
    for k, (v, orig) in enumerate((("Target", "OrigTarget"), ("DeliverTo", "OrigDeliverTo"), ("MeterMonster", "OrigMeterMonster"))):
        arr = R.get(orig, "", 800 + k * 450, 250)
        gi = R.named("Utilities|Array|Get", 1000 + k * 450, 250, [outp(arr, orig)]); link(arr, orig, gi, "TargetArray")
        link(rl, "Array Index", gi, "Index")
        s = R.set(v, TASK_C, 1000 + k * 450, 0); link(rl, "Array Element", s, "self")
        outname = [str(PIN.get_pin_name(p)) for p in BEL.list_all_pins(gi, OUT_D)][0]
        link(gi, outname, s, v)
        if prev is None: ex(rl, s, "LoopBody")
        else: ex(prev, s)
        prev = s
    for q in end_later:
        PIN.try_create_connection(outp(rl, "Completed"), q)
    ed.add_comment_node("TASK PICKERS (end) - when Play stops, put each card's typed Target / DeliverTo / MeterMonster back",
                        unreal.Vector2D(R.ox - 80, R.oy - 120), unreal.Vector2D(2600, 600))

    BEL.compile_blueprint(lsb)
    cdo = unreal.get_default_object(BEL.generated_class(lsb))
    cdo.set_editor_property("TaskManager", unreal.load_asset("/Game/_TASKS/DA_TaskManager"))
    log("TaskManager default: %s" % cdo.get_editor_property("TaskManager"))
    BEL.compile_blueprint(lsb)
    errs = list(ed.list_nodes_with_errors()) + list(fed.list_nodes_with_errors())
    log("compile errors: %d %s" % (len(errs), [str(BEL.get_node_title(n)) for n in errs]))
    log("bad links: %s" % BAD)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if "/Game/Maps/Office" in world.get_path_name() and not errs and not BAD:
        log("saved map: %s" % unreal.EditorLoadingAndSavingUtils.save_map(world, "/Game/Maps/Office"))
    else:
        log("NOT saved (errors or bad links) - check before saving")
except Exception:
    log("EXCEPTION " + traceback.format_exc())
    try:
        cleanup(); log("cleaned up after failure, map NOT saved")
    except Exception as e2:
        log("cleanup failed: %s" % e2)
finally:
    open(os.path.join(here, "level_pickers3.log"), "w").write("\n".join(LOG))
