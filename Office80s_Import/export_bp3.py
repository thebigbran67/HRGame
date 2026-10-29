import unreal, os
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bp_export3")
os.makedirs(out_dir, exist_ok=True)
for p in ("/Game/Blueprints/Dialogue/Blueprints/BP_Monster", "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter", "/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk"):
    a = unreal.load_asset(p)
    t = unreal.AssetExportTask(); t.object = a; t.filename = os.path.join(out_dir, p.split("/")[-1] + ".t3d"); t.automated = True; t.prompt = False; t.replace_identical = True
    t.exporter = unreal.ObjectExporterT3D(); unreal.Exporter.run_asset_export_task(t)
for p in unreal.EditorAssetLibrary.list_assets("/Game/Interaction", recursive=True):
    a = unreal.load_asset(p)
    ad = unreal.EditorAssetLibrary.find_asset_data(p)
    open(os.path.join(out_dir, "_interaction.txt"), "a").write("%s %s\n" % (p, ad.asset_class_path.asset_name))
    if str(ad.asset_class_path.asset_name) in ("Blueprint", "WidgetBlueprint"):
        t = unreal.AssetExportTask(); t.object = a; t.filename = os.path.join(out_dir, p.split("/")[-1].split(".")[0] + ".t3d"); t.automated = True; t.prompt = False; t.replace_identical = True
        t.exporter = unreal.ObjectExporterT3D(); unreal.Exporter.run_asset_export_task(t)
unreal.log("[Office80s] export3 done")
