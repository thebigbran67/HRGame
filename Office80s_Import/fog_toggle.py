import unreal, sys
hide = sys.argv[1] == "hide"
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label().startswith("YardFog_"):
        a.set_is_temporarily_hidden_in_editor(hide)
unreal.log("[Office80s] fog %s" % ("hidden" if hide else "shown"))
