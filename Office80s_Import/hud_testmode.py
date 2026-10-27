import unreal, sys
BEL = unreal.BlueprintEditorLibrary
on = unreal.Paths.file_exists(unreal.Paths.combine([unreal.Paths.project_dir(), "Office80s_Import", "TESTMODE"]))
bp = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
cdo = unreal.get_default_object(BEL.generated_class(bp))
cdo.set_editor_property("Phase", 1 if on else 0)
cdo.set_editor_property("FrustPerSec", 12.0 if on else 0.55)
unreal.EditorAssetLibrary.save_loaded_asset(bp)
unreal.log("[Office80s] test mode %s" % on)
