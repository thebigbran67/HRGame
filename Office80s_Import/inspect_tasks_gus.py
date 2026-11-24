"""Read-only: task cards in order, monsters in the level, and dialogue rows/assets mentioning Gus."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
L = []
F = ["Title", "Type", "Target", "MustAccept", "Count", "DeliverTitle", "DeliverTo", "MeterMonster", "MeterSeconds", "CalmAmount",
     "TalkTo", "ItemsToPickUp", "BringItemsTo", "GoToPlace", "AngryMonster"]
try:
    tm = unreal.load_asset("/Game/_TASKS/DA_TaskManager")
    for i, t in enumerate(tm.get_editor_property("Tasks")):
        row = []
        for f in F:
            try: row.append("%s=%r" % (f, t.get_editor_property(f)))
            except Exception as e: row.append("%s=ERR" % f)
        L.append("TASK %d %s\n   %s" % (i, t.get_path_name() if t else None, "\n   ".join(row)))
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    for a in acts:
        try:
            mn = a.get_editor_property("MonsterName")
            L.append("MONSTER %s class=%s name=%s tags=%s" % (a.get_actor_label(), a.get_class().get_name(), mn, [str(x) for x in a.tags]))
        except Exception:
            pass
    for a in acts:
        if "gus" in a.get_actor_label().lower() or "gus" in a.get_class().get_name().lower():
            L.append("GUS ACTOR %s class=%s path=%s" % (a.get_actor_label(), a.get_class().get_path_name(), a.get_path_name()))
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for ad in ar.get_assets_by_path("/Game", recursive=True):
        n = str(ad.asset_name)
        if "gus" in n.lower() or "spider" in n.lower() or "fire" in n.lower() or "dialog" in n.lower():
            if not str(ad.package_name).startswith(("/Game/__External", "/Game/Environment", "/Game/Office80s/Props", "/Game/Office80s/Outdoor")):
                L.append("ASSET %s (%s)" % (ad.package_name, ad.asset_class_path.asset_name))
    dt = unreal.load_asset("/Game/Dialogue/DataSet/DT_MonsterDialogue")
    if dt:
        names = unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)
        L.append("DT rows: %s" % [str(n) for n in names])
        csv = unreal.DataTableFunctionLibrary.export_data_table_to_csv_string(dt) if hasattr(unreal.DataTableFunctionLibrary, "export_data_table_to_csv_string") else dt.export_to_csv_string() if hasattr(dt, "export_to_csv_string") else ""
        L.append("DT csv:\n" + str(csv)[:6000])
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "inspect_tasks_gus.log"), "w").write("\n".join(L))
