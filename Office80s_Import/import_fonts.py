"""Imports Poppins Bold as a font face next to the typewriter face (FreeMonoBold) in TaskManager/Font; lists what's there."""
import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
D = "/Game/TaskSystem/TaskManager/Font"
out = []
if not unreal.EditorAssetLibrary.does_asset_exist(D + "/Poppins-Bold"):
    t = unreal.AssetImportTask(); t.filename = os.path.join(here, "ui", "Poppins-Bold.ttf"); t.destination_path = D
    t.automated = True; t.replace_existing = True; t.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
for p in unreal.EditorAssetLibrary.list_assets(D, recursive=True):
    a = unreal.load_asset(p); out.append("%s %s" % (p, a.get_class().get_name()))
open(os.path.join(here, "import_fonts.txt"), "w").write("\n".join(out))
