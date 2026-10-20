"""Marks the painted walls / tiled ceiling as modified so their material overrides are written to disk,
then saves them. Run with the Office map open."""
import unreal

WANT = ("M_80s_WallTwoTone", "M_80s_CeilingTile")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
fixed = []
with unreal.ScopedEditorTransaction("Save 80s wall materials"):
    for a in sub.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        c = a.static_mesh_component
        mats = c.get_materials()
        hit = [m for m in mats if m and m.get_name() in WANT]
        if not hit:
            continue
        a.modify()
        c.modify()
        for i, m in enumerate(mats):
            if m and m.get_name() in WANT:
                c.set_material(i, None)
                c.set_material(i, m)
        c.set_editor_property("override_materials", [m for m in mats])
        fixed.append(a)

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
pk = [a.get_outermost().get_name() for a in fixed]
unreal.log("[Office80s] re-saved %d wall/ceiling actors: %s" % (len(fixed), ", ".join(pk[:5]) + (" ..." if len(pk) > 5 else "")))
