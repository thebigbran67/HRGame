import unreal, sys
x, y, z, yaw, pitch = [float(v) for v in sys.argv[1:6]]
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
p = pc.get_controlled_pawn()
p.set_actor_location(unreal.Vector(x, y, z), False, True)
pc.set_control_rotation(unreal.Rotator(0, pitch, yaw))
