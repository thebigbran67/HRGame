import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.join(here, "bp_export5"); os.makedirs(out_dir, exist_ok=True)
for p in ("/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk", "/Game/Blueprints/Dialogue/Blueprints/BP_DialogueMaster",
          "/Game/Dialogue/Blueprints/BP_DialogueMaster", "/Game/Dialogue/DataSet/DT_MonsterDialogue"):
    a = unreal.load_asset(p)
    if not a: continue
    name = p.strip("/").replace("/", "_") + ".t3d"
    t = unreal.AssetExportTask(); t.object = a; t.filename = os.path.join(out_dir, name); t.automated = True; t.prompt = False; t.replace_identical = True
    t.exporter = unreal.ObjectExporterT3D(); unreal.Exporter.run_asset_export_task(t)
dt = unreal.load_asset("/Game/Dialogue/DataSet/DT_MonsterDialogue")
open(os.path.join(out_dir, "DT_MonsterDialogue.csv"), "w", encoding="utf-8").write(unreal.DataTableFunctionLibrary.export_data_table_to_csv_string(dt))
unreal.log("[Office80s] export5 done")
