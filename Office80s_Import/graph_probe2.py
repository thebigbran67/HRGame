import unreal, os
BEL = unreal.BlueprintEditorLibrary; PIN = unreal.BlueprintGraphPinLibrary; BGE = unreal.BlueprintGraphEditor
out = []
bp = unreal.load_asset("/Game/Office80s/Temp/BP_Probe")
ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
avail = ed.list_available_nodes([])
out += ["T " + a for a in avail if a.endswith("|Tab") or "Keyboard" in a and "Tab" in a][:20]
out += ["S " + a for a in avail if a in ("Utilities|FlowControl|Sequence", "Utilities|FlowControl|Branch") or "|DrawText" in a or "|DrawRect" in a or "|GetTextSize" in a or a.endswith("|EventDrawHUD") or a.endswith("|ForEachLoop")][:40]
def pins(n, tag):
    for p in BEL.list_all_pins(n):
        out.append("  %s pin %s %s %s" % (tag, PIN.get_pin_name(p), "out" if PIN.get_pin_direction(p) == unreal.EdGraphPinDirection.EGPD_OUTPUT else "in", PIN.get_pin_type_display_string(p)))
for nm in ("Utilities|FlowControl|Sequence", "Utilities|FlowControl|ForEachLoop", "Utilities|FlowControl|Branch"):
    try:
        n = ed.create_node_from_name(nm, unreal.Vector2D(0, 0), [])
        out.append("node %s -> %s" % (nm, n)); pins(n, nm)
    except Exception as e:
        out.append("ERR %s %s" % (nm, e))
ev = BEL.add_event_override(bp, "ReceiveDrawHUD", unreal.Vector2D(0, 0))
out.append("drawhud %s" % ev); pins(ev, "draw")
for f in ("/Script/Engine.HUD:DrawText", "/Script/Engine.HUD:GetTextSize", "/Script/Engine.HUD:DrawRect", "/Script/Engine.KismetMathLibrary:SelectString", "/Script/Engine.KismetMathLibrary:SelectColor", "/Script/Engine.KismetStringLibrary:Concat_StrStr"):
    n = ed.add_call_function_node(f); out.append("fn %s -> %s" % (f, n))
    if n: pins(n, f.split(":")[-1])
gm = unreal.EditorLevelLibrary.get_editor_world().get_world_settings().get_editor_property("default_game_mode")
out.append("world gm: %s" % gm)
try:
    out.append("project gm: %s" % unreal.get_default_object(unreal.GameMapsSettings).get_editor_property("global_default_game_mode"))
except Exception as e:
    out.append("gms err %s" % e)
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_probe2.txt")
open(p, "w", encoding="utf-8").write("\n".join(str(x) for x in out))
unreal.log("[Office80s] graph probe2 done")
