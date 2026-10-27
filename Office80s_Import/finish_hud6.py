import unreal
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor
bp = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
BEL.compile_blueprint(bp)
ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
errs = [str(BEL.get_node_title(n)) for n in ed.list_nodes_with_errors()]
warns = [str(BEL.get_node_title(n)) for n in ed.list_nodes_with_warnings()]
cdo = unreal.get_default_object(BEL.generated_class(bp))
done = None
for k in ("FrustPerSec", "frust_per_sec", "frustpersec"):
    try:
        cdo.set_editor_property(k, 0.55); done = k; break
    except Exception:
        pass
if done is None:
    names = [p for p in dir(cdo) if "frust" in p.lower()]
    unreal.log("[Office80s] frust props: %s" % names)
unreal.EditorAssetLibrary.save_loaded_asset(bp)
gm = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode")
unreal.log("[Office80s] hud6 finish: default via %s, errors %s, warnings %s, gm hud %s" % (done, errs, warns, unreal.get_default_object(BEL.generated_class(gm)).get_editor_property("hud_class")))
