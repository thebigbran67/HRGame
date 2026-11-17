"""Read-only: exports the MainMenu / Controls / Office level blueprints + game mode info as text."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "menu_export"); os.makedirs(out, exist_ok=True)
info = []
def w():
    open(os.path.join(out, "_info2.txt"), "w").write("\n".join(info))
def exp(obj, name):
    t = unreal.AssetExportTask(); t.object = obj; t.filename = os.path.join(out, name); t.automated = True; t.prompt = False; t.replace_identical = True
    t.exporter = unreal.ObjectExporterT3D(); unreal.Exporter.run_asset_export_task(t)
for m in ("MainMenu", "Controls", "Office"):
    try:
        path = "/Game/Maps/%s.%s:PersistentLevel" % (m, m)
        lvl = unreal.load_object(None, path)
        info.append("%s level: %s" % (m, lvl))
        lsb = None
        for nm in ("/Game/Maps/%s.%s:PersistentLevel.%s" % (m, m, m),):
            try:
                lsb = unreal.load_object(None, nm); info.append("  lsb via path: %s" % lsb)
            except Exception as e:
                info.append("  path err %s" % e)
        if lsb:
            exp(lsb, "LevelBP_%s.t3d" % m)
        wobj = unreal.load_object(None, "/Game/Maps/%s.%s" % (m, m))
        try:
            ws = unreal.load_object(None, "/Game/Maps/%s.%s:PersistentLevel.WorldSettings" % (m, m))
            info.append("  gamemode override: %s" % ws.get_editor_property("default_game_mode"))
        except Exception as e:
            info.append("  ws err %s" % e)
    except Exception:
        info.append("ERR %s %s" % (m, traceback.format_exc()))
    w()
try:
    s = unreal.get_default_object(unreal.GameMapsSettings)
    for k in ("editor_startup_map", "game_default_map", "global_default_game_mode"):
        try: info.append("%s = %s" % (k, s.get_editor_property(k)))
        except Exception as e: info.append("%s err %s" % (k, e))
    for p in ("/Game/FirstPerson/Blueprints/BP_FirstPersonPlayerController", "/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode"):
        exp(unreal.load_asset(p), p.split("/")[-1] + ".t3d")
except Exception:
    info.append(traceback.format_exc())
w()
