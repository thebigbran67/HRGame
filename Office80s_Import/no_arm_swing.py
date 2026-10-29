import unreal, os
BEL = unreal.BlueprintEditorLibrary
out = []
bp = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")
idle = unreal.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    o = lib.get_object(lib.get_data(h))
    if isinstance(o, unreal.SkeletalMeshComponent) and "FirstPersonMesh" in o.get_name():
        o.modify()
        o.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        d = o.get_editor_property("animation_data")
        d.set_editor_property("anim_to_play", idle)
        d.set_editor_property("saved_looping", True)
        d.set_editor_property("saved_playing", True)
        o.set_editor_property("animation_data", d)
        out.append("first person arms now play %s (was ABP_FP_Copy)" % idle.get_name())
BEL.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "no_arm_swing.log"), "w").write("\n".join(out) or "no first person mesh found")
