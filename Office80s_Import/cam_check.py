import unreal, os
BEL = unreal.BlueprintEditorLibrary
bp = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")
cdo = unreal.get_default_object(BEL.generated_class(bp))
out = []
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    d = lib.get_data(h); o = lib.get_associated_object(d)
    if isinstance(o, unreal.CameraComponent):
        out.append("camera %s rel=%s rot=%s socket=%s pawnrot=%s" % (o.get_name(), o.get_editor_property("relative_location"), o.get_editor_property("relative_rotation"), lib.get_socket_name(d) if hasattr(lib, "get_socket_name") else "?", o.get_editor_property("use_pawn_control_rotation")))
    if isinstance(o, unreal.SkeletalMeshComponent):
        out.append("mesh %s rel=%s rot=%s" % (o.get_name(), o.get_editor_property("relative_location"), o.get_editor_property("relative_rotation")))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cam_check.txt"), "w").write("\n".join(out))
