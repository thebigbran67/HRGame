import unreal
BEL = unreal.BlueprintEditorLibrary
bp = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
cdo = unreal.get_default_object(BEL.generated_class(bp))
cdo.set_editor_property("FrustPerSec", 0.6666667)
bp.modify()
unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
unreal.log("[Office80s] frust speed now %s" % unreal.get_default_object(BEL.generated_class(bp)).get_editor_property("FrustPerSec"))
