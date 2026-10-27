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

for p in ("/Game/Office80s/Temp/BP_Probe", HUD_PATH):
    if unreal.EditorAssetLibrary.does_asset_exist(p):
        unreal.EditorAssetLibrary.delete_asset(p)
bp = BEL.create_blueprint_asset_with_parent(HUD_PATH, unreal.HUD)
for name, t in (("Phase", "int"), ("TotalBags", "int"), ("Collected", "int"), ("ShowList", "bool")):
    BEL.add_member_variable(bp, name, BEL.get_basic_type_by_name(t))
ed = BGE.get_graph_editor(BEL.find_event_graph(bp))

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

# ---------------------------------------------------------------- BeginPlay: listen for TAB
bpl = at(BEL.add_event_override(bp, "ReceiveBeginPlay", unreal.IntPoint(0, -600)), 0, -600)
en = fn("/Script/Engine.Actor:EnableInput", 300, -600)
pc = fn("/Script/Engine.HUD:GetOwningPlayerController", 60, -480)
ex(bpl, en); link(pc, "ReturnValue", en, "PlayerController")

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
br_d = at(ed.add_branch_node(), 2750, 480); ex(co_s, br_d); link(and2, "ReturnValue", br_d, "Condition")
ph_s2 = setv("Phase", 2950, 480); val(ph_s2, "Phase", "2"); ex(br_d, ph_s2)

# drawing
Y = 1200
ph2 = get("Phase", 300, Y + 120); gtd = iconst_cmp("Greater_IntInt", ph2, "Phase", 0, 460, Y + 120)
br_v = at(ed.add_branch_node(), 600, Y); link(seq, "then_1", br_v, "execute"); link(gtd, "ReturnValue", br_v, "Condition")
HINT = "Press TAB for task list"
ts = fn("/Script/Engine.HUD:GetTextSize", 600, Y + 250); val(ts, "Text", HINT); val(ts, "Font", FONT); val(ts, "Scale", "0.85")
sx_m = fn(KML + "Subtract_IntInt", 600, Y + 420); link(dh, "SizeX", sx_m, "A"); val(sx_m, "B", "36")
sx_d = fn(KML + "Conv_IntToDouble", 780, Y + 420); link(sx_m, "ReturnValue", sx_d, "InInt")
hx = fn(KML + "Subtract_DoubleDouble", 950, Y + 350); link(sx_d, "ReturnValue", hx, "A"); link(ts, "OutWidth", hx, "B")
hint = fn("/Script/Engine.HUD:DrawText", 1150, Y)
val(hint, "Text", HINT); val(hint, "TextColor", "(R=0.85,G=0.82,B=0.74,A=0.9)"); val(hint, "ScreenY", "30")
val(hint, "Font", FONT); val(hint, "Scale", "0.85"); link(hx, "ReturnValue", hint, "ScreenX")
ex(br_v, hint)
sl2 = get("ShowList", 1150, Y + 300)
br_l = at(ed.add_branch_node(), 1450, Y); ex(hint, br_l); link(sl2, "ShowList", br_l, "Condition")

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
lw = fn("/Script/Engine.HUD:GetTextSize", 2800, Y + 560); link(s2, "ReturnValue", lw, "Text"); val(lw, "Font", FONT); val(lw, "Scale", "0.95")
pw = fn(KML + "Add_DoubleDouble", 3000, Y + 560); link(lw, "OutWidth", pw, "A"); val(pw, "B", "64")

bg = fn("/Script/Engine.HUD:DrawRect", 1700, Y)
val(bg, "RectColor", "(R=0.015,G=0.015,B=0.02,A=0.72)"); val(bg, "ScreenX", "28"); val(bg, "ScreenY", "28"); val(bg, "ScreenH", "92")
link(pw, "ReturnValue", bg, "ScreenW"); ex(br_l, bg)
acc = fn("/Script/Engine.HUD:DrawRect", 1950, Y)
val(acc, "RectColor", "(R=0.85,G=0.62,B=0.18,A=1.0)"); val(acc, "ScreenX", "28"); val(acc, "ScreenY", "28"); val(acc, "ScreenW", "5"); val(acc, "ScreenH", "92")
ex(bg, acc)
hdr = fn("/Script/Engine.HUD:DrawText", 2200, Y)
val(hdr, "Text", "TASKS"); val(hdr, "TextColor", "(R=0.85,G=0.62,B=0.18,A=1.0)"); val(hdr, "ScreenX", "50"); val(hdr, "ScreenY", "38")
val(hdr, "Font", FONT); val(hdr, "Scale", "0.75"); ex(acc, hdr)
line = fn("/Script/Engine.HUD:DrawText", 2450, Y)
link(s2, "ReturnValue", line, "Text"); link(colr, "ReturnValue", line, "TextColor"); val(line, "ScreenX", "50"); val(line, "ScreenY", "70")
val(line, "Font", FONT); val(line, "Scale", "0.95"); ex(hdr, line)

BEL.compile_blueprint(bp)
for n in ed.list_nodes_with_errors():
    log("COMPILE ERROR on %s (%s)" % (n.get_name(), BEL.get_node_title(n)))
for n in ed.list_nodes_with_warnings():
    log("compile warning on %s (%s)" % (n.get_name(), BEL.get_node_title(n)))
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
open(os.path.join(here, "build_task_hud.log"), "w").write("\n".join(LOG))
log("task HUD built")
