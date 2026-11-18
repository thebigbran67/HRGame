import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
D = "/Game/TaskSystem/TaskManager/Font"
tools = unreal.AssetToolsHelpers.get_asset_tools(); out = []
for n in ("F_TaskTypewriter", "F_TaskPrompt"):
    if not unreal.EditorAssetLibrary.does_asset_exist(D + "/" + n):
        f = tools.create_asset(n, D, unreal.Font, unreal.FontFactory())
        f.set_editor_property("font_cache_type", unreal.FontCacheType.RUNTIME)
        unreal.EditorAssetLibrary.save_loaded_asset(f)
    out.append("%s ok" % n)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([unreal.load_asset(D + "/F_TaskTypewriter")])
open(os.path.join(here, "make_fonts.txt"), "w").write("\n".join(out))
