import unreal
bp = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([bp])
