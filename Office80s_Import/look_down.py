import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
L = []
try:
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    pawn = unreal.GameplayStatics.get_player_pawn(gw, 0)
    L.append("pawn at %s rot %s" % (pawn.get_actor_location(), pc.get_control_rotation()))
    t = unreal.Vector(4410, -900, 21)
    cam = unreal.GameplayStatics.get_player_camera_manager(gw, 0).get_camera_location()
    r = unreal.MathLibrary.find_look_at_rotation(cam, t)
    pc.set_control_rotation(r)
    L.append("look at rot %s cam %s" % (r, cam))
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "look_down.log"), "w").write("\n".join(L))
