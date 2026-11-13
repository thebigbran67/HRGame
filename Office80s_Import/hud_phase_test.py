import unreal, sys
BEL = unreal.BlueprintEditorLibrary
p = int(sys.argv[1])
bp = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
cdo = unreal.get_default_object(BEL.generated_class(bp))
cdo.set_editor_property("Phase", p)
unreal.EditorAssetLibrary.save_loaded_asset(bp)
unreal.log("[Office80s] HUD start phase %d (frust %.4f)" % (p, cdo.get_editor_property("FrustPerSec")))
