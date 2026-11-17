"""Read-only: exports the main menu widget, the menu/controls/office level blueprints and world settings as text."""
import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "menu_export"); os.makedirs(out, exist_ok=True)
info = []
def exp(obj, name):
    t = unreal.AssetExportTask(); t.object = obj; t.filename = os.path.join(out, name); t.automated = True; t.prompt = False; t.replace_identical = True
    t.exporter = unreal.ObjectExporterT3D(); unreal.Exporter.run_asset_export_task(t)
for p in unreal.EditorAssetLibrary.list_assets("/Game/Maps", recursive=True):
    a = unreal.load_asset(p.split(".")[0])
    info.append("%s %s" % (p, a.get_class().get_name() if a else None))
    if isinstance(a, (unreal.WidgetBlueprint, unreal.Blueprint)):
        exp(a, a.get_name() + ".t3d")
for m in ("/Game/Maps/MainMenu", "/Game/Maps/Controls", "/Game/Maps/Office"):
    w = unreal.load_asset(m)
    if not w: continue
    lvl = w.get_editor_property("persistent_level")
    try:
        lsb = unreal.BlueprintEditorLibrary.get_level_script_blueprint(lvl) if hasattr(unreal.BlueprintEditorLibrary, "get_level_script_blueprint") else None
    except Exception as e:
        lsb = None; info.append("lsb err %s" % e)
    if lsb is None:
        try:
            lsb = lvl.get_level_script_blueprint()
        except Exception as e:
            info.append("lsb2 err %s" % e)
    if lsb: exp(lsb, "LevelBP_" + m.split("/")[-1] + ".t3d")
    try:
        ws = w.get_world_settings()
        info.append("%s gamemode override: %s" % (m, ws.get_editor_property("default_game_mode")))
    except Exception as e:
        info.append("%s ws err %s" % (m, e))
for p in ("/Game/FirstPerson/Blueprints/BP_FirstPersonPlayerController", "/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode"):
    exp(unreal.load_asset(p), p.split("/")[-1] + ".t3d")
s = unreal.get_default_object(unreal.GameMapsSettings)
for k in ("editor_startup_map", "game_default_map", "global_default_game_mode"):
    try: info.append("%s = %s" % (k, s.get_editor_property(k)))
    except Exception as e: info.append("%s err %s" % (k, e))
open(os.path.join(out, "_info.txt"), "w").write("\n".join(info))
