import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
L = []
try:
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    pawn = unreal.GameplayStatics.get_player_pawn(gw, 0)
    t = unreal.Vector(3030, -3620, 21)
    best = None
    for dx, dy in ((170, 0), (-170, 0), (0, 170), (0, -170), (120, 120), (-120, -120), (120, -120), (-120, 120)):
        s = unreal.Vector(t.x + dx, t.y + dy, 140)
        h = unreal.SystemLibrary.line_trace_single(gw, s, unreal.Vector(t.x, t.y, t.z + 8), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [pawn], unreal.DrawDebugTrace.NONE, True)
        hit = h.to_tuple() if h else None
        actor = hit[9] if hit else None
        L.append("from %s,%s hit %s" % (dx, dy, actor.get_class().get_name() if actor else None))
        if actor and "QuestSpider" in actor.get_class().get_name() and best is None: best = s
    if best:
        pawn.set_actor_location(unreal.Vector(best.x, best.y, 118), False, True)
        cam = unreal.GameplayStatics.get_player_camera_manager(gw, 0).get_camera_location()
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(cam, unreal.Vector(t.x, t.y, t.z + 8)))
        L.append("standing at %s" % best)
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "look_spider2.log"), "w").write("\n".join(L))
