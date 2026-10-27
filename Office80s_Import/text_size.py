import unreal
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
with unreal.ScopedEditorTransaction("Bigger wall message"):
    for a in sub.get_all_level_actors():
        if a.get_actor_label() == "WallMessage":
            a.modify(); c = a.get_component_by_class(unreal.TextRenderComponent); c.modify(); c.set_world_size(80.0)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[Office80s] text resized")
