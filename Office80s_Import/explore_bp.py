import unreal, os, json
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bp_export")
os.makedirs(out_dir, exist_ok=True)
report = []
for root in ("/Game/TaskSystem", "/Game/Dialogue", "/Game/Blueprints", "/Game/FirstPerson", "/Game/Characters", "/Game/Input", "/Game/Variant_Horror"):
    for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True):
        ad = unreal.EditorAssetLibrary.find_asset_data(p)
        cls = str(ad.asset_class_path.asset_name)
        report.append([p, cls])
        if cls in ("Blueprint", "WidgetBlueprint") and ("TaskSystem" in p or "Dialogue" in p or "Monster" in p or "Horror" in p or "Blueprints" in p):
            a = unreal.load_asset(p)
            fn = os.path.join(out_dir, p.split("/")[-1].split(".")[0] + ".t3d")
            t = unreal.AssetExportTask()
            t.object = a; t.filename = fn; t.automated = True; t.prompt = False; t.replace_identical = True
            t.exporter = unreal.ObjectExporterT3D()
            ok = unreal.Exporter.run_asset_export_task(t)
            report.append(["  export", ok, os.path.exists(fn) and os.path.getsize(fn)])
json.dump(report, open(os.path.join(out_dir, "_report.json"), "w"), indent=0)
unreal.log("[Office80s] explore done %d" % len(report))
