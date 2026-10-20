import unreal, sys
# usage: py cam.py x y z pitch yaw
a = [float(v) for v in sys.argv[1:6]]
unreal.get_editor_subsystem(unreal.EditorActorSubsystem).select_nothing()
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(a[0], a[1], a[2]), unreal.Rotator(0, a[3], a[4]))
