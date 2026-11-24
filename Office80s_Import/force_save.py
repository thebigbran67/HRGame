import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
L = []
w = unreal.load_asset("/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk")
wed = BGE.get_graph_editor(BEL.find_event_graph(w))
for n in wed.list_all_nodes():
    t = str(BEL.get_node_title(n))
    if t.startswith("SelectString"):
        L.append("select A=%s B=%s" % (PIN.get_pin_value(BEL.find_input_pin(n, "A")), PIN.get_pin_value(BEL.find_input_pin(n, "B"))))
    p = BEL.find_input_pin(n, "InText")
    if p and "FIRED" in str(PIN.get_pin_value(p)): L.append("gus line: %s" % PIN.get_pin_value(p))
hud = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
hed = BGE.get_graph_editor(BEL.find_event_graph(hud))
for n in hed.list_all_nodes():
    if str(BEL.get_node_title(n)).startswith("MakeTransform"):
        sp = BEL.find_input_pin(n, "Scale")
        if sp and "1.0" in str(PIN.get_pin_value(sp)).replace("1.000000", "1.0"):
            L.append("spider spot %s scale %s" % (PIN.get_pin_value(BEL.find_input_pin(n, "Location")), PIN.get_pin_value(sp)))
L.append("saved widget: %s" % unreal.EditorAssetLibrary.save_loaded_asset(w, False))
L.append("saved hud: %s" % unreal.EditorAssetLibrary.save_loaded_asset(hud, False))
open(os.path.join(here, "force_save.log"), "w").write("\n".join(L))
