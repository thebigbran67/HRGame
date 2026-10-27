import unreal, os
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bp_export2")
os.makedirs(out_dir, exist_ok=True)
lines = []
for root in ("/Game/FrustrationBar", "/Game/Blueprints/States", "/Game/Elevator"):
    for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True):
        ad = unreal.EditorAssetLibrary.find_asset_data(p)
        cls = str(ad.asset_class_path.asset_name)
        lines.append("%s  %s" % (p, cls))
        if cls in ("Blueprint", "WidgetBlueprint"):
            a = unreal.load_asset(p)
            fn = os.path.join(out_dir, p.split("/")[-1].split(".")[0] + ".t3d")
            t = unreal.AssetExportTask(); t.object = a; t.filename = fn; t.automated = True; t.prompt = False; t.replace_identical = True
            t.exporter = unreal.ObjectExporterT3D()
            unreal.Exporter.run_asset_export_task(t)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in sub.get_all_level_actors():
    c = a.get_class().get_name()
    if "Monster" in c or "Frust" in c or "Quest" in c:
        loc = a.get_actor_location()
        lines.append("ACTOR %s %s (%.0f,%.0f,%.0f)" % (a.get_actor_label(), c, loc.x, loc.y, loc.z))
        for prop in ("monster_name", "Monster Name"):
            pass
open(os.path.join(out_dir, "_list.txt"), "w").write("\n".join(lines))
unreal.log("[Office80s] frust explore done")
