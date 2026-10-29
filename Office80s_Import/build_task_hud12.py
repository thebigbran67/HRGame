"""Builds BP_TaskHUD: a clean task list for the Office.
 - Trash bags stay hidden (and can't be picked up) until the player gets the trash task from a monster
   (the dialogue's "Sure" option adds it to BP_QuestManager.ActiveTasks).
 - Once the task is active, "Press TAB for task list" shows in the top-right corner.
 - TAB toggles the task list in the top-left corner: "Take out the trash  n/5", then
   "Bring the trash to the dumpster", then COMPLETE once the player reaches the garbage dump with every bag.
The HUD is set as the HUD class of BP_FirstPersonGameMode. Re-runnable (rebuilds the asset)."""
import os, unreal
BEL = unreal.BlueprintEditorLibrary; PIN = unreal.BlueprintGraphPinLibrary; BGE = unreal.BlueprintGraphEditor
here = os.path.dirname(os.path.abspath(__file__))
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))

HUD_PATH = "/Game/TaskSystem/BP_TaskHUD"
QM = "/Game/TaskSystem/BP_QuestManager.BP_QuestManager_C"
BAG = "/Game/TaskSystem/Tasks/BP_TrashBag.BP_TrashBag_C"
DROP = "/Game/TaskSystem/Tasks/BP_TrashDropOff.BP_TrashDropOff_C"
FONT = "/Engine/EngineFonts/Roboto.Roboto"
KML = "/Script/Engine.KismetMathLibrary:"
KSL = "/Script/Engine.KismetStringLibrary:"

if unreal.EditorAssetLibrary.does_asset_exist("/Game/Office80s/Temp/BP_Probe"):
    unreal.EditorAssetLibrary.delete_asset("/Game/Office80s/Temp/BP_Probe")
if unreal.EditorAssetLibrary.does_asset_exist(HUD_PATH):
    bp = unreal.load_asset(HUD_PATH)
    ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
    ed.remove_nodes(list(ed.list_all_nodes()))
else:
    bp = BEL.create_blueprint_asset_with_parent(HUD_PATH, unreal.HUD)
    ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
have = [str(x) for x in BEL.list_member_variable_names(bp)] if hasattr(BEL, "list_member_variable_names") else []
for name, t in (("Phase", "int"), ("TotalBags", "int"), ("Collected", "int"), ("ShowList", "bool"), ("NearDump", "bool"), ("Talked", "bool"), ("Frust", "real"), ("FrustPerSec", "real"), ("Dead", "bool"), ("LastCollected", "int"), ("StepAcc", "real"), ("LastBonk", "real")):
    if name not in have:
        BEL.add_member_variable(bp, name, BEL.get_basic_type_by_name(t))
if "StepAudio" not in have:
    BEL.add_member_variable(bp, "StepAudio", BEL.get_object_reference_type(unreal.AudioComponent))
if "Janitor" not in have:
    BEL.add_member_variable(bp, "Janitor", BEL.get_object_reference_type(unreal.Actor))

def at(n, x, y):
    if n is None:
        raise RuntimeError("node creation failed near %d,%d" % (x, y))
    BEL.set_node_pos(n, unreal.IntPoint(int(x), int(y)))
    return n
def fn(path, x, y):
    return at(ed.add_call_function_node(path), x, y)
def named(name, x, y, ctx=()):
    return at(ed.create_node_from_name(name, unreal.Vector2D(x, y), list(ctx)), x, y)
def get(var, x, y, cls=""):
    return at(ed.add_get_member_variable_node(var, cls), x, y)
def setv(var, x, y):
    return at(ed.add_set_member_variable_node(var), x, y)
def opin(n, p):
    pin = BEL.find_output_pin(n, p)
    if not PIN.is_valid(pin):
        log("ERR no output pin %s on %s; has %s" % (p, n.get_name(), [str(PIN.get_pin_name(x)) for x in BEL.list_all_pins(n)]))
    return pin
def ipin(n, p):
    pin = BEL.find_input_pin(n, p)
    if not PIN.is_valid(pin):
        log("ERR no input pin %s on %s; has %s" % (p, n.get_name(), [str(PIN.get_pin_name(x)) for x in BEL.list_all_pins(n)]))
    return pin
def link(a, ap, b, bp_):
    o, i = opin(a, ap), ipin(b, bp_)
    if not PIN.try_create_connection(o, i):
        log("ERR link %s.%s -> %s.%s" % (a.get_name(), ap, b.get_name(), bp_))
def ex(a, b, ap="then", bp_="execute"):
    link(a, ap, b, bp_)
def val(n, p, v):
    if not PIN.set_pin_value(ipin(n, p), v):
        log("ERR value %s.%s = %s" % (n.get_name(), p, v))

def iconst_cmp(func, var_node, var_pin, k, x, y):
    c = fn(KML + func, x, y)
    link(var_node, var_pin, c, "A"); val(c, "B", str(k))
    return c

def main():
    global bp
    # ---------------------------------------------------------------- BeginPlay: listen for TAB
    bpl = at(BEL.add_event_override(bp, "ReceiveBeginPlay", unreal.IntPoint(0, -600)), 0, -600)
    en = fn("/Script/Engine.Actor:EnableInput", 300, -600)
    pc = fn("/Script/Engine.HUD:GetOwningPlayerController", 60, -480)
    ex(bpl, en); link(pc, "ReturnValue", en, "PlayerController")
    walk_snd = fn("/Script/Engine.GameplayStatics:SpawnSound2D", 550, -600); val(walk_snd, "Sound", "/Game/Office80s/Audio/roblox-walking.roblox-walking")
    val(walk_snd, "bAutoDestroy", "false"); val(walk_snd, "VolumeMultiplier", "0.7"); ex(en, walk_snd)
    sa_set = setv("StepAudio", 800, -600); link(walk_snd, "ReturnValue", sa_set, "StepAudio"); ex(walk_snd, sa_set)
    sa_g0 = get("StepAudio", 800, -450)
    pz = fn("/Script/Engine.AudioComponent:SetPaused", 1050, -600); val(pz, "bPause", "true"); link(sa_g0, "StepAudio", pz, "self"); ex(sa_set, pz)

    # ---------------------------------------------------------------- TAB toggles the list (only once the task exists)
    tab = named("Input|KeyboardEvents|Tab", 0, -300)
    ph_t = get("Phase", 60, -180)
    gt0 = iconst_cmp("Greater_IntInt", ph_t, "Phase", 0, 240, -180)
    br_t = at(ed.add_branch_node(), 420, -300)
    link(tab, "Pressed", br_t, "execute"); link(gt0, "ReturnValue", br_t, "Condition")
    sl_g = get("ShowList", 420, -150)
    nt = fn(KML + "Not_PreBool", 600, -150); link(sl_g, "ShowList", nt, "A")
    sl_s = setv("ShowList", 760, -300); ex(br_t, sl_s); link(nt, "ReturnValue", sl_s, "ShowList")

    # ---------------------------------------------------------------- DrawHUD: state + drawing every frame
    dh = at(BEL.add_event_override(bp, "ReceiveDrawHUD", unreal.IntPoint(0, 200)), 0, 200)
    seq = named("Utilities|FlowControl|Sequence", 220, 200)
    ex(dh, seq)

    # state
    bags = fn("/Script/Engine.GameplayStatics:GetAllActorsOfClass", 420, 200); val(bags, "ActorClass", BAG)
    qm = fn("/Script/Engine.GameplayStatics:GetActorOfClass", 720, 200); val(qm, "ActorClass", QM)
    dr = fn("/Script/Engine.GameplayStatics:GetActorOfClass", 1000, 200); val(dr, "ActorClass", DROP)
    link(seq, "then_0", bags, "execute"); ex(bags, qm); ex(qm, dr)
    ph0 = get("Phase", 1000, 380)
    eq0 = iconst_cmp("EqualEqual_IntInt", ph0, "Phase", 0, 1160, 380)
    br0 = at(ed.add_branch_node(), 1300, 200); ex(dr, br0); link(eq0, "ReturnValue", br0, "Condition")

    # phase 0: keep every bag hidden and untouchable, watch for the task to be handed out
    fe_h = named("Utilities|Array|ForEachLoop", 1550, 100, [opin(bags, "OutActors")])
    link(bags, "OutActors", fe_h, "Array"); link(br0, "then", fe_h, "Exec")
    hid = fn("/Script/Engine.Actor:SetActorHiddenInGame", 1850, 0); val(hid, "bNewHidden", "true")
    col = fn("/Script/Engine.Actor:SetActorEnableCollision", 2100, 0); val(col, "bNewActorEnableCollision", "false")
    link(fe_h, "LoopBody", hid, "execute"); link(fe_h, "Array Element", hid, "self")
    ex(hid, col); link(fe_h, "Array Element", col, "self")
    tasks = get("ActiveTasks", 1600, 330, QM); link(qm, "ReturnValue", tasks, "self")
    tlen = named("Utilities|Array|Length", 1820, 330, [opin(tasks, "ActiveTasks")]); link(tasks, "ActiveTasks", tlen, "TargetArray")
    has = fn(KML + "Greater_IntInt", 2000, 330); link(tlen, "ReturnValue", has, "A"); val(has, "B", "0")
    br_g = at(ed.add_branch_node(), 2150, 200); link(fe_h, "Completed", br_g, "execute"); link(has, "ReturnValue", br_g, "Condition")
    ph_s1 = setv("Phase", 2350, 200); val(ph_s1, "Phase", "1"); ex(br_g, ph_s1)
    blen = named("Utilities|Array|Length", 2350, 360, [opin(bags, "OutActors")]); link(bags, "OutActors", blen, "TargetArray")
    tb_s = setv("TotalBags", 2550, 200); ex(ph_s1, tb_s); link(blen, "ReturnValue", tb_s, "TotalBags")
    fe_s = named("Utilities|Array|ForEachLoop", 2800, 200, [opin(bags, "OutActors")])
    link(bags, "OutActors", fe_s, "Array"); ex(tb_s, fe_s, "then", "Exec")
    shw = fn("/Script/Engine.Actor:SetActorHiddenInGame", 3100, 120); val(shw, "bNewHidden", "false")
    col2 = fn("/Script/Engine.Actor:SetActorEnableCollision", 3350, 120); val(col2, "bNewActorEnableCollision", "true")
    link(fe_s, "LoopBody", shw, "execute"); link(fe_s, "Array Element", shw, "self")
    ex(shw, col2); link(fe_s, "Array Element", col2, "self")

    # phase 1+: count collected bags, finish at the dump with every bag
    tb_g = get("TotalBags", 1500, 560)
    blen2 = named("Utilities|Array|Length", 1500, 660, [opin(bags, "OutActors")]); link(bags, "OutActors", blen2, "TargetArray")
    sub_ = fn(KML + "Subtract_IntInt", 1700, 600); link(tb_g, "TotalBags", sub_, "A"); link(blen2, "ReturnValue", sub_, "B")
    co_s = setv("Collected", 1900, 480); link(br0, "else", co_s, "execute"); link(sub_, "ReturnValue", co_s, "Collected")
    co_g = get("Collected", 1900, 700); tb_g2 = get("TotalBags", 1900, 780)
    all_ = fn(KML + "GreaterEqual_IntInt", 2100, 720); link(co_g, "Collected", all_, "A"); link(tb_g2, "TotalBags", all_, "B")
    ph1 = get("Phase", 2100, 620); eq1 = iconst_cmp("EqualEqual_IntInt", ph1, "Phase", 1, 2260, 620)
    pawn = fn("/Script/Engine.HUD:GetOwningPawn", 2100, 860)
    ov = fn("/Script/Engine.Actor:IsOverlappingActor", 2300, 840); link(pawn, "ReturnValue", ov, "self"); link(dr, "ReturnValue", ov, "Other")
    and1 = fn(KML + "BooleanAND", 2450, 680); link(eq1, "ReturnValue", and1, "A"); link(all_, "ReturnValue", and1, "B")
    and2 = fn(KML + "BooleanAND", 2600, 760); link(and1, "ReturnValue", and2, "A"); link(ov, "ReturnValue", and2, "B")
    nd_s = setv("NearDump", 2750, 480); link(and2, "ReturnValue", nd_s, "NearDump")
    # bag pickup sound whenever the collected count goes up
    co_p = get("Collected", 1900, 320); lc_g = get("LastCollected", 1900, 400)
    more = fn(KML + "Greater_IntInt", 2060, 340); link(co_p, "Collected", more, "A"); link(lc_g, "LastCollected", more, "B")
    br_p = at(ed.add_branch_node(), 2150, 480); ex(co_s, br_p); link(more, "ReturnValue", br_p, "Condition")
    snd_p = fn("/Script/Engine.GameplayStatics:PlaySound2D", 2300, 300); val(snd_p, "Sound", "/Game/Office80s/Audio/SFX_80s_TrashPickup.SFX_80s_TrashPickup")
    ex(br_p, snd_p)
    co_p2 = get("Collected", 2450, 380); lc_s = setv("LastCollected", 2500, 300); link(co_p2, "Collected", lc_s, "LastCollected"); ex(snd_p, lc_s)
    ex(lc_s, nd_s); link(br_p, "else", nd_s, "execute")

    # E at the dump (with every bag) takes the trash out; doesn't swallow E so doors still work
    ek = named("Input|KeyboardEvents|E", 0, -1000)
    try:
        ek.set_editor_property("consume_input", False)
    except Exception as e1:
        try:
            ek.set_editor_property("b_consume_input", False)
        except Exception as e2:
            log("consume flag not set: %s / %s" % (e1, e2))
    nd_g = get("NearDump", 60, -880)
    br_e = at(ed.add_branch_node(), 300, -1000); link(ek, "Pressed", br_e, "execute"); link(nd_g, "NearDump", br_e, "Condition")
    ph_s2 = setv("Phase", 520, -1000); val(ph_s2, "Phase", "2"); ex(br_e, ph_s2)
    nd_off = setv("NearDump", 740, -1000); val(nd_off, "NearDump", "false"); ex(ph_s2, nd_off)
    # finishing the task calms the janitor down by half the bar
    fq = get("Frust", 740, -860); fsub = fn(KML + "Subtract_DoubleDouble", 900, -860); link(fq, "Frust", fsub, "A"); val(fsub, "B", "50.0")
    fmx = fn(KML + "FMax", 1060, -860); link(fsub, "ReturnValue", fmx, "A"); val(fmx, "B", "0.0")
    fcalm = setv("Frust", 960, -1000); link(fmx, "ReturnValue", fcalm, "Frust"); ex(nd_off, fcalm)
    snd_d = fn("/Script/Engine.GameplayStatics:PlaySound2D", 1200, -1000); val(snd_d, "Sound", "/Game/Office80s/Audio/SFX_80s_DumpsterDrop.SFX_80s_DumpsterDrop"); ex(fcalm, snd_d)

    # drawing
    Y = 1200
    ph2 = get("Phase", 300, Y + 120); gtd = iconst_cmp("Greater_IntInt", ph2, "Phase", 0, 460, Y + 120)
    br_v = at(ed.add_branch_node(), 600, Y); link(gtd, "ReturnValue", br_v, "Condition")
    # before the task: "Talk to the janitor" in the top-left until a monster conversation opens
    YT = Y - 1300
    gw = fn("/Script/UMG.WidgetBlueprintLibrary:GetAllWidgetsOfClass", 300, YT)
    val(gw, "WidgetClass", "/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk.W_MonsterTalk_C"); val(gw, "TopLevelOnly", "true")
    link(seq, "then_1", gw, "execute")
    wl = named("Utilities|Array|Length", 300, YT + 200, [opin(gw, "FoundWidgets")]); link(gw, "FoundWidgets", wl, "TargetArray")
    open_ = fn(KML + "Greater_IntInt", 480, YT + 200); link(wl, "ReturnValue", open_, "A"); val(open_, "B", "0")
    br_w = at(ed.add_branch_node(), 620, YT); ex(gw, br_w); link(open_, "ReturnValue", br_w, "Condition")
    tk_s = setv("Talked", 820, YT); val(tk_s, "Talked", "true"); ex(br_w, tk_s)
    phz = get("Phase", 820, YT + 200); eqz = iconst_cmp("EqualEqual_IntInt", phz, "Phase", 0, 980, YT + 200)
    tk_g = get("Talked", 820, YT + 300); ntk = fn(KML + "Not_PreBool", 980, YT + 300); link(tk_g, "Talked", ntk, "A")
    andz = fn(KML + "BooleanAND", 1140, YT + 240); link(eqz, "ReturnValue", andz, "A"); link(ntk, "ReturnValue", andz, "B")
    br_z = at(ed.add_branch_node(), 1100, YT); link(br_w, "else", br_z, "execute"); ex(tk_s, br_z); link(andz, "ReturnValue", br_z, "Condition")
    TJ = "Talk to the janitor"
    jts = fn("/Script/Engine.HUD:GetTextSize", 1300, YT + 250); val(jts, "Text", TJ); val(jts, "Font", FONT); val(jts, "Scale", "1.5")
    jw = fn(KML + "Add_DoubleDouble", 1500, YT + 250); link(jts, "OutWidth", jw, "A"); val(jw, "B", "80")
    jbg = fn("/Script/Engine.HUD:DrawRect", 1300, YT)
    val(jbg, "RectColor", "(R=0.015,G=0.015,B=0.02,A=0.72)"); val(jbg, "ScreenX", "28"); val(jbg, "ScreenY", "28"); val(jbg, "ScreenH", "130")
    link(jw, "ReturnValue", jbg, "ScreenW"); link(br_z, "then", jbg, "execute")
    jac = fn("/Script/Engine.HUD:DrawRect", 1550, YT)
    val(jac, "RectColor", "(R=0.85,G=0.62,B=0.18,A=1.0)"); val(jac, "ScreenX", "28"); val(jac, "ScreenY", "28"); val(jac, "ScreenW", "6"); val(jac, "ScreenH", "130")
    ex(jbg, jac)
    jhd = fn("/Script/Engine.HUD:DrawText", 1800, YT)
    val(jhd, "Text", "TASKS"); val(jhd, "TextColor", "(R=0.85,G=0.62,B=0.18,A=1.0)"); val(jhd, "ScreenX", "54"); val(jhd, "ScreenY", "40")
    val(jhd, "Font", FONT); val(jhd, "Scale", "1.1"); ex(jac, jhd)
    jln = fn("/Script/Engine.HUD:DrawText", 2050, YT)
    val(jln, "Text", TJ); val(jln, "TextColor", "(R=0.95,G=0.93,B=0.88,A=1.0)"); val(jln, "ScreenX", "54"); val(jln, "ScreenY", "80")
    val(jln, "Font", FONT); val(jln, "Scale", "1.5"); ex(jhd, jln)
    ex(jln, br_v); link(br_z, "else", br_v, "execute")
    HINT = "Press TAB for task list"
    ts = fn("/Script/Engine.HUD:GetTextSize", 600, Y + 250); val(ts, "Text", HINT); val(ts, "Font", FONT); val(ts, "Scale", "1.3")
    sx_m = fn(KML + "Subtract_IntInt", 600, Y + 420); link(dh, "SizeX", sx_m, "A"); val(sx_m, "B", "40")
    sx_d = fn(KML + "Conv_IntToDouble", 780, Y + 420); link(sx_m, "ReturnValue", sx_d, "InInt")
    hx = fn(KML + "Subtract_DoubleDouble", 950, Y + 350); link(sx_d, "ReturnValue", hx, "A"); link(ts, "OutWidth", hx, "B")
    hint = fn("/Script/Engine.HUD:DrawText", 1150, Y)
    val(hint, "Text", HINT); val(hint, "TextColor", "(R=0.85,G=0.82,B=0.74,A=0.9)"); val(hint, "ScreenY", "28")
    val(hint, "Font", FONT); val(hint, "Scale", "1.3"); link(hx, "ReturnValue", hint, "ScreenX")
    ex(br_v, hint)
    sl2 = get("ShowList", 1150, Y + 300)
    br_l = at(ed.add_branch_node(), 1450, Y); link(sl2, "ShowList", br_l, "Condition")
    # "Press E to take out trash" prompt, centered low on screen, while standing at the dump with every bag
    P = "Press E to take out trash"
    ndg2 = get("NearDump", 1150, Y - 300)
    br_n = at(ed.add_branch_node(), 1300, Y - 420); ex(hint, br_n); link(ndg2, "NearDump", br_n, "Condition")
    link(br_n, "else", br_l, "execute")
    pts = fn("/Script/Engine.HUD:GetTextSize", 1300, Y - 700); val(pts, "Text", P); val(pts, "Font", FONT); val(pts, "Scale", "1.6")
    sxd = fn(KML + "Conv_IntToDouble", 1300, Y - 820); link(dh, "SizeX", sxd, "InInt")
    syd = fn(KML + "Conv_IntToDouble", 1300, Y - 900); link(dh, "SizeY", syd, "InInt")
    dx = fn(KML + "Subtract_DoubleDouble", 1500, Y - 820); link(sxd, "ReturnValue", dx, "A"); link(pts, "OutWidth", dx, "B")
    px = fn(KML + "Divide_DoubleDouble", 1680, Y - 820); link(dx, "ReturnValue", px, "A"); val(px, "B", "2.0")
    py = fn(KML + "Multiply_DoubleDouble", 1680, Y - 900); link(syd, "ReturnValue", py, "A"); val(py, "B", "0.66")
    rx = fn(KML + "Subtract_DoubleDouble", 1860, Y - 820); link(px, "ReturnValue", rx, "A"); val(rx, "B", "22")
    ry = fn(KML + "Subtract_DoubleDouble", 1860, Y - 900); link(py, "ReturnValue", ry, "A"); val(ry, "B", "12")
    rw = fn(KML + "Add_DoubleDouble", 1860, Y - 740); link(pts, "OutWidth", rw, "A"); val(rw, "B", "44")
    rh = fn(KML + "Add_DoubleDouble", 1860, Y - 660); link(pts, "OutHeight", rh, "A"); val(rh, "B", "24")
    pbg = fn("/Script/Engine.HUD:DrawRect", 1500, Y - 420); val(pbg, "RectColor", "(R=0.015,G=0.015,B=0.02,A=0.75)")
    link(rx, "ReturnValue", pbg, "ScreenX"); link(ry, "ReturnValue", pbg, "ScreenY"); link(rw, "ReturnValue", pbg, "ScreenW"); link(rh, "ReturnValue", pbg, "ScreenH")
    link(br_n, "then", pbg, "execute")
    ptx = fn("/Script/Engine.HUD:DrawText", 1750, Y - 420); val(ptx, "Text", P); val(ptx, "TextColor", "(R=1.0,G=0.95,B=0.85,A=1.0)")
    val(ptx, "Font", FONT); val(ptx, "Scale", "1.6"); link(px, "ReturnValue", ptx, "ScreenX"); link(py, "ReturnValue", ptx, "ScreenY")
    ex(pbg, ptx); ex(ptx, br_l)

    # task line text
    co3 = get("Collected", 1300, Y + 520); tb3 = get("TotalBags", 1300, Y + 600)
    cs = fn(KSL + "Conv_IntToString", 1480, Y + 520); link(co3, "Collected", cs, "InInt")
    tsx = fn(KSL + "Conv_IntToString", 1480, Y + 600); link(tb3, "TotalBags", tsx, "InInt")
    c1 = fn(KSL + "Concat_StrStr", 1660, Y + 520); link(cs, "ReturnValue", c1, "A"); val(c1, "B", " / ")
    c2 = fn(KSL + "Concat_StrStr", 1820, Y + 560); link(c1, "ReturnValue", c2, "A"); link(tsx, "ReturnValue", c2, "B")
    la = fn(KSL + "Concat_StrStr", 1980, Y + 480); val(la, "A", "Take out the trash       "); link(c2, "ReturnValue", la, "B")
    lb = fn(KSL + "Concat_StrStr", 1980, Y + 620); val(lb, "A", "Bring the trash to the dumpster       "); link(c2, "ReturnValue", lb, "B")
    co4 = get("Collected", 1980, Y + 760); tb4 = get("TotalBags", 1980, Y + 840)
    full = fn(KML + "GreaterEqual_IntInt", 2150, Y + 780); link(co4, "Collected", full, "A"); link(tb4, "TotalBags", full, "B")
    s1 = fn(KML + "SelectString", 2300, Y + 560); link(lb, "ReturnValue", s1, "A"); link(la, "ReturnValue", s1, "B"); link(full, "ReturnValue", s1, "bPickA")
    ph3 = get("Phase", 2300, Y + 760); done = iconst_cmp("EqualEqual_IntInt", ph3, "Phase", 2, 2450, Y + 760)
    s2 = fn(KML + "SelectString", 2600, Y + 560); val(s2, "A", "Take out the trash       COMPLETE"); link(s1, "ReturnValue", s2, "B"); link(done, "ReturnValue", s2, "bPickA")
    colr = fn(KML + "SelectColor", 2600, Y + 760); val(colr, "A", "(R=0.35,G=0.95,B=0.45,A=1.0)"); val(colr, "B", "(R=0.95,G=0.93,B=0.88,A=1.0)")
    link(done, "ReturnValue", colr, "bPickA")
    lw = fn("/Script/Engine.HUD:GetTextSize", 2800, Y + 560); link(s2, "ReturnValue", lw, "Text"); val(lw, "Font", FONT); val(lw, "Scale", "1.5")
    pw = fn(KML + "Add_DoubleDouble", 3000, Y + 560); link(lw, "OutWidth", pw, "A"); val(pw, "B", "80")

    bg = fn("/Script/Engine.HUD:DrawRect", 1700, Y)
    val(bg, "RectColor", "(R=0.015,G=0.015,B=0.02,A=0.72)"); val(bg, "ScreenX", "28"); val(bg, "ScreenY", "28"); val(bg, "ScreenH", "130")
    link(pw, "ReturnValue", bg, "ScreenW"); ex(br_l, bg)
    acc = fn("/Script/Engine.HUD:DrawRect", 1950, Y)
    val(acc, "RectColor", "(R=0.85,G=0.62,B=0.18,A=1.0)"); val(acc, "ScreenX", "28"); val(acc, "ScreenY", "28"); val(acc, "ScreenW", "6"); val(acc, "ScreenH", "130")
    ex(bg, acc)
    hdr = fn("/Script/Engine.HUD:DrawText", 2200, Y)
    val(hdr, "Text", "TASKS"); val(hdr, "TextColor", "(R=0.85,G=0.62,B=0.18,A=1.0)"); val(hdr, "ScreenX", "54"); val(hdr, "ScreenY", "40")
    val(hdr, "Font", FONT); val(hdr, "Scale", "1.1"); ex(acc, hdr)
    line = fn("/Script/Engine.HUD:DrawText", 2450, Y)
    link(s2, "ReturnValue", line, "Text"); link(colr, "ReturnValue", line, "TextColor"); val(line, "ScreenX", "54"); val(line, "ScreenY", "80")
    val(line, "Font", FONT); val(line, "Scale", "1.5"); ex(hdr, line)

    # ------------------------------------------------ frustration: janitor's bar, rises while the task is open, kills at 100
    ed.add_node_pin(seq); ed.add_node_pin(seq); ed.add_node_pin(seq); ed.add_node_pin(seq); ed.add_node_pin(seq)
    # ------------------------------------------------ "Press E to interact" while the crosshair is on a BP_Monster
    M = 7700
    pwm = fn("/Script/Engine.HUD:GetOwningPawn", 300, M + 200)
    cfp = named("Utilities|Casting|CastToBP_FirstPersonCharacter", 500, M, [opin(pwm, "ReturnValue")]); link(pwm, "ReturnValue", cfp, "Object")
    link(seq, "then_6", cfp, "execute")
    cfp_out = None
    for p in BEL.list_all_pins(cfp, unreal.EdGraphPinDirection.EGPD_OUTPUT):
        if str(PIN.get_pin_name(p)).startswith("As"):
            cfp_out = p
    ti = get("Trace_Item", 800, M + 200, "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter_C")
    if not PIN.try_create_connection(cfp_out, ipin(ti, "self")):
        log("ERR cast -> trace item")
    oc = fn("/Script/Engine.GameplayStatics:GetObjectClass", 1000, M + 200); link(ti, "Trace_Item", oc, "Object")
    isn = fn(KML + "ClassIsChildOf", 1200, M + 200); link(oc, "ReturnValue", isn, "TestClass"); val(isn, "ParentClass", "/Game/Blueprints/Dialogue/Blueprints/BP_Monster.BP_Monster_C")
    gwm = fn("/Script/UMG.WidgetBlueprintLibrary:GetAllWidgetsOfClass", 800, M)
    val(gwm, "WidgetClass", "/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk.W_MonsterTalk_C"); val(gwm, "TopLevelOnly", "true"); ex(cfp, gwm)
    wlm = named("Utilities|Array|Length", 1000, M + 320, [opin(gwm, "FoundWidgets")]); link(gwm, "FoundWidgets", wlm, "TargetArray")
    nod = fn(KML + "EqualEqual_IntInt", 1200, M + 320); link(wlm, "ReturnValue", nod, "A"); val(nod, "B", "0")
    dgm = get("Dead", 1200, M + 420); ndm = fn(KML + "Not_PreBool", 1350, M + 420); link(dgm, "Dead", ndm, "A")
    am1 = fn(KML + "BooleanAND", 1400, M + 260); link(isn, "ReturnValue", am1, "A"); link(nod, "ReturnValue", am1, "B")
    am2 = fn(KML + "BooleanAND", 1550, M + 340); link(am1, "ReturnValue", am2, "A"); link(ndm, "ReturnValue", am2, "B")
    br_m = at(ed.add_branch_node(), 1500, M); ex(gwm, br_m); link(am2, "ReturnValue", br_m, "Condition")
    PM = "Press E to interact"
    mts = fn("/Script/Engine.HUD:GetTextSize", 1700, M + 300); val(mts, "Text", PM); val(mts, "Font", FONT); val(mts, "Scale", "1.6")
    msx = fn(KML + "Conv_IntToDouble", 1700, M + 420); link(dh, "SizeX", msx, "InInt")
    msy = fn(KML + "Conv_IntToDouble", 1700, M + 500); link(dh, "SizeY", msy, "InInt")
    mdx = fn(KML + "Subtract_DoubleDouble", 1900, M + 420); link(msx, "ReturnValue", mdx, "A"); link(mts, "OutWidth", mdx, "B")
    mpx = fn(KML + "Divide_DoubleDouble", 2060, M + 420); link(mdx, "ReturnValue", mpx, "A"); val(mpx, "B", "2.0")
    mpy = fn(KML + "Multiply_DoubleDouble", 2060, M + 500); link(msy, "ReturnValue", mpy, "A"); val(mpy, "B", "0.66")
    mrx = fn(KML + "Subtract_DoubleDouble", 2220, M + 420); link(mpx, "ReturnValue", mrx, "A"); val(mrx, "B", "22")
    mry = fn(KML + "Subtract_DoubleDouble", 2220, M + 500); link(mpy, "ReturnValue", mry, "A"); val(mry, "B", "12")
    mrw = fn(KML + "Add_DoubleDouble", 2220, M + 300); link(mts, "OutWidth", mrw, "A"); val(mrw, "B", "44")
    mrh = fn(KML + "Add_DoubleDouble", 2220, M + 580); link(mts, "OutHeight", mrh, "A"); val(mrh, "B", "24")
    mbg = fn("/Script/Engine.HUD:DrawRect", 1750, M); val(mbg, "RectColor", "(R=0.015,G=0.015,B=0.02,A=0.75)")
    link(mrx, "ReturnValue", mbg, "ScreenX"); link(mry, "ReturnValue", mbg, "ScreenY"); link(mrw, "ReturnValue", mbg, "ScreenW"); link(mrh, "ReturnValue", mbg, "ScreenH")
    ex(br_m, mbg)
    mtx = fn("/Script/Engine.HUD:DrawText", 2000, M); val(mtx, "Text", PM); val(mtx, "TextColor", "(R=1.0,G=0.95,B=0.85,A=1.0)")
    val(mtx, "Font", FONT); val(mtx, "Scale", "1.6"); link(mpx, "ReturnValue", mtx, "ScreenX"); link(mpy, "ReturnValue", mtx, "ScreenY"); ex(mbg, mtx)
    # ------------------------------------------------ footsteps
    F = 6200
    pw = fn("/Script/Engine.HUD:GetOwningPawn", 300, F + 200)
    vel = fn("/Script/Engine.Actor:GetVelocity", 450, F + 200); link(pw, "ReturnValue", vel, "self")
    spd = fn(KML + "VSizeXY", 600, F + 200); link(vel, "ReturnValue", spd, "A")
    cmc = fn("/Script/Engine.Actor:GetComponentByClass", 450, F + 320); val(cmc, "ComponentClass", "/Script/Engine.CharacterMovementComponent"); link(pw, "ReturnValue", cmc, "self")
    gnd = None
    for gp in ("/Script/Engine.NavMovementComponent:IsMovingOnGround", "/Script/Engine.PawnMovementComponent:IsMovingOnGround", "/Script/Engine.CharacterMovementComponent:IsMovingOnGround", "/Script/Engine.MovementComponent:IsMovingOnGround"):
        gnd = ed.add_call_function_node(gp)
        if gnd:
            log("ground fn: " + gp); break
    at(gnd, 650, F + 320); link(cmc, "ReturnValue", gnd, "self")
    mov = fn(KML + "Greater_DoubleDouble", 760, F + 200); link(spd, "ReturnValue", mov, "A"); val(mov, "B", "40.0")
    walk = fn(KML + "BooleanAND", 900, F + 260); link(mov, "ReturnValue", walk, "A"); link(gnd, "ReturnValue", walk, "B")
    br_s = at(ed.add_branch_node(), 900, F); link(seq, "then_4", br_s, "execute"); link(walk, "ReturnValue", br_s, "Condition")
    # walking loop (roblox-walking) plays while moving on the ground, pauses when you stop
    sa_get = get("StepAudio", 1150, F + 200)
    go = fn("/Script/Engine.AudioComponent:SetPaused", 1200, F); val(go, "bPause", "false"); link(sa_get, "StepAudio", go, "self"); ex(br_s, go)
    sa_get2 = get("StepAudio", 1150, F + 420)
    stop = fn("/Script/Engine.AudioComponent:SetPaused", 1200, F + 300); val(stop, "bPause", "true"); link(sa_get2, "StepAudio", stop, "self"); link(br_s, "else", stop, "execute")

    # ------------------------------------------------ goofy bonk when the player shoves a floating chair
    B = 6900
    tgc = fn("/Script/Engine.GameplayStatics:GetAllActorsWithTag", 300, B); val(tgc, "Tag", "BonkChair"); link(seq, "then_5", tgc, "execute")
    fec = named("Utilities|Array|ForEachLoop", 600, B, [opin(tgc, "OutActors")]); link(tgc, "OutActors", fec, "Array"); ex(tgc, fec, "then", "Exec")
    pw2 = fn("/Script/Engine.HUD:GetOwningPawn", 600, B + 250)
    dist = fn("/Script/Engine.Actor:GetDistanceTo", 800, B + 250); link(pw2, "ReturnValue", dist, "self"); link(fec, "Array Element", dist, "OtherActor")
    near = fn(KML + "Less_DoubleDouble", 960, B + 250); link(dist, "ReturnValue", near, "A"); val(near, "B", "260.0")
    cv = fn("/Script/Engine.Actor:GetVelocity", 800, B + 360); link(fec, "Array Element", cv, "self")
    cs_ = fn(KML + "VSize", 960, B + 360); link(cv, "ReturnValue", cs_, "A")
    fast = fn(KML + "Greater_DoubleDouble", 1100, B + 360); link(cs_, "ReturnValue", fast, "A"); val(fast, "B", "90.0")
    now = fn("/Script/Engine.GameplayStatics:GetTimeSeconds", 800, B + 480)
    lb = get("LastBonk", 800, B + 560)
    since = fn(KML + "Subtract_DoubleDouble", 960, B + 500); link(now, "ReturnValue", since, "A"); link(lb, "LastBonk", since, "B")
    ready = fn(KML + "Greater_DoubleDouble", 1100, B + 500); link(since, "ReturnValue", ready, "A"); val(ready, "B", "0.45")
    a1 = fn(KML + "BooleanAND", 1250, B + 300); link(near, "ReturnValue", a1, "A"); link(fast, "ReturnValue", a1, "B")
    a2 = fn(KML + "BooleanAND", 1400, B + 380); link(a1, "ReturnValue", a2, "A"); link(ready, "ReturnValue", a2, "B")
    br_b = at(ed.add_branch_node(), 1300, B); link(fec, "LoopBody", br_b, "execute"); link(a2, "ReturnValue", br_b, "Condition")
    cl = fn("/Script/Engine.Actor:K2_GetActorLocation", 1450, B + 200); link(fec, "Array Element", cl, "self")
    bp_ = fn(KML + "RandomFloatInRange", 1450, B + 300); val(bp_, "Min", "0.85"); val(bp_, "Max", "1.3")
    snd_b = fn("/Script/Engine.GameplayStatics:PlaySoundAtLocation", 1650, B); val(snd_b, "Sound", "/Game/Office80s/Audio/SFX_80s_ChairBonk.SFX_80s_ChairBonk")
    link(cl, "ReturnValue", snd_b, "Location"); link(bp_, "ReturnValue", snd_b, "PitchMultiplier"); ex(br_b, snd_b)
    now2 = fn("/Script/Engine.GameplayStatics:GetTimeSeconds", 1900, B + 200)
    lb_s = setv("LastBonk", 1950, B); link(now2, "ReturnValue", lb_s, "LastBonk"); ex(snd_b, lb_s)

    Z = 3200
    tg = fn("/Script/Engine.GameplayStatics:GetAllActorsWithTag", 300, Z); val(tg, "Tag", "Janitor"); link(seq, "then_2", tg, "execute")
    fej = named("Utilities|Array|ForEachLoop", 600, Z, [opin(tg, "OutActors")]); link(tg, "OutActors", fej, "Array"); ex(tg, fej, "then", "Exec")
    js = setv("Janitor", 900, Z); link(fej, "LoopBody", js, "execute"); link(fej, "Array Element", js, "Janitor")
    gc = fn("/Script/Engine.Actor:GetComponentByClass", 900, Z + 200); val(gc, "ComponentClass", "/Script/UMG.WidgetComponent"); link(fej, "Array Element", gc, "self")
    php = get("Phase", 900, Z + 340); vis = iconst_cmp("EqualEqual_IntInt", php, "Phase", 1, 1060, Z + 340)
    sv = fn("/Script/Engine.SceneComponent:SetVisibility", 1150, Z); link(gc, "ReturnValue", sv, "self"); link(vis, "ReturnValue", sv, "bNewVisibility"); ex(js, sv)
    uw = fn("/Script/UMG.WidgetComponent:GetUserWidgetObject", 1150, Z + 200); link(gc, "ReturnValue", uw, "self")
    cst = named("Utilities|Casting|CastToWBP_Frustraion_Bar", 1400, Z, [opin(uw, "ReturnValue")]); link(uw, "ReturnValue", cst, "Object"); ex(sv, cst)
    cast_out = None
    for p in BEL.list_all_pins(cst, unreal.EdGraphPinDirection.EGPD_OUTPUT):
        if str(PIN.get_pin_name(p)).startswith("As"):
            cast_out = p
    fg = get("Frust", 1400, Z + 260); pct = fn(KML + "Divide_DoubleDouble", 1560, Z + 260); link(fg, "Frust", pct, "A"); val(pct, "B", "100.0")
    ps = at(ed.add_set_member_variable_node("Percent", "/Game/FrustrationBar/WBP_Frustraion_Bar.WBP_Frustraion_Bar_C"), 1750, Z)
    ex(cst, ps)
    if not PIN.try_create_connection(cast_out, ipin(ps, "self")):
        log("ERR cast -> percent self")
    link(pct, "ReturnValue", ps, "Percent")

    phf = get("Phase", 600, Z + 560); eqf = iconst_cmp("EqualEqual_IntInt", phf, "Phase", 1, 760, Z + 560)
    dg = get("Dead", 600, Z + 660); ndd = fn(KML + "Not_PreBool", 760, Z + 660); link(dg, "Dead", ndd, "A")
    af = fn(KML + "BooleanAND", 920, Z + 600); link(eqf, "ReturnValue", af, "A"); link(ndd, "ReturnValue", af, "B")
    brf = at(ed.add_branch_node(), 1000, Z + 460); link(fej, "Completed", brf, "execute"); link(af, "ReturnValue", brf, "Condition")
    dt = fn("/Script/Engine.GameplayStatics:GetWorldDeltaSeconds", 1000, Z + 760)
    rate = get("FrustPerSec", 1000, Z + 860)
    mul = fn(KML + "Multiply_DoubleDouble", 1180, Z + 780); link(dt, "ReturnValue", mul, "A"); link(rate, "FrustPerSec", mul, "B")
    fg2 = get("Frust", 1180, Z + 680); fad = fn(KML + "Add_DoubleDouble", 1340, Z + 700); link(fg2, "Frust", fad, "A"); link(mul, "ReturnValue", fad, "B")
    fmn = fn(KML + "FMin", 1500, Z + 700); link(fad, "ReturnValue", fmn, "A"); val(fmn, "B", "100.0")
    fs = setv("Frust", 1650, Z + 460); link(brf, "then", fs, "execute"); link(fmn, "ReturnValue", fs, "Frust")
    fg3 = get("Frust", 1650, Z + 640); fful = fn(KML + "GreaterEqual_DoubleDouble", 1800, Z + 640); link(fg3, "Frust", fful, "A"); val(fful, "B", "100.0")
    brk = at(ed.add_branch_node(), 1900, Z + 460); ex(fs, brk); link(fful, "ReturnValue", brk, "Condition")
    dset = setv("Dead", 2100, Z + 460); val(dset, "Dead", "true"); ex(brk, dset)
    pawn2 = fn("/Script/Engine.HUD:GetOwningPawn", 2100, Z + 660)
    ploc = fn("/Script/Engine.Actor:K2_GetActorLocation", 2280, Z + 640); link(pawn2, "ReturnValue", ploc, "self")
    fwd = fn("/Script/Engine.Actor:GetActorForwardVector", 2280, Z + 740); link(pawn2, "ReturnValue", fwd, "self")
    fsc = fn(KML + "Multiply_VectorFloat", 2440, Z + 740); link(fwd, "ReturnValue", fsc, "A"); val(fsc, "B", "170.0")
    fnp = fn(KML + "Add_VectorVector", 2600, Z + 680); link(ploc, "ReturnValue", fnp, "A"); link(fsc, "ReturnValue", fnp, "B")
    brv = fn(KML + "BreakVector", 2760, Z + 680); link(fnp, "ReturnValue", brv, "InVec")
    mkv = fn(KML + "MakeVector", 2920, Z + 680); link(brv, "X", mkv, "X"); link(brv, "Y", mkv, "Y"); val(mkv, "Z", "20.0")
    jg = get("Janitor", 2600, Z + 580)
    mv = fn("/Script/Engine.Actor:K2_SetActorLocation", 2350, Z + 460); link(jg, "Janitor", mv, "self"); link(mkv, "ReturnValue", mv, "NewLocation"); val(mv, "bTeleport", "true")
    nocol = fn("/Script/Engine.Actor:SetActorEnableCollision", 2200, Z + 300); link(jg, "Janitor", nocol, "self"); val(nocol, "bNewActorEnableCollision", "false")
    ex(dset, nocol); ex(nocol, mv)
    pc2 = fn("/Script/Engine.HUD:GetOwningPlayerController", 2600, Z + 860)
    dis = fn("/Script/Engine.Actor:DisableInput", 2650, Z + 460); link(pawn2, "ReturnValue", dis, "self"); link(pc2, "ReturnValue", dis, "PlayerController"); ex(mv, dis)
    dly = fn("/Script/Engine.KismetSystemLibrary:Delay", 2900, Z + 460); val(dly, "Duration", "3.5"); ex(dis, dly)
    rst = fn("/Script/Engine.KismetSystemLibrary:ExecuteConsoleCommand", 3150, Z + 460); val(rst, "Command", "RestartLevel")
    link(pc2, "ReturnValue", rst, "SpecificPlayer"); ex(dly, rst)

    # death screen
    D = Z + 1300
    dg2 = get("Dead", 300, D + 120)
    brd = at(ed.add_branch_node(), 450, D); link(seq, "then_3", brd, "execute"); link(dg2, "Dead", brd, "Condition")
    sxf = fn(KML + "Conv_IntToDouble", 450, D + 260); link(dh, "SizeX", sxf, "InInt")
    syf = fn(KML + "Conv_IntToDouble", 450, D + 340); link(dh, "SizeY", syf, "InInt")
    red = fn("/Script/Engine.HUD:DrawRect", 700, D); val(red, "RectColor", "(R=0.35,G=0.0,B=0.0,A=0.6)"); val(red, "ScreenX", "0"); val(red, "ScreenY", "0")
    link(sxf, "ReturnValue", red, "ScreenW"); link(syf, "ReturnValue", red, "ScreenH"); ex(brd, red)
    T1, T2 = "YOU DIED", "The janitor got tired of waiting."
    s1z = fn("/Script/Engine.HUD:GetTextSize", 700, D + 300); val(s1z, "Text", T1); val(s1z, "Font", FONT); val(s1z, "Scale", "4.0")
    s2z = fn("/Script/Engine.HUD:GetTextSize", 700, D + 460); val(s2z, "Text", T2); val(s2z, "Font", FONT); val(s2z, "Scale", "1.5")
    d1 = fn(KML + "Subtract_DoubleDouble", 900, D + 300); link(sxf, "ReturnValue", d1, "A"); link(s1z, "OutWidth", d1, "B")
    x1 = fn(KML + "Divide_DoubleDouble", 1060, D + 300); link(d1, "ReturnValue", x1, "A"); val(x1, "B", "2.0")
    d2 = fn(KML + "Subtract_DoubleDouble", 900, D + 460); link(sxf, "ReturnValue", d2, "A"); link(s2z, "OutWidth", d2, "B")
    x2 = fn(KML + "Divide_DoubleDouble", 1060, D + 460); link(d2, "ReturnValue", x2, "A"); val(x2, "B", "2.0")
    y1 = fn(KML + "Multiply_DoubleDouble", 1060, D + 380); link(syf, "ReturnValue", y1, "A"); val(y1, "B", "0.36")
    y2a = fn(KML + "Add_DoubleDouble", 1220, D + 380); link(y1, "ReturnValue", y2a, "A"); link(s1z, "OutHeight", y2a, "B")
    t1 = fn("/Script/Engine.HUD:DrawText", 950, D); val(t1, "Text", T1); val(t1, "TextColor", "(R=0.95,G=0.08,B=0.05,A=1.0)")
    val(t1, "Font", FONT); val(t1, "Scale", "4.0"); link(x1, "ReturnValue", t1, "ScreenX"); link(y1, "ReturnValue", t1, "ScreenY"); ex(red, t1)
    t2 = fn("/Script/Engine.HUD:DrawText", 1200, D); val(t2, "Text", T2); val(t2, "TextColor", "(R=0.95,G=0.9,B=0.85,A=1.0)")
    val(t2, "Font", FONT); val(t2, "Scale", "1.5"); link(x2, "ReturnValue", t2, "ScreenX"); link(y2a, "ReturnValue", t2, "ScreenY"); ex(t1, t2)

    ghosts = [n for n in ed.list_nodes_of_class(unreal.K2Node_Event) if not any(len(PIN.list_connected_pins(p)) for p in BEL.list_all_pins(n))]
    ed.remove_nodes(ghosts)
    log("removed %d unused default events" % len(ghosts))
    rw = unreal.load_asset("/Game/Office80s/Audio/roblox-walking")
    rw.set_editor_property("looping", True); unreal.EditorAssetLibrary.save_loaded_asset(rw)
    BEL.compile_blueprint(bp)
    for n in ed.list_nodes_with_errors():
        log("COMPILE ERROR on %s (%s)" % (n.get_name(), BEL.get_node_title(n)))
    for n in ed.list_nodes_with_warnings():
        log("compile warning on %s (%s)" % (n.get_name(), BEL.get_node_title(n)))
    hcdo = unreal.get_default_object(BEL.generated_class(bp))
    hcdo.set_editor_property("FrustPerSec", 0.6666667); hcdo.set_editor_property("Phase", 0)   # full bar in about 3 minutes
    unreal.EditorAssetLibrary.save_loaded_asset(bp)

    # use it as the HUD for the game mode the Office runs with
    gm_bp = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode")
    cdo = unreal.get_default_object(BEL.generated_class(gm_bp))
    log("old HUD class: %s" % cdo.get_editor_property("hud_class"))
    cdo.set_editor_property("hud_class", BEL.generated_class(bp))
    gm_bp.modify()
    BEL.compile_blueprint(gm_bp)
    unreal.get_default_object(BEL.generated_class(gm_bp)).set_editor_property("hud_class", BEL.generated_class(bp))
    unreal.EditorAssetLibrary.save_loaded_asset(gm_bp)
    log("HUD class now: %s" % unreal.get_default_object(BEL.generated_class(gm_bp)).get_editor_property("hud_class"))

    # keep the task actors always loaded so the bag count is right
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in sub.get_all_level_actors():
        c = a.get_class().get_name()
        if c in ("BP_TrashBag_C", "BP_TrashDropOff_C", "BP_QuestManager_C") or a.get_actor_label() == "garbagedump":
            try:
                if a.get_editor_property("is_spatially_loaded"):
                    a.modify(); a.set_editor_property("is_spatially_loaded", False); n += 1
            except Exception as e:
                log("spatial flag: %s" % e)
    log("always-loaded set on %d actors" % n)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("task HUD built")


try:
    main()
except Exception as e:
    import traceback
    log('EXCEPTION ' + traceback.format_exc())
finally:
    open(os.path.join(here, 'build_task_hud.log'), 'w').write('\n'.join(LOG))
