import unreal, os
out = []
BEL = unreal.BlueprintEditorLibrary
gm = unreal.get_default_object(BEL.generated_class(unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode")))
pawn_cls = gm.get_editor_property("default_pawn_class")
out.append("pawn class: %s" % pawn_cls)
jump = unreal.load_asset("/Game/Input/Actions/IA_Jump")
for p in unreal.EditorAssetLibrary.list_assets("/Game", recursive=True):
    ad = unreal.EditorAssetLibrary.find_asset_data(p)
    if str(ad.asset_class_path.asset_name) == "InputMappingContext":
        imc = unreal.load_asset(p)
        try:
            maps = imc.get_editor_property("mappings")
            before = len(maps)
        except Exception:
            before = -1
        imc.unmap_all_keys_from_action(jump)
        try:
            after = len(imc.get_editor_property("mappings"))
        except Exception:
            after = -1
        if before != after:
            unreal.EditorAssetLibrary.save_loaded_asset(imc)
        out.append("%s: %d -> %d" % (p, before, after))
for bp_path in ("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter", "/Game/Variant_Horror/Blueprints/BP_HorrorCharacter"):
    bp = unreal.load_asset(bp_path)
    cdo = unreal.get_default_object(BEL.generated_class(bp))
    cdo.set_editor_property("jump_max_count", 0)
    bp.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
    out.append("%s jump_max_count=%s" % (bp_path, cdo.get_editor_property("jump_max_count")))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "no_jump.log"), "w").write("\n".join(out))
