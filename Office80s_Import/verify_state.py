import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary
out = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if isinstance(a, unreal.PlayerStart):
        out.append("PlayerStart %s yaw %.1f" % (a.get_actor_location(), a.get_actor_rotation().yaw))
cdo = unreal.get_default_object(BEL.generated_class(unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")))
out.append("HUD Phase %d FrustPerSec %.4f Stamina %.2f" % (cdo.get_editor_property("Phase"), cdo.get_editor_property("FrustPerSec"), cdo.get_editor_property("Stamina")))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
out.append("saved")
open(os.path.join(here, "verify_state.log"), "w").write("\n".join(out))
