"""Read-only: exports the current monster/dialogue/interaction blueprints as text, and dumps the boss's per-instance settings."""
import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(here, "bp_export4"); os.makedirs(out_dir, exist_ok=True)
paths = ["/Game/Blueprints/Dialogue/Blueprints/BP_Monster", "/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk",
         "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter", "/Game/TaskSystem/BP_QuestManager"]
listing = []
for root in ("/Game/Blueprints", "/Game/Dialogue", "/Game/Interaction", "/Game/TaskSystem"):
    for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True):
        ad = unreal.EditorAssetLibrary.find_asset_data(p)
        cls = str(ad.asset_class_path.asset_name)
        listing.append("%s %s" % (p, cls))
        if cls in ("Blueprint", "WidgetBlueprint") and p.split(".")[0] not in paths:
            paths.append(p.split(".")[0])
open(os.path.join(out_dir, "_listing.txt"), "w").write("\n".join(listing))
for p in paths:
    a = unreal.load_asset(p)
    if not a: continue
    t = unreal.AssetExportTask(); t.object = a; t.filename = os.path.join(out_dir, p.split("/")[-1] + ".t3d"); t.automated = True; t.prompt = False; t.replace_identical = True
    t.exporter = unreal.ObjectExporterT3D(); unreal.Exporter.run_asset_export_task(t)
lines = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label() in ("BP_Monster2", "BP_Monster"):
        t = unreal.AssetExportTask(); t.object = a; t.filename = os.path.join(out_dir, "actor_" + a.get_actor_label() + ".t3d"); t.automated = True; t.prompt = False
        t.exporter = unreal.ObjectExporterT3D(); unreal.Exporter.run_asset_export_task(t)
        lines.append("%s class=%s" % (a.get_actor_label(), a.get_class().get_path_name()))
open(os.path.join(out_dir, "_actors.txt"), "w").write("\n".join(lines))
unreal.log("[Office80s] export4 done")
