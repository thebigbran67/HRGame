"""Moves TaskSystem/TaskManager to a top-level /Game/_TASKS hub, fixes up references, and adds ready-to-copy templates."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
EAL = unreal.EditorAssetLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools()
OLD, NEW = "/Game/TaskSystem/TaskManager", "/Game/_TASKS"
LOG = []
def log(m): LOG.append(str(m)); unreal.log("[Tasks] " + str(m))
try:
    if EAL.does_directory_exist(OLD) and not EAL.does_asset_exist(NEW + "/DA_TaskManager"):
        log("move: %s" % EAL.rename_directory(OLD, NEW))
    # point everything at the new location and remove the leftover redirectors
    reds = []
    for p in EAL.list_assets("/Game/TaskSystem", recursive=True, include_folder=False):
        ad = EAL.find_asset_data(p)
        if str(ad.asset_class_path.asset_name) == "ObjectRedirector":
            reds.append(unreal.load_asset(p))
    if reds:
        tools.fixup_referencers(reds); log("fixed %d redirectors" % len(reds))
    for p in ("/Game/TaskSystem/BP_TaskHUD", "/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode"):
        EAL.save_asset(p, only_if_is_dirty=False)
    hud = unreal.get_default_object(unreal.BlueprintEditorLibrary.generated_class(unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")))
    log("HUD task list now: %s" % hud.get_editor_property("TaskList"))

    # templates: copy one into Tasks/, rename it, change the words, drag it into DA_TaskManager
    task_cls = unreal.BlueprintEditorLibrary.generated_class(unreal.load_asset(NEW + "/BPD_Task"))
    T = [
        ("TEMPLATE_1_TalkToSomeone", {"Title": "Talk to the receptionist", "Type": "Talk", "Target": "Receptionist"}),
        ("TEMPLATE_2_TalkAndSayYes", {"Title": "Ask the floor manager for work", "Type": "Talk", "Target": "Floor Manager", "MustAccept": True}),
        ("TEMPLATE_3_PickUpItems", {"Title": "Find 3 lost staplers", "Type": "Collect", "Target": "Task_Stapler", "Count": 3,
                                    "MeterMonster": "", "MeterSeconds": 150.0, "CalmAmount": 0.0}),
        ("TEMPLATE_4_PickUpAndBringBack", {"Title": "Grab the boss a coffee", "Type": "Collect", "Target": "Task_Coffee", "Count": 1,
                                    "DeliverTitle": "Bring the coffee to the boss", "DeliverTo": "Task_Boss", "DeliverPrompt": "to hand over the coffee",
                                    "MeterMonster": "Boss", "MeterSeconds": 120.0, "CalmAmount": 40.0}),
        ("TEMPLATE_5_GoSomewhere", {"Title": "Check on the break room", "Type": "GoTo", "Target": "Task_BreakRoom"}),
    ]
    for name, vals in T:
        p = NEW + "/Templates/" + name
        if EAL.does_asset_exist(p):
            log("kept " + name); continue
        f = unreal.DataAssetFactory(); f.set_editor_property("data_asset_class", task_cls)
        da = tools.create_asset(name, NEW + "/Templates", None, f)
        for k, v in vals.items():
            da.set_editor_property(k, v)
        EAL.save_loaded_asset(da); log("template " + name)
    content = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
    d = os.path.join(content, "_TASKS"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "README_HowToAddTasks.txt"), "w").write(open(os.path.join(here, "README_HowToAddTasks.txt")).read())
    old_readme = os.path.join(content, "TaskSystem", "TaskManager", "README_TaskManager.txt")
    if os.path.exists(old_readme):
        os.remove(old_readme)
    for p in sorted(EAL.list_assets(NEW, recursive=True)):
        log("  " + p)
    log("hub done")
except Exception:
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "make_tasks_hub.log"), "w").write("\n".join(LOG))
