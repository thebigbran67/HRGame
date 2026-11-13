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
for name, t in (("Phase", "int"), ("TotalBags", "int"), ("Collected", "int"), ("ShowList", "bool"), ("NearDump", "bool"), ("Talked", "bool"), ("Frust", "real"), ("FrustPerSec", "real"), ("Dead", "bool"), ("LastCollected", "int"), ("StepAcc", "real"), ("LastBonk", "real"), ("DoneTime", "real"), ("BobTime", "real"), ("BobBlend", "real"), ("BobOffset", "real"), ("ShiftHeld", "bool"), ("Stamina", "real"), ("Exhausted", "bool"), ("LastSprint", "real"), ("Sprinting", "bool"), ("PhaseSeen", "real"), ("PhaseTime", "real"), ("CollectTime", "real"), ("ListAnim", "real"), ("PromptStart", "real"), ("LastPromptT", "real"), ("DeadTime", "real"), ("InBath", "bool"), ("BathTime", "real"), ("LastBathT", "real"), ("IntroStart", "real"), ("BlipNext", "real")):
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

# ======================================================================== tiny expression -> blueprint compiler
import ast as _ast
UI = "/Game/Office80s/UI/"
INT_VARS = {"Phase", "TotalBags", "Collected", "LastCollected"}
BOOL_VARS = {"ShowList", "NearDump", "Talked", "Dead", "ShiftHeld", "Exhausted", "Sprinting", "InBath"}
_BIN = {_ast.Add: "Add_DoubleDouble", _ast.Sub: "Subtract_DoubleDouble", _ast.Mult: "Multiply_DoubleDouble", _ast.Div: "Divide_DoubleDouble"}
_CMP = {_ast.Lt: "Less_DoubleDouble", _ast.Gt: "Greater_DoubleDouble", _ast.LtE: "LessEqual_DoubleDouble", _ast.GtE: "GreaterEqual_DoubleDouble",
        _ast.Eq: "EqualEqual_DoubleDouble", _ast.NotEq: "NotEqual_DoubleDouble"}
_FN = {"sin": ("Sin", ["A"]), "cos": ("Cos", ["A"]), "abs": ("Abs", ["A"]), "frac": ("Fraction", ["A"]), "clamp": ("FClamp", ["Value", "Min", "Max"]),
       "min": ("FMin", ["A", "B"]), "max": ("FMax", ["A", "B"]), "lerp": ("Lerp", ["A", "B", "Alpha"]), "exp": ("Exp", ["A"])}

class X:
    """one per graph section: compiles expression strings into pure nodes (cached per section)"""
    def __init__(self, x, y, dh, env=None):
        self.x, self.y, self.n, self.dh = x, y, 0, dh
        self.env = dict(env or {}); self.cache = {}
    def pos(self):
        self.n += 1
        return self.x + (self.n % 14) * 200, self.y + 300 + (self.n // 14) * 110
    def f(self, path):
        x, y = self.pos(); return fn(path, x, y)
    def node(self, mk):
        x, y = self.pos(); return at(mk(x, y), x, y)
    # --- returns ("c", value, type) or ("p", node, pin, type)
    def c(self, src):
        return self._c(_ast.parse(src, mode="eval").body)
    def _c(self, e):
        if isinstance(e, _ast.Constant):
            if isinstance(e.value, bool):
                return ("c", e.value, "b")
            return ("c", float(e.value), "f")
        if isinstance(e, _ast.Name):
            return self.name(e.id)
        if isinstance(e, _ast.BinOp):
            a, b = self._c(e.left), self._c(e.right)
            if a[0] == "c" and b[0] == "c":
                op = type(e.op)
                return ("c", a[1] + b[1] if op is _ast.Add else a[1] - b[1] if op is _ast.Sub else a[1] * b[1] if op is _ast.Mult else a[1] / b[1], "f")
            n = self.f(KML + _BIN[type(e.op)]); self.bind_all(n, [("A", a), ("B", b)])
            return ("p", n, "ReturnValue", "f")
        if isinstance(e, _ast.UnaryOp):
            a = self._c(e.operand)
            if isinstance(e.op, _ast.USub):
                if a[0] == "c": return ("c", -a[1], "f")
                n = self.f(KML + "Multiply_DoubleDouble"); self.bind(n, "A", a); val(n, "B", "-1.0"); return ("p", n, "ReturnValue", "f")
            if isinstance(e.op, _ast.Not):
                if a[0] == "c": return ("c", not a[1], "b")
                n = self.f(KML + "Not_PreBool"); self.bind(n, "A", a); return ("p", n, "ReturnValue", "b")
        if isinstance(e, _ast.BoolOp):
            parts = [self._c(v) for v in e.values]
            cur = parts[0]
            for p in parts[1:]:
                n = self.f(KML + ("BooleanAND" if isinstance(e.op, _ast.And) else "BooleanOR")); self.bind_all(n, [("A", cur), ("B", p)])
                cur = ("p", n, "ReturnValue", "b")
            return cur
        if isinstance(e, _ast.Compare):
            a, b = self._c(e.left), self._c(e.comparators[0])
            n = self.f(KML + _CMP[type(e.ops[0])]); self.bind_all(n, [("A", a), ("B", b)])
            return ("p", n, "ReturnValue", "b")
        if isinstance(e, _ast.IfExp):
            cnd, a, b = self._c(e.test), self._c(e.body), self._c(e.orelse)
            n = self.f(KML + "SelectFloat"); self.bind_all(n, [("A", a), ("B", b), ("bPickA", cnd)])
            return ("p", n, "ReturnValue", "f")
        if isinstance(e, _ast.Call):
            nm = e.func.id; args = [self._c(a) for a in e.args]
            if nm == "interp":
                n = self.f(KML + "FInterpTo"); self.bind_all(n, [("Current", args[0]), ("Target", args[1]), ("DeltaTime", self.name("DT")), ("InterpSpeed", args[2])])
                return ("p", n, "ReturnValue", "f")
            path, pins = _FN[nm]
            n = self.f(KML + path)
            self.bind_all(n, list(zip(pins, args)))
            return ("p", n, "ReturnValue", "f")
        raise RuntimeError("unsupported expression %s" % _ast.dump(e))
    def name(self, nm):
        if nm in self.env: return self.env[nm]
        if nm in self.cache: return self.cache[nm]
        if nm == "T":
            n = self.f("/Script/Engine.GameplayStatics:GetTimeSeconds"); r = ("p", n, "ReturnValue", "f")
        elif nm == "DT":
            n = self.f("/Script/Engine.GameplayStatics:GetWorldDeltaSeconds"); r = ("p", n, "ReturnValue", "f")
        elif nm in ("SX", "SY"):
            n = self.f(KML + "Conv_IntToDouble"); link(self.dh, "SizeX" if nm == "SX" else "SizeY", n, "InInt"); r = ("p", n, "ReturnValue", "f")
        elif nm == "U":
            r = self.c("SY / 1080.0")
        else:
            x, y = self.pos(); g = get(nm, x, y)
            if nm in INT_VARS:
                n = self.f(KML + "Conv_IntToDouble"); link(g, nm, n, "InInt"); r = ("p", n, "ReturnValue", "f")
            else:
                r = ("p", g, nm, "b" if nm in BOOL_VARS else "f")
        self.cache[nm] = r
        return r
    def bind(self, node, pin, v):
        if isinstance(v, str):
            v = self.c(v)
        if v[0] == "c":
            val(node, pin, ("true" if v[1] else "false") if v[2] == "b" else repr(float(v[1])))
        else:
            link(v[1], v[2], node, pin)
    def bind_all(self, node, pairs):
        pairs = [(p, self.c(v) if isinstance(v, str) else v) for p, v in pairs]
        for p, v in pairs:
            if v[0] == "p": self.bind(node, p, v)
        for p, v in pairs:
            if v[0] == "c": self.bind(node, p, v)
    def color(self, r, g, b, a):
        cs = [self.c(s) if isinstance(s, str) else ("c", float(s), "f") for s in (r, g, b, a)]
        if all(c[0] == "c" for c in cs):
            return "(R=%f,G=%f,B=%f,A=%f)" % tuple(c[1] for c in cs)
        n = self.f(KML + "MakeColor")
        self.bind_all(n, list(zip("RGBA", cs)))
        return ("p", n, "ReturnValue", "s")

class Chain:
    def __init__(self, X_, outs):
        self.X = X_; self.outs = list(outs)
    def add(self, node):
        for n, p in self.outs:
            if not PIN.try_create_connection(BEL.find_output_pin(n, p), BEL.find_input_pin(node, "execute")):
                log("ERR exec %s.%s -> %s" % (n.get_name(), p, node.get_name()))
        self.outs = [(node, "then")]
        return node
    def when(self, cond, body):
        br = self.X.node(lambda x, y: ed.add_branch_node()); self.add(br); self.X.bind(br, "Condition", cond)
        self.outs = [(br, "then")]; body(); self.outs = self.outs + [(br, "else")]
    def set(self, var, expr):
        x, y = self.X.pos(); n = setv(var, x, y); self.add(n); self.X.bind(n, var, expr); return n
    def tex(self, name, x, y, w, h, tint=None, u="0", v="0", uw="1", vh="1", rot="0", piv=(0.5, 0.5)):
        n = self.X.f("/Script/Engine.HUD:DrawTexture"); self.add(n)
        val(n, "Texture", UI + name + "." + name)
        for p, e in (("ScreenX", x), ("ScreenY", y), ("ScreenW", w), ("ScreenH", h), ("TextureU", u), ("TextureV", v),
                     ("TextureUWidth", uw), ("TextureVHeight", vh), ("Rotation", rot)):
            self.X.bind(n, p, e)
        t = tint if tint is not None else "(R=1,G=1,B=1,A=1)"
        if isinstance(t, str): val(n, "TintColor", t)
        else: link(t[1], t[2], n, "TintColor")
        val(n, "BlendMode", "BLEND_Translucent"); val(n, "Scale", "1.0")
        val(n, "RotPivot", "(X=%f,Y=%f)" % piv)
        return n
    def rect(self, x, y, w, h, color):
        n = self.X.f("/Script/Engine.HUD:DrawRect"); self.add(n)
        for p, e in (("ScreenX", x), ("ScreenY", y), ("ScreenW", w), ("ScreenH", h)):
            self.X.bind(n, p, e)
        if isinstance(color, str): val(n, "RectColor", color)
        else: link(color[1], color[2], n, "RectColor")
        return n

# ======================================================================== animated monster-office HUD sections
def draw_prompt(ch, X, texname, w, h):
    """keycap prompt low and centered: pops in, pulses and bobs"""
    ch.when("T - LastPromptT > 0.25", lambda: ch.set("PromptStart", "T"))
    ch.set("LastPromptT", "T")
    k = "clamp((T - PromptStart) / 0.18, 0.0, 1.0)"
    s = "(1.0 + 0.035 * sin(T * 6.0)) * (0.55 + 0.45 * %s)" % k
    X.env["PS"] = X.c(s)
    ch.tex(texname, "SX / 2.0 - %f * U * PS" % (w / 2), "SY * 0.64 + 4.0 * U * sin(T * 3.0) - %f * U * PS" % (h / 2),
           "%f * U * PS" % w, "%f * U * PS" % h, tint=X.color(1, 1, 1, k))

def draw_main(seq, dh):
    """then_1: who-to-talk-to detection, then the sliding memo panel, sticky note and dump prompt"""
    X_ = X(300, -100, dh)
    gw = X_.f("/Script/UMG.WidgetBlueprintLibrary:GetAllWidgetsOfClass")
    val(gw, "WidgetClass", "/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk.W_MonsterTalk_C"); val(gw, "TopLevelOnly", "true")
    ch = Chain(X_, [(seq, "then_1")]); ch.add(gw)
    wl = X_.node(lambda x, y: ed.create_node_from_name("Utilities|Array|Length", unreal.Vector2D(x, y), [opin(gw, "FoundWidgets")]))
    link(gw, "FoundWidgets", wl, "TargetArray")
    wlf = X_.f(KML + "Conv_IntToDouble"); link(wl, "ReturnValue", wlf, "InInt")
    X_.env["OPEN"] = ("p", wlf, "ReturnValue", "f")
    ch.when("OPEN > 0.5", lambda: ch.set("Talked", "True"))
    ch.when("Phase != PhaseSeen", lambda: (ch.set("PhaseTime", "T"), ch.set("PhaseSeen", "Phase")))
    show = "(Phase == 0 and not Talked) or (Phase == 1 and (ShowList or T - PhaseTime < 4.5)) or Phase == 2"
    ch.set("ListAnim", "interp(ListAnim, (1.0 if %s else 0.0), 7.0)" % show)
    X_.cache.pop("ListAnim", None)

    def panel():
        X_.env["PX"] = X_.c("(24.0 - 740.0 * (1.0 - ListAnim)) * U")
        X_.env["PY"] = X_.c("(20.0 + 3.0 * sin(T * 1.4)) * U")
        # slime drip growing under the memo, then a drop falls off
        X_.env["DC"] = X_.c("frac(T * 0.32)")
        ch.tex("T_UI_Drip", "PX + 128.0 * U", "PY + 180.0 * U", "28.0 * U", "(26.0 + 74.0 * DC) * U")
        ch.when("DC < 0.4", lambda: ch.tex("T_UI_Drop", "PX + 134.0 * U", "PY + (300.0 + 1500.0 * DC * DC) * U", "16.0 * U", "22.0 * U",
                                           tint=X_.color(1, 1, 1, "1.0 - DC / 0.4")))
        ch.tex("T_UI_Memo", "PX", "PY", "680.0 * U", "220.0 * U")
        # the eye peeking over the corner: looks around and blinks
        ch.tex("T_UI_Eye", "PX + 598.0 * U", "PY - 22.0 * U", "80.0 * U", "80.0 * U")
        ch.tex("T_UI_Pupil", "PX + (620.0 + 10.0 * sin(T * 0.9)) * U", "PY + (-2.0 + 5.0 * sin(T * 1.7)) * U", "40.0 * U", "40.0 * U")
        ch.when("frac(T / 3.7) > 0.95", lambda: ch.tex("T_UI_Lid", "PX + 598.0 * U", "PY - 22.0 * U", "80.0 * U", "80.0 * U"))
        # task line
        def talk():
            ch.tex("T_UI_Check_Empty", "PX + 22.0 * U", "PY + 98.0 * U", "40.0 * U", "40.0 * U")
            ch.tex("T_UI_Line_Janitor", "PX + 72.0 * U", "PY + 98.0 * U", "304.5 * U", "40.0 * U")
        def trash():
            ch.when("Phase == 1 and Collected >= TotalBags",
                    lambda: ch.tex("T_UI_Line_Dump", "PX + 72.0 * U", "PY + 98.0 * U", "491.5 * U", "40.0 * U"))
            ch.when("not (Phase == 1 and Collected >= TotalBags)",
                    lambda: ch.tex("T_UI_Line_Trash", "PX + 72.0 * U", "PY + 98.0 * U", "289.0 * U", "40.0 * U"))
            ch.when("Phase == 2", lambda: (ch.tex("T_UI_Check_Done", "PX + 22.0 * U", "PY + 98.0 * U", "40.0 * U", "40.0 * U"),
                                           ch.rect("PX + 70.0 * U", "PY + 117.0 * U", "296.0 * U * clamp((T - DoneTime) / 0.45, 0.0, 1.0)", "3.0 * U",
                                                   "(R=0.16,G=0.10,B=0.08,A=1.0)")))
            ch.when("Phase == 1", lambda: ch.tex("T_UI_Check_Empty", "PX + 22.0 * U", "PY + 98.0 * U", "40.0 * U", "40.0 * U"))
            def counter():
                X_.env["POP"] = X_.c("clamp(1.0 - (T - CollectTime) / 0.5, 0.0, 1.0)")
                X_.env["DS"] = X_.c("1.0 + 0.5 * POP")
                ink = X_.color("lerp(0.16, 0.25, POP)", "lerp(0.11, 0.85, POP)", "lerp(0.09, 0.12, POP)", 1)
                for i, (u) in enumerate(("Collected / 11.0", "10.0 / 11.0", "TotalBags / 11.0")):
                    ch.tex("T_UI_Digits", "PX + (586.0 + %d * 24.0) * U - (DS - 1.0) * 12.0 * U" % i, "PY + 98.0 * U - (DS - 1.0) * 20.0 * U",
                           "24.0 * U * DS", "40.0 * U * DS", tint=ink, u=u, uw="1.0 / 11.0")
                ch.when("T - CollectTime < 1.2", lambda: ch.tex(
                    "T_UI_Plus1", "PX + 560.0 * U", "PY + (150.0 - 60.0 * (T - CollectTime)) * U", "113.0 * U", "40.0 * U",
                    tint=X_.color(1, 1, 1, "1.0 - (T - CollectTime) / 1.2")))
            ch.when("Phase == 1", counter)
            # stamps slam onto the memo
            X_.env["KN"] = X_.c("clamp((T - PhaseTime - 0.35) / 0.22, 0.0, 1.0)")
            ch.when("Phase == 1 and T - PhaseTime < 4.5", lambda: ch.tex(
                "T_UI_Stamp_New", "PX + 430.0 * U - 170.0 * U * (2.4 - 1.4 * KN)", "PY + 120.0 * U - 65.0 * U * (2.4 - 1.4 * KN)",
                "340.0 * U * (2.4 - 1.4 * KN)", "130.0 * U * (2.4 - 1.4 * KN)", tint=X_.color(1, 1, 1, "KN * clamp((4.5 - (T - PhaseTime)) / 0.6, 0.0, 1.0)")))
            X_.env["KD"] = X_.c("clamp((T - DoneTime - 0.2) / 0.22, 0.0, 1.0)")
            ch.when("Phase == 2", lambda: ch.tex(
                "T_UI_Stamp_Done", "PX + 430.0 * U - 170.0 * U * (2.4 - 1.4 * KD)", "PY + 120.0 * U - 65.0 * U * (2.4 - 1.4 * KD)",
                "340.0 * U * (2.4 - 1.4 * KD)", "130.0 * U * (2.4 - 1.4 * KD)", tint=X_.color(1, 1, 1, "KD")))
        ch.when("Phase == 0", talk)
        ch.when("Phase > 0", trash)
    ch.when("ListAnim > 0.01", panel)
    # sticky note: drops in once the task is handed out, then sways
    X_.env["KT"] = X_.c("clamp((T - PhaseTime - 0.8) / 0.45, 0.0, 1.0)")
    ch.when("Phase == 1 and not Dead", lambda: ch.tex(
        "T_UI_NoteTab", "SX - 352.0 * U", "(16.0 - 190.0 * (1.0 - KT) * (1.0 - KT)) * U", "320.0 * U", "140.0 * U",
        rot="4.0 * sin(T * 1.8) + 10.0 * (1.0 - KT)", piv=(0.5, 0.0)))
    ch.when("NearDump", lambda: draw_prompt(ch, X_, "T_UI_Prompt_Dump", 464.0, 96.0))

def draw_sprint(br_ui, dh):
    X_ = X(2900, 10200, dh); ch = Chain(X_, [(br_ui, "then")])
    X_.env["SH"] = X_.c("(3.0 * sin(T * 47.0) * U) if Exhausted else 0.0")
    X_.env["BX"] = X_.c("SX / 2.0 + SH")
    ch.tex("T_UI_SprintFrame", "BX - 220.0 * U", "SY - 96.0 * U", "440.0 * U", "40.0 * U")
    tint = X_.color("1.0 if Exhausted else 0.9", "0.3 if Exhausted else 0.92 + 0.08 * sin(T * 4.0)", "0.2 if Exhausted else 0.9", 1)
    ch.when("Stamina > 0.005", lambda: ch.tex("T_UI_SprintFill", "BX - 206.0 * U", "SY - 88.0 * U", "412.0 * U * Stamina", "24.0 * U",
                                              tint=tint, u="frac(T * (0.6 if Sprinting else 0.15))", uw="412.0 * Stamina / 128.0"))
    ch.when("Exhausted", lambda: ch.tex("T_UI_SprintOut", "SX / 2.0 - 107.0 * U", "SY - 50.0 * U", "214.5 * U", "36.5 * U",
                                        tint=X_.color(1, 1, 1, "0.6 + 0.4 * sin(T * 8.0)")))
    ch.when("not Exhausted", lambda: ch.tex("T_UI_SprintLabel", "SX / 2.0 - 125.0 * U", "SY - 50.0 * U", "250.0 * U", "44.0 * U",
                                            tint="(R=1,G=1,B=1,A=0.85)"))

def draw_interact(br_m, dh):
    X_ = X(1700, 7700, dh); ch = Chain(X_, [(br_m, "then")])
    draw_prompt(ch, X_, "T_UI_Prompt_Interact", 371.0, 96.0)

def draw_death(seq, dh):
    X_ = X(300, 4500, dh); ch = Chain(X_, [(seq, "then_3")])
    def body():
        ch.when("DeadTime < 0.001", lambda: ch.set("DeadTime", "T"))
        X_.env["D"] = X_.c("T - DeadTime")
        ch.tex("T_UI_DeathVignette", "0.0", "0.0", "SX", "SY", tint=X_.color(1, 1, 1, "clamp(D / 0.4, 0.0, 1.0)"))
        ch.rect("0.0", "0.0", "SX", "SY", X_.color(0.05, 0, 0, "0.55 * clamp(D / 0.6, 0.0, 1.0)"))
        X_.env["KC"] = X_.c("clamp(D / 0.2, 0.0, 1.0)")
        ch.tex("T_UI_DeathClaw", "SX / 2.0 - 450.0 * U", "SY / 2.0 - 300.0 * U", "900.0 * U * KC", "520.0 * U", uw="KC")
        X_.env["KT2"] = X_.c("clamp((D - 0.25) / 0.25, 0.0, 1.0)")
        X_.env["TS"] = X_.c("1.0 + 0.6 * (1.0 - KT2)")
        X_.env["SHK"] = X_.c("7.0 * U * sin(T * 41.0) * clamp(1.4 - D, 0.0, 1.0)")
        ch.tex("T_UI_DeathTitle", "SX / 2.0 - 336.5 * U * TS + SHK", "SY * 0.36 - 88.5 * U * TS", "673.0 * U * TS", "177.0 * U * TS",
               tint=X_.color(1, 1, 1, "KT2"))
        ch.tex("T_UI_DeathSub", "SX / 2.0 - 450.0 * U", "SY * 0.36 + 120.0 * U", "900.0 * U", "60.0 * U",
               tint=X_.color(1, 1, 1, "clamp((D - 0.9) / 0.5, 0.0, 1.0)"))
    ch.when("Dead", body)

def build_bath_and_skip(seq, dh, F0, B0, A0):
    """then_10: slippery bathroom floor (low friction while inside) + caution sign; Space skips the intro"""
    ed.add_node_pin(seq)
    X_ = X(300, 11800, dh)
    pw = X_.f("/Script/Engine.HUD:GetOwningPawn")
    loc = X_.f("/Script/Engine.Actor:K2_GetActorLocation"); link(pw, "ReturnValue", loc, "self")
    bv = X_.f(KML + "BreakVector"); link(loc, "ReturnValue", bv, "InVec")
    X_.env["PXW"] = ("p", bv, "X", "f"); X_.env["PYW"] = ("p", bv, "Y", "f"); X_.env["PZW"] = ("p", bv, "Z", "f")
    cm = X_.f("/Script/Engine.Actor:GetComponentByClass"); val(cm, "ComponentClass", "/Script/Engine.CharacterMovementComponent"); link(pw, "ReturnValue", cm, "self")
    ch = Chain(X_, [(seq, "then_10")])
    ch.set("InBath", "PXW > 1945.0 and PXW < 3143.0 and PYW > -5726.0 and PYW < -4206.0 and PZW < 400.0")
    X_.cache.pop("InBath", None)
    for var, v_in, v_out in (("GroundFriction", 0.35, F0), ("BrakingDecelerationWalking", 80.0, B0), ("MaxAcceleration", 700.0, A0)):
        x, y = X_.pos()
        s = at(ed.add_set_member_variable_node(var, "/Script/Engine.CharacterMovementComponent"), x, y)
        ch.add(s); link(cm, "ReturnValue", s, "self"); X_.bind(s, var, "%f if InBath else %f" % (v_in, v_out))
    def entered():
        ch.when("T - LastBathT > 0.5", lambda: ch.set("BathTime", "T"))
        ch.set("LastBathT", "T")
        X_.env["KB"] = X_.c("clamp((T - BathTime) / 0.3, 0.0, 1.0)")
        X_.env["BS"] = X_.c("KB * (1.0 + 0.18 * sin(KB * 3.14159))")
        ch.tex("T_UI_Caution", "SX / 2.0 - 210.0 * U * BS", "(110.0 + 6.0 * sin(T * 2.6)) * U", "420.0 * U * BS", "120.0 * U * BS",
               tint=X_.color(1, 1, 1, "clamp(1.0 - (T - BathTime - 3.5) / 0.8, 0.35, 1.0)"), rot="5.0 * sin(T * 2.2)", piv=(0.5, 0.0))
    ch.when("InBath and not Dead", entered)

    # Space skips the intro cinematic
    sk = None
    for kn in ("Input|KeyboardEvents|SpaceBar", "Input|KeyboardEvents|Space Bar", "Input|KeyboardEvents|Space"):
        try:
            sk = ed.create_node_from_name(kn, unreal.Vector2D(0, -1800), [])
        except Exception:
            sk = None
        if sk:
            log("space key node: " + kn); break
    at(sk, 0, -1800)
    try:
        sk.set_editor_property("consume_input", False)
    except Exception as e:
        log("space consume flag: %s" % e)
    ga = fn("/Script/Engine.GameplayStatics:GetActorOfClass", 250, -1800); val(ga, "ActorClass", "/Script/LevelSequence.LevelSequenceActor")
    link(sk, "Pressed", ga, "execute")
    iv = fn("/Script/Engine.KismetSystemLibrary:IsValid", 250, -1650); link(ga, "ReturnValue", iv, "Object")
    br = at(ed.add_branch_node(), 500, -1800); ex(ga, br); link(iv, "ReturnValue", br, "Condition")
    gp = fn("/Script/LevelSequence.LevelSequenceActor:GetSequencePlayer", 500, -1650); link(ga, "ReturnValue", gp, "self")
    isp = fn("/Script/MovieScene.MovieSceneSequencePlayer:IsPlaying", 700, -1650); link(gp, "ReturnValue", isp, "self")
    br2 = at(ed.add_branch_node(), 750, -1800); ex(br, br2); link(isp, "ReturnValue", br2, "Condition")
    ge = fn("/Script/MovieScene.MovieSceneSequencePlayer:GoToEndAndStop", 1000, -1800); link(gp, "ReturnValue", ge, "self"); ex(br2, ge)


def intro_gate(dh, seq):
    """while the intro cinematic plays, the HUD only shows the driver's line (typed out with blips); otherwise run everything"""
    X_ = X(-900, 400, dh)
    ga = X_.f("/Script/Engine.GameplayStatics:GetActorOfClass"); val(ga, "ActorClass", "/Script/LevelSequence.LevelSequenceActor")
    ch = Chain(X_, [(dh, "then")]); ch.add(ga)
    iv = X_.f("/Script/Engine.KismetSystemLibrary:IsValid"); link(ga, "ReturnValue", iv, "Object")
    X_.env["SEQOK"] = ("p", iv, "ReturnValue", "b")
    gp = X_.f("/Script/LevelSequence.LevelSequenceActor:GetSequencePlayer"); link(ga, "ReturnValue", gp, "self")
    isp = X_.f("/Script/MovieScene.MovieSceneSequencePlayer:IsPlaying"); link(gp, "ReturnValue", isp, "self")
    X_.env["PLAYING"] = ("p", isp, "ReturnValue", "b")
    br1 = X_.node(lambda x, y: ed.add_branch_node()); ch.add(br1); X_.bind(br1, "Condition", "SEQOK")
    br2 = X_.node(lambda x, y: ed.add_branch_node()); link(br1, "then", br2, "execute"); X_.bind(br2, "Condition", "PLAYING")
    link(br1, "else", seq, "execute"); link(br2, "else", seq, "execute")
    c2 = Chain(X_, [(br2, "then")])
    c2.when("IntroStart < 0.001", lambda: c2.set("IntroStart", "T"))
    X_.env["E"] = X_.c("T - IntroStart")
    def sub():
        X_.env["KA"] = X_.c("clamp((E - 5.0) / 0.3, 0.0, 1.0) * clamp((12.3 - E) / 0.4, 0.0, 1.0)")
        X_.env["RV"] = X_.c("clamp((E - 5.4) / 2.8, 0.0, 1.0)")
        X_.env["BW"] = X_.c("%f * U" % 1134.5)
        X_.env["BYY"] = X_.c("SY - 190.0 * U + 12.0 * U * (1.0 - KA)")
        c2.tex("T_UI_SubBox", "SX / 2.0 - BW / 2.0", "BYY", "BW", "%f * U" % 120, tint=X_.color(1, 1, 1, "KA"))
        c2.when("RV > 0.001", lambda: c2.tex("T_UI_SubText", "SX / 2.0 - BW / 2.0 + 40.0 * U", "BYY + 46.0 * U", "%f * U * RV" % 1054.5,
                                             "%f * U" % 56.0, tint=X_.color(1, 1, 1, "KA"), uw="RV"))
        def blip():
            c2.set("BlipNext", "T + 0.075")
            n = X_.f("/Script/Engine.GameplayStatics:PlaySound2D"); c2.add(n)
            val(n, "Sound", "/Game/Office80s/Audio/SFX_80s_TextBlip.SFX_80s_TextBlip"); val(n, "VolumeMultiplier", "0.6")
        c2.when("RV > 0.0 and RV < 1.0 and T > BlipNext", blip)
    c2.when("E > 5.0 and E < 12.4", sub)

def import_ui():
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    d = os.path.join(here, "ui")
    tasks = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".png"):
            t = unreal.AssetImportTask(); t.filename = os.path.join(d, f); t.destination_path = "/Game/Office80s/UI"
            t.automated = True; t.replace_existing = True; t.save = False; tasks.append(t)
    tools.import_asset_tasks(tasks)
    n = 0
    for p in unreal.EditorAssetLibrary.list_assets("/Game/Office80s/UI", recursive=False):
        tx = unreal.load_asset(p)
        if isinstance(tx, unreal.Texture2D):
            tx.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
            tx.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
            tx.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
            tx.set_editor_property("never_stream", True)
            unreal.EditorAssetLibrary.save_loaded_asset(tx); n += 1
    log("ui textures: %d" % n)

def movement_defaults():
    ch = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")
    cdo = unreal.get_default_object(BEL.generated_class(ch))
    cm = cdo.get_editor_property("character_movement")
    v = (cm.get_editor_property("ground_friction"), cm.get_editor_property("braking_deceleration_walking"), cm.get_editor_property("max_acceleration"))
    log("movement defaults friction/braking/accel: %s" % (v,))
    return v

def main():
    global bp
    import_ui()
    F0, B0, A0 = movement_defaults()
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
    intro_gate(dh, seq)

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
    ctn = fn("/Script/Engine.GameplayStatics:GetTimeSeconds", 2650, 380); ct_s = setv("CollectTime", 2700, 300); link(ctn, "ReturnValue", ct_s, "CollectTime"); ex(lc_s, ct_s)
    ex(ct_s, nd_s); link(br_p, "else", nd_s, "execute")

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
    # remember when the task finished and stop the player, TempOverScreen fades in after that
    tnow = fn("/Script/Engine.GameplayStatics:GetTimeSeconds", 1300, -860)
    dts_s = setv("DoneTime", 1450, -1000); link(tnow, "ReturnValue", dts_s, "DoneTime"); ex(snd_d, dts_s)
    pwd = fn("/Script/Engine.HUD:GetOwningPawn", 1550, -860); pcd = fn("/Script/Engine.HUD:GetOwningPlayerController", 1550, -780)
    dsi = fn("/Script/Engine.Actor:DisableInput", 1700, -1000); link(pwd, "ReturnValue", dsi, "self"); link(pcd, "ReturnValue", dsi, "PlayerController"); ex(dts_s, dsi)

    draw_main(seq, dh)


    # ------------------------------------------------ frustration: janitor's bar, rises while the task is open, kills at 100
    ed.add_node_pin(seq); ed.add_node_pin(seq); ed.add_node_pin(seq); ed.add_node_pin(seq); ed.add_node_pin(seq); ed.add_node_pin(seq)
    # ------------------------------------------------ head bob: camera dips up and down while walking
    ed.add_node_pin(seq)
    Hb = 9300
    pb = fn("/Script/Engine.HUD:GetOwningPawn", 300, Hb + 200)
    vb = fn("/Script/Engine.Actor:GetVelocity", 450, Hb + 200); link(pb, "ReturnValue", vb, "self")
    sb = fn(KML + "VSizeXY", 600, Hb + 200); link(vb, "ReturnValue", sb, "A")
    cmb = fn("/Script/Engine.Actor:GetComponentByClass", 450, Hb + 320); val(cmb, "ComponentClass", "/Script/Engine.CharacterMovementComponent"); link(pb, "ReturnValue", cmb, "self")
    gb = at(ed.add_call_function_node("/Script/Engine.NavMovementComponent:IsMovingOnGround"), 650, Hb + 320); link(cmb, "ReturnValue", gb, "self")
    mvb = fn(KML + "Greater_DoubleDouble", 760, Hb + 200); link(sb, "ReturnValue", mvb, "A"); val(mvb, "B", "40.0")
    wkb = fn(KML + "BooleanAND", 900, Hb + 260); link(mvb, "ReturnValue", wkb, "A"); link(gb, "ReturnValue", wkb, "B")
    tgt = fn(KML + "SelectFloat", 1050, Hb + 260); val(tgt, "A", "1.0"); val(tgt, "B", "0.0"); link(wkb, "ReturnValue", tgt, "bPickA")
    dtb = fn("/Script/Engine.GameplayStatics:GetWorldDeltaSeconds", 1050, Hb + 400)
    bbg = get("BobBlend", 1050, Hb + 140)
    fin = fn(KML + "FInterpTo", 1220, Hb + 200); link(bbg, "BobBlend", fin, "Current"); link(tgt, "ReturnValue", fin, "Target"); link(dtb, "ReturnValue", fin, "DeltaTime"); val(fin, "InterpSpeed", "8.0")
    bbs = setv("BobBlend", 600, Hb); link(fin, "ReturnValue", bbs, "BobBlend"); link(seq, "then_8", bbs, "execute")
    # phase advances with speed (about 1.8 bobs per second at normal walking speed)
    rate = fn(KML + "Divide_DoubleDouble", 1220, Hb + 500); link(sb, "ReturnValue", rate, "A"); val(rate, "B", "650.0")
    w1 = fn(KML + "Multiply_DoubleDouble", 1380, Hb + 500); link(rate, "ReturnValue", w1, "A"); val(w1, "B", "10.0")
    w2 = fn(KML + "Multiply_DoubleDouble", 1540, Hb + 500); link(w1, "ReturnValue", w2, "A"); link(dtb, "ReturnValue", w2, "B")
    btg = get("BobTime", 1540, Hb + 600)
    bta = fn(KML + "Add_DoubleDouble", 1700, Hb + 540); link(btg, "BobTime", bta, "A"); link(w2, "ReturnValue", bta, "B")
    bts = setv("BobTime", 850, Hb); link(bta, "ReturnValue", bts, "BobTime"); ex(bbs, bts)
    btg2 = get("BobTime", 1100, Hb + 700)
    sn = fn(KML + "Sin", 1250, Hb + 700); link(btg2, "BobTime", sn, "A")
    bbg2 = get("BobBlend", 1250, Hb + 800)
    amp = fn(KML + "Multiply_DoubleDouble", 1400, Hb + 740); link(sn, "ReturnValue", amp, "A"); link(bbg2, "BobBlend", amp, "B")
    off = fn(KML + "Multiply_DoubleDouble", 1550, Hb + 740); link(amp, "ReturnValue", off, "A"); val(off, "B", "2.0")
    bog = get("BobOffset", 1550, Hb + 860)
    dlt = fn(KML + "Subtract_DoubleDouble", 1700, Hb + 780); link(off, "ReturnValue", dlt, "A"); link(bog, "BobOffset", dlt, "B")
    mkd = fn(KML + "MakeVector", 1850, Hb + 780); val(mkd, "X", "0.0"); val(mkd, "Y", "0.0"); link(dlt, "ReturnValue", mkd, "Z")
    camc = fn("/Script/Engine.Actor:GetComponentByClass", 1700, Hb + 950); val(camc, "ComponentClass", "/Script/Engine.CameraComponent"); link(pb, "ReturnValue", camc, "self")
    addl = fn("/Script/Engine.SceneComponent:K2_AddWorldOffset", 1100, Hb); link(camc, "ReturnValue", addl, "self"); link(mkd, "ReturnValue", addl, "DeltaLocation"); ex(bts, addl)
    bos = setv("BobOffset", 1400, Hb); link(off, "ReturnValue", bos, "BobOffset"); ex(addl, bos)

    # ------------------------------------------------ sprint: hold Shift, limited stamina with an exhaustion cooldown
    WALK, RUN, DRAIN, REGEN, DELAY, RECOVER = 650.0, 1000.0, 4.5, 6.0, 0.8, 0.35
    sk = None
    for kn in ("Input|KeyboardEvents|LeftShift", "Input|KeyboardEvents|Left Shift"):
        try:
            sk = ed.create_node_from_name(kn, unreal.Vector2D(0, -1400), [])
        except Exception:
            sk = None
        if sk:
            log("shift key node: " + kn); break
    at(sk, 0, -1400)
    try:
        sk.set_editor_property("consume_input", False)
    except Exception as e:
        log("shift consume flag: %s" % e)
    shp = setv("ShiftHeld", 250, -1450); val(shp, "ShiftHeld", "true"); link(sk, "Pressed", shp, "execute")
    shr = setv("ShiftHeld", 250, -1300); val(shr, "ShiftHeld", "false"); link(sk, "Released", shr, "execute")

    ed.add_node_pin(seq)
    S = 10200
    ps = fn("/Script/Engine.HUD:GetOwningPawn", 300, S + 300)
    vs = fn("/Script/Engine.Actor:GetVelocity", 450, S + 300); link(ps, "ReturnValue", vs, "self")
    ss = fn(KML + "VSizeXY", 600, S + 300); link(vs, "ReturnValue", ss, "A")
    cms = fn("/Script/Engine.Actor:GetComponentByClass", 450, S + 420); val(cms, "ComponentClass", "/Script/Engine.CharacterMovementComponent"); link(ps, "ReturnValue", cms, "self")
    gs = at(ed.add_call_function_node("/Script/Engine.NavMovementComponent:IsMovingOnGround"), 650, S + 420); link(cms, "ReturnValue", gs, "self")
    mws = at(ed.add_get_member_variable_node("MaxWalkSpeed", "/Script/Engine.CharacterMovementComponent"), 650, S + 520); link(cms, "ReturnValue", mws, "self")
    free = fn(KML + "Greater_DoubleDouble", 820, S + 520); link(mws, "MaxWalkSpeed", free, "A"); val(free, "B", "1.0")   # 0 = frozen by dialogue, leave it alone
    mov = fn(KML + "Greater_DoubleDouble", 820, S + 300); link(ss, "ReturnValue", mov, "A"); val(mov, "B", "40.0")
    shg = get("ShiftHeld", 820, S + 200); exg = get("Exhausted", 820, S + 620)
    nex = fn(KML + "Not_PreBool", 980, S + 620); link(exg, "Exhausted", nex, "A")
    stg = get("Stamina", 820, S + 720); hst = fn(KML + "Greater_DoubleDouble", 980, S + 720); link(stg, "Stamina", hst, "A"); val(hst, "B", "0.0")
    dds = get("Dead", 820, S + 820); nds = fn(KML + "Not_PreBool", 980, S + 820); link(dds, "Dead", nds, "A")
    c1 = fn(KML + "BooleanAND", 1150, S + 250); link(shg, "ShiftHeld", c1, "A"); link(mov, "ReturnValue", c1, "B")
    c2 = fn(KML + "BooleanAND", 1300, S + 350); link(c1, "ReturnValue", c2, "A"); link(gs, "ReturnValue", c2, "B")
    c3 = fn(KML + "BooleanAND", 1450, S + 450); link(c2, "ReturnValue", c3, "A"); link(free, "ReturnValue", c3, "B")
    c4 = fn(KML + "BooleanAND", 1600, S + 550); link(c3, "ReturnValue", c4, "A"); link(nex, "ReturnValue", c4, "B")
    c5 = fn(KML + "BooleanAND", 1750, S + 650); link(c4, "ReturnValue", c5, "A"); link(hst, "ReturnValue", c5, "B")
    c6 = fn(KML + "BooleanAND", 1900, S + 750); link(c5, "ReturnValue", c6, "A"); link(nds, "ReturnValue", c6, "B")
    sps = setv("Sprinting", 600, S); link(c6, "ReturnValue", sps, "Sprinting"); link(seq, "then_9", sps, "execute")
    dt9 = fn("/Script/Engine.GameplayStatics:GetWorldDeltaSeconds", 1100, S + 950)
    now9 = fn("/Script/Engine.GameplayStatics:GetTimeSeconds", 1100, S + 1050)
    br_sp = at(ed.add_branch_node(), 850, S); ex(sps, br_sp); link(c6, "ReturnValue", br_sp, "Condition")
    # sprinting: drain
    dr = fn(KML + "Divide_DoubleDouble", 1300, S + 950); link(dt9, "ReturnValue", dr, "A"); val(dr, "B", str(DRAIN))
    stg2 = get("Stamina", 1300, S + 1050); sdn = fn(KML + "Subtract_DoubleDouble", 1450, S + 1000); link(stg2, "Stamina", sdn, "A"); link(dr, "ReturnValue", sdn, "B")
    cl1 = fn(KML + "FClamp", 1600, S + 1000); link(sdn, "ReturnValue", cl1, "Value"); val(cl1, "Min", "0.0"); val(cl1, "Max", "1.0")
    sst1 = setv("Stamina", 1100, S - 300); link(cl1, "ReturnValue", sst1, "Stamina"); link(br_sp, "then", sst1, "execute")
    lss = setv("LastSprint", 1350, S - 300); link(now9, "ReturnValue", lss, "LastSprint"); ex(sst1, lss)
    stg3 = get("Stamina", 1500, S - 150); emp = fn(KML + "LessEqual_DoubleDouble", 1650, S - 150); link(stg3, "Stamina", emp, "A"); val(emp, "B", "0.0")
    br_e2 = at(ed.add_branch_node(), 1600, S - 300); ex(lss, br_e2); link(emp, "ReturnValue", br_e2, "Condition")
    exs = setv("Exhausted", 1850, S - 300); val(exs, "Exhausted", "true"); ex(br_e2, exs)
    # not sprinting: regen after a short delay; leave exhaustion once recovered enough
    lsg = get("LastSprint", 1300, S + 1150); since = fn(KML + "Subtract_DoubleDouble", 1450, S + 1150); link(now9, "ReturnValue", since, "A"); link(lsg, "LastSprint", since, "B")
    rdy = fn(KML + "Greater_DoubleDouble", 1600, S + 1150); link(since, "ReturnValue", rdy, "A"); val(rdy, "B", str(DELAY))
    br_r = at(ed.add_branch_node(), 1100, S + 100); link(br_sp, "else", br_r, "execute"); link(rdy, "ReturnValue", br_r, "Condition")
    rg = fn(KML + "Divide_DoubleDouble", 1300, S + 1250); link(dt9, "ReturnValue", rg, "A"); val(rg, "B", str(REGEN))
    stg4 = get("Stamina", 1300, S + 1350); sup = fn(KML + "Add_DoubleDouble", 1450, S + 1300); link(stg4, "Stamina", sup, "A"); link(rg, "ReturnValue", sup, "B")
    cl2 = fn(KML + "FClamp", 1600, S + 1300); link(sup, "ReturnValue", cl2, "Value"); val(cl2, "Min", "0.0"); val(cl2, "Max", "1.0")
    sst2 = setv("Stamina", 1350, S + 100); link(cl2, "ReturnValue", sst2, "Stamina"); ex(br_r, sst2)
    stg5 = get("Stamina", 1500, S + 250); rec = fn(KML + "GreaterEqual_DoubleDouble", 1650, S + 250); link(stg5, "Stamina", rec, "A"); val(rec, "B", str(RECOVER))
    br_x = at(ed.add_branch_node(), 1600, S + 100); ex(sst2, br_x); link(rec, "ReturnValue", br_x, "Condition")
    exc = setv("Exhausted", 1850, S + 100); val(exc, "Exhausted", "false"); ex(br_x, exc)
    # apply the speed (only when the dialogue isn't freezing the player)
    br_ap = at(ed.add_branch_node(), 2100, S); link(free, "ReturnValue", br_ap, "Condition")
    ex(exs, br_ap); link(br_e2, "else", br_ap, "execute"); ex(exc, br_ap); link(br_x, "else", br_ap, "execute"); link(br_r, "else", br_ap, "execute")
    spg = get("Sprinting", 2100, S + 200)
    spd_sel = fn(KML + "SelectFloat", 2250, S + 200); val(spd_sel, "A", str(RUN)); val(spd_sel, "B", str(WALK)); link(spg, "Sprinting", spd_sel, "bPickA")
    setspd = at(ed.add_set_member_variable_node("MaxWalkSpeed", "/Script/Engine.CharacterMovementComponent"), 2350, S)
    link(cms, "ReturnValue", setspd, "self"); link(spd_sel, "ReturnValue", setspd, "MaxWalkSpeed"); ex(br_ap, setspd)
    # bar at the bottom + "Shift to sprint" (animated slime tube)
    ph9 = get("Phase", 2350, S + 400); n2 = fn(KML + "NotEqual_IntInt", 2500, S + 400); link(ph9, "Phase", n2, "A"); val(n2, "B", "2")
    dd9 = get("Dead", 2350, S + 500); nd9 = fn(KML + "Not_PreBool", 2500, S + 500); link(dd9, "Dead", nd9, "A")
    show9 = fn(KML + "BooleanAND", 2650, S + 450); link(n2, "ReturnValue", show9, "A"); link(nd9, "ReturnValue", show9, "B")
    br_ui = at(ed.add_branch_node(), 2650, S); ex(setspd, br_ui); link(br_ap, "else", br_ui, "execute"); link(show9, "ReturnValue", br_ui, "Condition")
    draw_sprint(br_ui, dh)

    # ------------------------------------------------ TempOverScreen after the trash task (fades in over a second)
    O = 8500
    pho = get("Phase", 300, O + 150); eqo = iconst_cmp("EqualEqual_IntInt", pho, "Phase", 2, 460, O + 150)
    br_o = at(ed.add_branch_node(), 600, O); link(seq, "then_7", br_o, "execute"); link(eqo, "ReturnValue", br_o, "Condition")
    tn = fn("/Script/Engine.GameplayStatics:GetTimeSeconds", 600, O + 300); dtg = get("DoneTime", 600, O + 400)
    el = fn(KML + "Subtract_DoubleDouble", 780, O + 340); link(tn, "ReturnValue", el, "A"); link(dtg, "DoneTime", el, "B")
    el2 = fn(KML + "Subtract_DoubleDouble", 940, O + 340); link(el, "ReturnValue", el2, "A"); val(el2, "B", "1.0")
    al = fn(KML + "FClamp", 1100, O + 340); link(el2, "ReturnValue", al, "Value"); val(al, "Min", "0.0"); val(al, "Max", "1.0")
    mc = fn(KML + "MakeColor", 1260, O + 340); val(mc, "R", "1.0"); val(mc, "G", "1.0"); val(mc, "B", "1.0"); link(al, "ReturnValue", mc, "A")
    osx = fn(KML + "Conv_IntToDouble", 1100, O + 480); link(dh, "SizeX", osx, "InInt")
    osy = fn(KML + "Conv_IntToDouble", 1100, O + 560); link(dh, "SizeY", osy, "InInt")
    blk = fn("/Script/Engine.HUD:DrawRect", 850, O)
    bc = fn(KML + "MakeColor", 1260, O + 200); val(bc, "R", "0.0"); val(bc, "G", "0.0"); val(bc, "B", "0.0"); link(al, "ReturnValue", bc, "A")
    link(bc, "ReturnValue", blk, "RectColor"); val(blk, "ScreenX", "0"); val(blk, "ScreenY", "0"); link(osx, "ReturnValue", blk, "ScreenW"); link(osy, "ReturnValue", blk, "ScreenH")
    ex(br_o, blk)
    dtx = fn("/Script/Engine.HUD:DrawTexture", 1450, O)
    val(dtx, "Texture", "/Game/TempGameOver/TempOverScreen.TempOverScreen"); val(dtx, "ScreenX", "0"); val(dtx, "ScreenY", "0")
    link(osx, "ReturnValue", dtx, "ScreenW"); link(osy, "ReturnValue", dtx, "ScreenH")
    val(dtx, "TextureU", "0"); val(dtx, "TextureV", "0"); val(dtx, "TextureUWidth", "1"); val(dtx, "TextureVHeight", "1")
    link(mc, "ReturnValue", dtx, "TintColor"); val(dtx, "BlendMode", "BLEND_Translucent"); ex(blk, dtx)
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
    draw_interact(br_m, dh)
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
    draw_death(seq, dh)

    # bathroom floor + skip intro
    build_bath_and_skip(seq, dh, F0, B0, A0)


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
    hcdo.set_editor_property("FrustPerSec", 0.6666667); hcdo.set_editor_property("Phase", 0); hcdo.set_editor_property("Stamina", 1.0)   # full bar in about 3 minutes
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
    for a in sub.get_all_level_actors():
        if a.get_actor_label() == "IntroSequence":
            ps = a.get_editor_property("playback_settings"); ps.set_editor_property("hide_hud", False)
            a.modify(); a.set_editor_property("playback_settings", ps)
            log("intro sequence: hud allowed (subtitle only)")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("task HUD built")


try:
    main()
except Exception as e:
    import traceback
    log('EXCEPTION ' + traceback.format_exc())
finally:
    open(os.path.join(here, 'build_task_hud19.log'), 'w').write('\n'.join(LOG))
