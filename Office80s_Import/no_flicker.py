import unreal
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = []
with unreal.ScopedEditorTransaction("Remove flickering lights"):
    for a in sub.get_all_level_actors():
        for c in a.get_components_by_class(unreal.LightComponent):
            m = c.get_editor_property("light_function_material")
            if m and "LightFlicker" in m.get_name():
                a.modify(); c.modify()
                c.set_editor_property("light_function_material", None)
                n.append(a.get_actor_label())
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
unreal.log("[Office80s] flicker removed from %s; still unsaved: %d" % (n, len(left)))
