import unreal
want = "JMUOZ2T50AHPEUO2B250UZ"
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    p = a.get_outermost().get_name()
    if want in p:
        unreal.log("[Office80s] unsaved package %s = %s (%s) folder=%s" % (p, a.get_actor_label(), a.get_class().get_name(), a.get_folder_path()))
        ok = unreal.EditorLoadingAndSavingUtils.save_packages([a.get_outermost()], False)
        unreal.log("[Office80s] retry save -> %s" % ok)
