"""BP_TaskHUD:
 1) spider spawn spots back to the originals (size stays 1.0)
 2) new function DrawSquishPrompt = same slime plate + font as the Press E prompt, text 'Left click to squish these little fuckers'
    and it replaces the old plain 'LEFT CLICK - SQUASH SPIDER' DrawText (same spot in the chain)."""
import unreal, os, ast, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary; EAL = unreal.EditorAssetLibrary
KML = "/Script/Engine.KismetMathLibrary:"
UI = "/Game/Office80s/UI/"
PFONT = "/Game/_TASKS/Font/F_TaskPrompt.F_TaskPrompt"
WORDS = "Left click to squish these little fuckers"
OUT_D = unreal.EdGraphPinDirection.EGPD_OUTPUT
L = []; BAD = []
def log(m): L.append(str(m)); unreal.log("[Squish] " + str(m))
def outp(n, name):
    p = BEL.find_output_pin(n, name)
    if p is None or not PIN.is_valid(p): raise RuntimeError("no out pin %s on %s" % (name, BEL.get_node_title(n)))
    return p
def inp(n, name):
    p = BEL.find_input_pin(n, name)
    if p is None or not PIN.is_valid(p): raise RuntimeError("no in pin %s on %s" % (name, BEL.get_node_title(n)))
    return p
def link(src, n, pin):
    if not PIN.try_create_connection(outp(src[0], src[1]), inp(n, pin)): BAD.append("%s.%s -> %s.%s" % (BEL.get_node_title(src[0]), src[1], BEL.get_node_title(n), pin))
def val(n, pin, v):
    if not PIN.set_pin_value(inp(n, pin), v): BAD.append("value %s=%s" % (pin, v))

ORIG = {(2470, -4767): (2100, -4920), (3252, -3712): (3030, -3620), (3630, -2470): (4030, -2470),
        (4563, -530): (4410, -900), (5427, -2003): (5710, -1720)}
try:
    hud = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
    ed = BGE.get_graph_editor(BEL.find_event_graph(hud))

    # ---------------- 1) spiders back
    moved = 0
    for n in ed.list_all_nodes():
        if not str(BEL.get_node_title(n)).startswith("MakeTransform"): continue
        lp = BEL.find_input_pin(n, "Location")
        if not lp: continue
        v = str(PIN.get_pin_value(lp))
        try: d = dict(kv.split("=") for kv in v.strip("()").split(","))
        except Exception: continue
        key = (int(round(float(d["X"]))), int(round(float(d["Y"]))))
        if key in ORIG.values():
            moved += 1; log("spider already at %s" % (key,)); continue
        if key in ORIG:
            ox, oy = ORIG[key]
            PIN.set_pin_value(lp, "(X=%d,Y=%d,Z=%s)" % (ox, oy, d["Z"]))
            moved += 1
            log("spider %s -> (%d,%d,%s)" % (key, ox, oy, d["Z"]))
    if moved != 5: raise RuntimeError("expected to move 5 spiders back, moved %d - not saving" % moved)

    # ---------------- 2) find the old prompt
    old = [n for n in ed.list_all_nodes() if str(BEL.get_node_title(n)).strip() == "DrawText" and BEL.find_input_pin(n, "Text")
           and "SQUASH" in str(PIN.get_pin_value(BEL.find_input_pin(n, "Text"))).upper()]
    if len(old) != 1: raise RuntimeError("expected 1 old squash DrawText, found %d" % len(old))
    old = old[0]
    before = list(PIN.list_connected_pins(inp(old, "execute")))
    after = list(PIN.list_connected_pins(outp(old, "then")))
    opos = BEL.get_node_pos(old)
    log("old prompt: %d in, %d out" % (len(before), len(after)))

    # ---------------- function DrawSquishPrompt
    if BEL.find_graph(hud, "DrawSquishPrompt"): raise RuntimeError("DrawSquishPrompt already exists")
    fed = BGE.create_and_edit_function_graph(hud, "DrawSquishPrompt")
    entry_then = fed.find_graph_entry_pin()
    entry = PIN.get_owning_node(entry_then)
    BEL.set_node_pos(entry, unreal.IntPoint(0, 0))
    pos = [300, 300]
    def place(n):
        BEL.set_node_pos(n, unreal.IntPoint(pos[0], pos[1])); pos[1] += 140
        if pos[1] > 1700: pos[1] = 300; pos[0] += 320
        return n
    def fn(path):
        n = fed.add_call_function_node(path)
        if n is None: raise RuntimeError("could not add " + path)
        return place(n)
    env = {}
    def expr(s):
        def go(t):
            if isinstance(t, ast.Constant): return float(t.value)
            if isinstance(t, ast.Name): return env[t.id]
            if isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.USub):
                v = go(t.operand); return -v if isinstance(v, float) else go(ast.BinOp(ast.Constant(0.0), ast.Sub(), t.operand))
            if isinstance(t, ast.Call) and t.func.id == "sin":
                a = go(t.args[0])
                n = fn(KML + "Sin")
                if isinstance(a, float): val(n, "A", repr(a))
                else: link(a, n, "A")
                return (n, "ReturnValue")
            if isinstance(t, ast.BinOp):
                a, b = go(t.left), go(t.right)
                ops = {ast.Add: ("Add", lambda x, y: x + y), ast.Sub: ("Subtract", lambda x, y: x - y),
                       ast.Mult: ("Multiply", lambda x, y: x * y), ast.Div: ("Divide", lambda x, y: x / y)}
                nm, f = ops[type(t.op)]
                if isinstance(a, float) and isinstance(b, float): return f(a, b)
                n = fn(KML + nm + "_DoubleDouble")
                if not isinstance(a, float): link(a, n, "A")
                if not isinstance(b, float): link(b, n, "B")
                if isinstance(a, float): val(n, "A", repr(a))
                if isinstance(b, float): val(n, "B", repr(b))
                return (n, "ReturnValue")
            raise RuntimeError("bad expr " + ast.dump(t))
        r = go(ast.parse(s, mode="eval").body)
        return r
    def bind(n, pin, s):
        r = expr(s)
        if isinstance(r, float): val(n, pin, repr(r))
        else: link(r, n, pin)

    pc = fn("/Script/Engine.HUD:GetOwningPlayerController")
    vs = fn("/Script/Engine.PlayerController:GetViewportSize"); link((pc, "ReturnValue"), vs, "self")
    sx = fn(KML + "Conv_IntToDouble"); link((vs, "SizeX"), sx, "InInt")
    sy = fn(KML + "Conv_IntToDouble"); link((vs, "SizeY"), sy, "InInt")
    tt = fn("/Script/Engine.GameplayStatics:GetTimeSeconds")
    gts = fn("/Script/Engine.HUD:GetTextSize"); val(gts, "Text", WORDS); val(gts, "Font", PFONT); val(gts, "Scale", "1.0")
    env.update(SX=(sx, "ReturnValue"), SY=(sy, "ReturnValue"), T=(tt, "ReturnValue"), W=(gts, "OutWidth"))
    # same numbers as the Press E prompt (1080p units, scaled by U)
    env["U"] = expr("SY / 1080.0")
    env["PS"] = expr("U * (1.0 + 0.035 * sin(T * 6.0))")
    env["BW"] = expr("24.0 + W * 1.25 + 26.0")
    env["PX0"] = expr("SX / 2.0 - BW * PS / 2.0")
    env["PY0"] = expr("SY * 0.64 + 4.0 * U * sin(T * 3.0) - 48.0 * PS")

    exec_prev = [entry_then]
    def chain(n):
        PIN.try_create_connection(exec_prev[0], inp(n, "execute")) or BAD.append("exec -> %s" % BEL.get_node_title(n))
        exec_prev[0] = outp(n, "then")
    def tex(name, x, y, w, h, uw="1.0"):
        n = fn("/Script/Engine.HUD:DrawTexture")
        val(n, "Texture", UI + name + "." + name)
        for p, e in (("ScreenX", x), ("ScreenY", y), ("ScreenW", w), ("ScreenH", h), ("TextureUWidth", uw)):
            bind(n, p, e)
        val(n, "TextureU", "0.0"); val(n, "TextureV", "0.0"); val(n, "TextureVHeight", "1.0")
        val(n, "TintColor", "(R=1,G=1,B=1,A=1)"); val(n, "BlendMode", "BLEND_Translucent"); val(n, "Scale", "1.0")
        chain(n)
    tex("T_UI_PromptM", "PX0 + 38.0 * PS", "PY0", "(BW - 76.0) * PS", "96.0 * PS", uw="(BW - 76.0) / 64.0")
    tex("T_UI_PlateL", "PX0", "PY0", "40.0 * PS", "96.0 * PS")
    tex("T_UI_PromptR", "PX0 + (BW - 40.0) * PS", "PY0", "40.0 * PS", "96.0 * PS")
    dt = fn("/Script/Engine.HUD:DrawText")
    val(dt, "Text", WORDS); val(dt, "Font", PFONT); val(dt, "TextColor", "(R=0.92,G=0.89,B=0.8,A=1)")
    bind(dt, "ScreenX", "PX0 + 24.0 * PS"); bind(dt, "ScreenY", "PY0 + 21.0 * PS"); bind(dt, "Scale", "1.25 * PS")
    chain(dt)
    fed.add_comment_node("SPIDER PROMPT - same slime plate and font as the Press E prompt. Change the words in GetTextSize AND DrawText.",
                         unreal.Vector2D(-60, -160), unreal.Vector2D(pos[0] + 500, 1950))
    BEL.compile_blueprint(hud)
    FN = BEL.generated_class(hud).get_path_name() + ":DrawSquishPrompt"

    # ---------------- swap the old DrawText for the new function call
    call = ed.add_call_function_node(FN)
    if call is None: raise RuntimeError("could not add call to " + FN)
    BEL.set_node_pos(call, opos)
    PIN.break_pin_links(inp(old, "execute")); PIN.break_pin_links(outp(old, "then"))
    for b in before:
        PIN.try_create_connection(b, inp(call, "execute")) or BAD.append("before -> call")
    for a in after:
        PIN.try_create_connection(outp(call, "then"), a) or BAD.append("call -> after")
    ed.remove_nodes([old])
    BEL.compile_blueprint(hud)
    errs = list(ed.list_nodes_with_errors()) + list(fed.list_nodes_with_errors())
    log("compile errors: %d %s" % (len(errs), [str(BEL.get_node_title(n)) for n in errs]))
    log("bad links: %s" % BAD)
    if errs or BAD:
        log("NOT saved")
    else:
        log("saved: %s" % EAL.save_loaded_asset(hud, False))
except Exception:
    log("EXCEPTION " + traceback.format_exc() + "\nNOT saved")
    try:
        if BEL.find_graph(hud, "DrawSquishPrompt") and not EAL.does_asset_exist("/Game/__never__"):
            BEL.remove_function_graph(hud, "DrawSquishPrompt"); log("removed half-built function")
    except Exception as e2:
        log("cleanup issue %s" % e2)
open(os.path.join(here, "squish_prompt2.log"), "w").write("\n".join(L))
