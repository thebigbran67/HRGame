"""Dialogue upgrade for W_MonsterTalk (no changes to its existing logic):
 - Typewriter: whatever text the dialogue logic puts in the Dialogue text block gets typed out fast,
   with a soft blip every few letters. Done in a new Tick event that only reads/rewrites the visible text.
 - Restyle: rounded dark dialogue box with an amber outline, amber name tag, response buttons as rounded
   'bubbles' that light up on hover, smaller cleaner text, options stacked neatly above the dialogue box."""
import os, unreal
BEL = unreal.BlueprintEditorLibrary; PIN = unreal.BlueprintGraphPinLibrary; BGE = unreal.BlueprintGraphEditor
here = os.path.dirname(os.path.abspath(__file__))
WP = "/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk"
KML = "/Script/Engine.KismetMathLibrary:"; KSL = "/Script/Engine.KismetStringLibrary:"; KTL = "/Script/Engine.KismetTextLibrary:"
CHARS_PER_SEC = 55.0
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))

def lc(r, g, b, a=1.0):
    return unreal.LinearColor(r, g, b, a)

def rounded_brush(fill, outline=None, width=0.0, radius=12.0):
    br = unreal.SlateBrush()
    br.set_editor_property("draw_as", unreal.SlateBrushDrawType.ROUNDED_BOX)
    br.set_editor_property("tint_color", unreal.SlateColor(fill))
    try:
        o = unreal.SlateBrushOutlineSettings()
        o.set_editor_property("corner_radii", unreal.Vector4(radius, radius, radius, radius))
        o.set_editor_property("rounding_type", unreal.SlateBrushRoundingType.FIXED_RADIUS)
        if outline is not None:
            o.set_editor_property("color", unreal.SlateColor(outline))
            o.set_editor_property("width", width)
        br.set_editor_property("outline_settings", o)
    except Exception as e:
        log("outline: %s" % e)
    return br

def style_text(tb, size, color, bold=False, just=None):
    f = tb.get_editor_property("font")
    f.set_editor_property("size", size)
    if bold:
        f.set_editor_property("typeface_font_name", "Bold")
    tb.set_editor_property("font", f)
    tb.set_editor_property("color_and_opacity", unreal.SlateColor(color))
    if just is not None:
        tb.set_editor_property("justification", just)
    try:
        tb.set_editor_property("shadow_offset", unreal.Vector2D(1.5, 1.5))
        tb.set_editor_property("shadow_color_and_opacity", lc(0, 0, 0, 0.6))
    except Exception:
        pass

def wt(name):
    return unreal.load_object(None, WP + ".W_MonsterTalk:WidgetTree." + name)

try:
    # ---------------------------------------------------------------- blip sound
    t = unreal.AssetImportTask(); t.filename = os.path.join(here, "SFX_80s_TextBlip.wav"); t.destination_path = "/Game/Office80s/Audio"
    t.destination_name = "SFX_80s_TextBlip"; t.automated = True; t.replace_existing = True; t.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])

    w = unreal.load_asset(WP)

    # ---------------------------------------------------------------- style
    AMBER = lc(0.85, 0.62, 0.18, 1.0)
    CREAM = lc(0.96, 0.93, 0.86, 1.0)
    db = wt("DialogueBorder")
    db.set_editor_property("background", rounded_brush(lc(1, 1, 1, 1), AMBER, 2.0, 14.0))
    db.set_editor_property("brush_color", lc(0.025, 0.02, 0.02, 0.9))
    nb = wt("NameBorder")
    nb.set_editor_property("background", rounded_brush(lc(1, 1, 1, 1), None, 0.0, 10.0))
    nb.set_editor_property("brush_color", AMBER)
    style_text(wt("Dialogue"), 30, CREAM)
    style_text(wt("Name"), 28, lc(0.06, 0.04, 0.03, 1.0), bold=True)

    def bubble(btn_name, txt_name, size):
        b = wt(btn_name)
        st = b.get_editor_property("widget_style")
        st.set_editor_property("normal", rounded_brush(lc(0.03, 0.025, 0.025, 0.88), lc(0.85, 0.62, 0.18, 0.55), 1.5, 18.0))
        st.set_editor_property("hovered", rounded_brush(lc(0.22, 0.14, 0.04, 0.95), AMBER, 2.5, 18.0))
        st.set_editor_property("pressed", rounded_brush(lc(0.45, 0.3, 0.08, 1.0), AMBER, 2.5, 18.0))
        st.set_editor_property("normal_padding", unreal.Margin(26, 12, 26, 12))
        st.set_editor_property("pressed_padding", unreal.Margin(26, 14, 26, 10))
        b.set_editor_property("widget_style", st)
        style_text(wt(txt_name), size, CREAM, just=unreal.TextJustify.LEFT)
    for i in (1, 2, 3):
        bubble("Option%d" % i, "OptionText%d" % i, 28)
    bubble("Back", "TextBlock_671", 24)

    # response bubbles stacked just above the dialogue box (Option3 top, Option1 bottom, same order as before)
    for btn, y in (("Option3", 448), ("Option2", 540), ("Option1", 632)):
        s = wt(btn).get_editor_property("slot")
        ld = s.get_editor_property("layout_data")
        off = ld.get_editor_property("offsets")
        off.set_editor_property("left", 332.0); off.set_editor_property("top", float(y))
        ld.set_editor_property("offsets", off)
        s.set_editor_property("layout_data", ld)
    log("style applied")

    # ---------------------------------------------------------------- typewriter (new Tick)
    have = [str(x) for x in BEL.list_member_variable_names(w, False)]
    for name, typ in (("TW_Full", "string"), ("TW_Shown", "string"), ("TW_Count", "real"), ("TW_LastN", "int")):
        if name not in have:
            BEL.add_member_variable(w, name, BEL.get_basic_type_by_name(typ))
    ed = BGE.get_graph_editor(BEL.find_event_graph(w))
    old = [n for n in ed.list_nodes_of_class(unreal.K2Node_Event) if "Tick" in str(BEL.get_node_title(n))]
    for n in old:
        if not any(len(PIN.list_connected_pins(p)) for p in BEL.list_all_pins(n)):
            ed.remove_nodes([n])
        else:
            raise RuntimeError("W_MonsterTalk already has a connected Tick; not touching it")
    def at(n, x, y):
        if n is None:
            raise RuntimeError("node failed at %d,%d" % (x, y))
        BEL.set_node_pos(n, unreal.IntPoint(int(x), int(y))); return n
    def fn(path, x, y): return at(ed.add_call_function_node(path), x, y)
    def get(v, x, y): return at(ed.add_get_member_variable_node(v, ""), x, y)
    def setv(v, x, y): return at(ed.add_set_member_variable_node(v), x, y)
    def link(a, ap, b, bp_):
        if not PIN.try_create_connection(BEL.find_output_pin(a, ap), BEL.find_input_pin(b, bp_)):
            log("ERR link %s.%s -> %s.%s" % (a.get_name(), ap, b.get_name(), bp_))
    def ex(a, b, ap="then", bp_="execute"): link(a, ap, b, bp_)
    def val(n, p, v):
        if not PIN.set_pin_value(BEL.find_input_pin(n, p), v):
            log("ERR val %s.%s=%s" % (n.get_name(), p, v))
    X, Y = 0, 3000
    tick = at(BEL.add_event_override(w, "Tick", unreal.IntPoint(X, Y)), X, Y)
    dlg = get("Dialogue", X + 150, Y + 200)
    gtx = fn("/Script/UMG.TextBlock:GetText", X + 300, Y + 200); link(dlg, "Dialogue", gtx, "self")
    cur = fn(KTL + "Conv_TextToString", X + 480, Y + 200); link(gtx, "ReturnValue", cur, "InText")
    shown = get("TW_Shown", X + 480, Y + 300)
    diff = fn(KSL + "NotEqual_StrStr", X + 650, Y + 240); link(cur, "ReturnValue", diff, "A"); link(shown, "TW_Shown", diff, "B")
    br_new = at(ed.add_branch_node(), X + 300, Y); ex(tick, br_new); link(diff, "ReturnValue", br_new, "Condition")
    s_full = setv("TW_Full", X + 520, Y - 200); link(cur, "ReturnValue", s_full, "TW_Full"); ex(br_new, s_full)
    s_cnt0 = setv("TW_Count", X + 740, Y - 200); val(s_cnt0, "TW_Count", "0.0"); ex(s_full, s_cnt0)
    s_ln0 = setv("TW_LastN", X + 960, Y - 200); val(s_ln0, "TW_LastN", "0"); ex(s_cnt0, s_ln0)
    s_sh0 = setv("TW_Shown", X + 1180, Y - 200); val(s_sh0, "TW_Shown", ""); ex(s_ln0, s_sh0)
    full = get("TW_Full", X + 900, Y + 260)
    ln = fn(KSL + "Len", X + 1050, Y + 260); link(full, "TW_Full", ln, "S")
    lnd = fn(KML + "Conv_IntToDouble", X + 1200, Y + 260); link(ln, "ReturnValue", lnd, "InInt")
    cnt = get("TW_Count", X + 1050, Y + 360)
    typing = fn(KML + "Less_DoubleDouble", X + 1350, Y + 300); link(cnt, "TW_Count", typing, "A"); link(lnd, "ReturnValue", typing, "B")
    br_t = at(ed.add_branch_node(), X + 1450, Y); ex(s_sh0, br_t); link(br_new, "else", br_t, "execute"); link(typing, "ReturnValue", br_t, "Condition")
    cnt2 = get("TW_Count", X + 1450, Y + 460)
    dtm = fn(KML + "Multiply_DoubleDouble", X + 1600, Y + 520); link(tick, "InDeltaTime", dtm, "A"); val(dtm, "B", str(CHARS_PER_SEC))
    nc = fn(KML + "Add_DoubleDouble", X + 1750, Y + 480); link(cnt2, "TW_Count", nc, "A"); link(dtm, "ReturnValue", nc, "B")
    s_cnt = setv("TW_Count", X + 1700, Y); link(nc, "ReturnValue", s_cnt, "TW_Count"); ex(br_t, s_cnt)
    cnt3 = get("TW_Count", X + 1900, Y + 300)
    n_ = fn(KML + "FTrunc", X + 2050, Y + 300); link(cnt3, "TW_Count", n_, "A")
    full2 = get("TW_Full", X + 1900, Y + 200)
    sub = fn(KSL + "GetSubstring", X + 2200, Y + 220); link(full2, "TW_Full", sub, "SourceString"); val(sub, "StartIndex", "0"); link(n_, "ReturnValue", sub, "Length")
    s_sh = setv("TW_Shown", X + 1950, Y); link(sub, "ReturnValue", s_sh, "TW_Shown"); ex(s_cnt, s_sh)
    dlg2 = get("Dialogue", X + 2200, Y + 380)
    s2t = fn(KTL + "Conv_StringToText", X + 2350, Y + 300); link(sub, "ReturnValue", s2t, "InString")
    stx = fn("/Script/UMG.TextBlock:SetText", X + 2200, Y); link(dlg2, "Dialogue", stx, "self"); link(s2t, "ReturnValue", stx, "InText"); ex(s_sh, stx)
    # blip every 3rd new letter
    ln_g = get("TW_LastN", X + 2400, Y + 500)
    moved = fn(KML + "NotEqual_IntInt", X + 2550, Y + 460); link(n_, "ReturnValue", moved, "A"); link(ln_g, "TW_LastN", moved, "B")
    md = fn(KML + "Percent_IntInt", X + 2550, Y + 560); link(n_, "ReturnValue", md, "A"); val(md, "B", "3")
    third = fn(KML + "EqualEqual_IntInt", X + 2700, Y + 560); link(md, "ReturnValue", third, "A"); val(third, "B", "0")
    bl = fn(KML + "BooleanAND", X + 2850, Y + 500); link(moved, "ReturnValue", bl, "A"); link(third, "ReturnValue", bl, "B")
    br_b = at(ed.add_branch_node(), X + 2500, Y); ex(stx, br_b); link(bl, "ReturnValue", br_b, "Condition")
    rp = fn(KML + "RandomFloatInRange", X + 2700, Y + 200); val(rp, "Min", "0.9"); val(rp, "Max", "1.15")
    blip = fn("/Script/Engine.GameplayStatics:PlaySound2D", X + 2750, Y); val(blip, "Sound", "/Game/Office80s/Audio/SFX_80s_TextBlip.SFX_80s_TextBlip")
    val(blip, "VolumeMultiplier", "0.35"); link(rp, "ReturnValue", blip, "PitchMultiplier"); ex(br_b, blip)
    s_ln = setv("TW_LastN", X + 3000, Y); link(n_, "ReturnValue", s_ln, "TW_LastN"); ex(blip, s_ln); link(br_b, "else", s_ln, "execute")
    # when done, make sure the full line is shown (covers rounding)
    s_shf = setv("TW_Shown", X + 1700, Y + 700); full3 = get("TW_Full", X + 1500, Y + 760)
    link(full3, "TW_Full", s_shf, "TW_Shown"); link(br_t, "else", s_shf, "execute")
    dlg3 = get("Dialogue", X + 1900, Y + 860)
    s2t2 = fn(KTL + "Conv_StringToText", X + 1900, Y + 760); link(full3, "TW_Full", s2t2, "InString")
    br_d = at(ed.add_branch_node(), X + 1950, Y + 700)
    gtx2 = fn("/Script/UMG.TextBlock:GetText", X + 2100, Y + 860); link(dlg3, "Dialogue", gtx2, "self")
    cur2 = fn(KTL + "Conv_TextToString", X + 2250, Y + 860); link(gtx2, "ReturnValue", cur2, "InText")
    ne2 = fn(KSL + "NotEqual_StrStr", X + 2400, Y + 800); link(cur2, "ReturnValue", ne2, "A"); link(full3, "TW_Full", ne2, "B")
    ex(s_shf, br_d); link(ne2, "ReturnValue", br_d, "Condition")
    stx2 = fn("/Script/UMG.TextBlock:SetText", X + 2250, Y + 700); link(dlg3, "Dialogue", stx2, "self"); link(s2t2, "ReturnValue", stx2, "InText"); ex(br_d, stx2)

    BEL.compile_blueprint(w)
    for n in ed.list_nodes_with_errors():
        log("COMPILE ERROR %s" % BEL.get_node_title(n))
    unreal.EditorAssetLibrary.save_loaded_asset(w)
    log("dialogue upgrade done")
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "dialogue_upgrade.log"), "w").write("\n".join(LOG))
