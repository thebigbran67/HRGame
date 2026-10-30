import unreal, os
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob_probe.txt")
rows = []
state = {"h": None, "n": 0}
def tick(dt):
    try:
        worlds = unreal.EditorUtilityLibrary.get_pie_worlds(False) if hasattr(unreal.EditorUtilityLibrary, "get_pie_worlds") else []
        w = worlds[0] if worlds else unreal.EditorLevelLibrary.get_game_world()
        if not w:
            return
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        if not pawn:
            return
        cam = pawn.get_component_by_class(unreal.CameraComponent)
        c = cam.get_world_location(); p = pawn.get_actor_location(); r = pawn.get_actor_rotation()
        v = pawn.get_velocity()
        rows.append("%.2f %.2f %.2f | yaw %.1f | spd %.0f" % (c.x - p.x, c.y - p.y, c.z - p.z, r.yaw, (v.x**2 + v.y**2) ** 0.5))
        state["n"] += 1
        if state["n"] >= 240:
            unreal.unregister_slate_post_tick_callback(state["h"])
            open(path, "w").write("\n".join(rows))
    except Exception as e:
        rows.append("err %s" % e)
state["h"] = unreal.register_slate_post_tick_callback(tick)
