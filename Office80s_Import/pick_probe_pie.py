"""Run while Playing: does the picked actor resolve to the Play copy?"""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
LOG = []
try:
    da = unreal.load_asset("/Game/Office80s/Temp/DA_PickProbe")
    v = da.get_editor_property("Pick"); LOG.append("raw %r" % (v,))
    for fn in ("conv_soft_object_reference_to_object", "load_asset_blocking"):
        try:
            o = getattr(unreal.SystemLibrary, fn)(v); LOG.append("%s -> %s" % (fn, o.get_path_name() if o else None))
        except Exception as e:
            LOG.append("%s failed %s" % (fn, e))
    try:
        s = unreal.SystemLibrary.conv_soft_object_reference_to_string(v); LOG.append("as string " + str(s))
    except Exception as e:
        LOG.append("to string failed %s" % e)
    ws = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    gw = ws.get_game_world(); LOG.append("game world %s" % (gw.get_path_name() if gw else None))
    if gw:
        bags = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.load_class(None, "/Game/TaskSystem/Tasks/TrashTask/BP_TrashBag.BP_TrashBag_C"))
        LOG.append("pie bags: %s" % [b.get_path_name() for b in bags[:3]])
except Exception:
    LOG.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "pick_probe_pie.log"), "w").write("\n".join(LOG))
