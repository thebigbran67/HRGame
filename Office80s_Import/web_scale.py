import unreal
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = 0
with unreal.ScopedEditorTransaction("Bigger cobwebs"):
    for a in sub.get_all_level_actors():
        if a.get_actor_label().startswith("Cobweb_"):
            a.modify(); a.set_actor_scale3d(unreal.Vector(1.9, 1.9, 1.9)); n += 1
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[Office80s] cobwebs scaled: %d" % n)
