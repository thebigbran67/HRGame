import unreal
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    l = a.get_actor_label()
    if l.startswith("RoomDoor_") or l.startswith("DoorInfill_") or a.get_class().get_name() == "BP_CubeDoor_C":
        p = a.get_actor_location(); o, e = a.get_actor_bounds(False)
        unreal.log("[Office80s] %s at (%.0f, %.0f) yaw %.0f bounds x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f" % (l, p.x, p.y, a.get_actor_rotation().yaw, o.x-e.x, o.x+e.x, o.y-e.y, o.y+e.y, o.z-e.z, o.z+e.z))
