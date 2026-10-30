import unreal, os
ar = unreal.AssetRegistryHelpers.get_asset_registry()
out = []
odir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bp_export4"); os.makedirs(odir, exist_ok=True)
for ad in ar.get_assets_by_path("/Game", recursive=True):
    if "tempover" in str(ad.asset_name).lower():
        out.append("%s %s" % (ad.package_name, ad.asset_class_path.asset_name))
        a = unreal.load_asset(str(ad.package_name))
        t = unreal.AssetExportTask(); t.object = a; t.filename = os.path.join(odir, str(ad.asset_name) + ".t3d"); t.automated = True; t.prompt = False; t.replace_identical = True
        t.exporter = unreal.ObjectExporterT3D(); unreal.Exporter.run_asset_export_task(t)
open(os.path.join(odir, "_found.txt"), "w").write("\n".join(out) or "none")
