"""Put the 5 quest-spider spawn spots in BP_TaskHUD back to their original places and size (0.65)."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
BACK = {"(X=2470,Y=-4767,Z=22)": "(X=2100,Y=-4920,Z=22)", "(X=3252,Y=-3712,Z=21)": "(X=3030,Y=-3620,Z=21)",
        "(X=3630,Y=-2470,Z=21)": "(X=4030,Y=-2470,Z=21)", "(X=4563,Y=-530,Z=21)": "(X=4410,Y=-900,Z=21)",
        "(X=5427,Y=-2003,Z=21)": "(X=5710,Y=-1720,Z=21)"}
L = []
try:
    hud = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
    hud.modify()
    ed = BGE.get_graph_editor(BEL.find_event_graph(hud))
    done = 0
    for n in ed.list_all_nodes():
        if not str(BEL.get_node_title(n)).startswith("MakeTransform"): continue
        lp = BEL.find_input_pin(n, "Location"); sp = BEL.find_input_pin(n, "Scale")
        if not lp or not sp: continue
        v = str(PIN.get_pin_value(lp)).replace(".000000", "")
        if v in BACK:
            PIN.set_pin_value(lp, BACK[v]); PIN.set_pin_value(sp, "(X=0.65,Y=0.65,Z=0.65)"); done += 1
            L.append("%s -> %s scale %s" % (v, PIN.get_pin_value(lp), PIN.get_pin_value(sp)))
    L.append("restored %d of 5" % done)
    if done != 5: raise RuntimeError("did not find all 5, not saving")
    BEL.compile_blueprint(hud)
    L.append("compile errors: %d" % len(list(ed.list_nodes_with_errors())))
    L.append("saved: %s" % unreal.EditorAssetLibrary.save_loaded_asset(hud, False))
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "spiders_back.log"), "w").write("\n".join(L))
