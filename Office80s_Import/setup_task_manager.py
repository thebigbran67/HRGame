"""Creates the task manager in /Game/TaskSystem/TaskManager:
  BPD_Task          - the "task card" class (Title, Type, Target, ...)
  BPD_TaskList      - holds the ordered Tasks list
  DA_TaskManager    - THE list the game runs, in order
  Tasks/DA_Task_*   - the three starting cards (boss, janitor, trash)
  BP_TaskPickup     - drop-in pickup item for Collect tasks (tag it)
  BP_TaskZone       - drop-in box for GoTo tasks (tag it)
  Font/F_Typewriter - typewriter font for task titles
Also tags BP_TrashBag (Task_Trash) and BP_TrashDropOff (Task_Dumpster) in their class defaults.
Re-runnable: existing task cards and the list are left as they are (your edits are kept)."""
import os, unreal
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
TM = "/Game/TaskSystem/TaskManager"
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[TaskManager] " + str(m))

FIELDS = [  # name, type, default, tooltip
    ("Title", "string", "", "Text on the task memo"),
    ("Type", "string", "Talk", "Talk, Collect or GoTo"),
    ("Target", "string", "", "Talk: monster name (Boss, Janitor...). Collect: tag on the items. GoTo: tag on the zone/actor"),
    ("MustAccept", "bool", False, "Talk only: finishes after you pick the option that gives you work (like Sure)"),
    ("Count", "int", 0, "Collect: how many to grab (0 = every tagged item)"),
    ("DeliverTitle", "string", "", "Collect: memo text once you have everything (leave empty = done when collected)"),
    ("DeliverTo", "string", "", "Collect: tag on the turn-in spot (press E there)"),
    ("DeliverPrompt", "string", "to turn it in", "Collect: words after 'Press E' at the turn-in spot"),
    ("MeterMonster", "string", "", "Name of the monster whose frustration bar runs during this task (empty = none)"),
    ("MeterSeconds", "real", 150.0, "Seconds until that bar fills up and you die"),
    ("CalmAmount", "real", 50.0, "How much the bar drops when the task is done"),
]

def bp_asset(name, parent):
    p = TM + "/" + name
    if EAL.does_asset_exist(p):
        return unreal.load_asset(p), False
    return BEL.create_blueprint_asset_with_parent(p, parent), True

def ensure_var(bp, name, t):
    have = [str(x) for x in BEL.list_member_variable_names(bp)]
    if name not in have:
        BEL.add_member_variable(bp, name, t)
    BEL.set_blueprint_variable_instance_editable(bp, name, True)
    BEL.set_blueprint_variable_category(bp, name, "Task")

def make_card(task_cls, name, values):
    p = TM + "/Tasks/" + name
    if EAL.does_asset_exist(p):
        log("kept existing card " + name); return unreal.load_asset(p)
    f = unreal.DataAssetFactory(); f.set_editor_property("data_asset_class", task_cls)
    da = tools.create_asset(name, TM + "/Tasks", None, f)
    for k, v in values.items():
        da.set_editor_property(k, v)
    EAL.save_loaded_asset(da); log("card " + name)
    return da

def subobj(bp, cls, name, parent_handle=None):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        o = lib.get_associated_object(lib.get_data(h))
        if o and o.get_name().startswith(name):
            return o
    ph = parent_handle if parent_handle is not None else handles[0]
    nh, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=ph, new_class=cls, blueprint_context=bp))
    sds.rename_subobject(nh, unreal.Text(name))
    return lib.get_associated_object(lib.get_data(nh))

def main():
    # ------------------------------------------------ task card class + list class
    task_bp, _ = bp_asset("BPD_Task", unreal.PrimaryDataAsset)
    for n, t, d, tip in FIELDS:
        ensure_var(task_bp, n, BEL.get_basic_type_by_name(t))
    BEL.compile_blueprint(task_bp)
    cdo = unreal.get_default_object(BEL.generated_class(task_bp))
    for n, t, d, tip in FIELDS:
        cdo.set_editor_property(n, d)
    EAL.save_loaded_asset(task_bp)
    task_cls = BEL.generated_class(task_bp)
    list_bp, _ = bp_asset("BPD_TaskList", unreal.PrimaryDataAsset)
    ensure_var(list_bp, "Tasks", BEL.get_array_type(BEL.get_object_reference_type(task_cls)))
    BEL.compile_blueprint(list_bp); EAL.save_loaded_asset(list_bp)
    list_cls = BEL.generated_class(list_bp)
    log("classes ready")

    # ------------------------------------------------ the three starting tasks + the list
    c1 = make_card(task_cls, "DA_Task_01_TalkToBoss", {"Title": "Talk to the boss", "Type": "Talk", "Target": "Boss"})
    c2 = make_card(task_cls, "DA_Task_02_TalkToJanitor", {"Title": "Talk to the janitor", "Type": "Talk", "Target": "Janitor", "MustAccept": True})
    c3 = make_card(task_cls, "DA_Task_03_TakeOutTrash", {"Title": "Take out the trash", "Type": "Collect", "Target": "Task_Trash", "Count": 0,
                    "DeliverTitle": "Bring the trash to the dumpster", "DeliverTo": "Task_Dumpster", "DeliverPrompt": "to take out trash",
                    "MeterMonster": "Janitor", "MeterSeconds": 150.0, "CalmAmount": 50.0})
    lp = TM + "/DA_TaskManager"
    if EAL.does_asset_exist(lp):
        tl = unreal.load_asset(lp); log("kept existing DA_TaskManager (%d tasks)" % len(tl.get_editor_property("Tasks")))
    else:
        f = unreal.DataAssetFactory(); f.set_editor_property("data_asset_class", list_cls)
        tl = tools.create_asset("DA_TaskManager", TM, None, f)
        tl.set_editor_property("Tasks", [c1, c2, c3]); EAL.save_loaded_asset(tl); log("DA_TaskManager with 3 tasks")

    # ------------------------------------------------ typewriter font
    fp = TM + "/Font/F_Typewriter"
    if not EAL.does_asset_exist(fp):
        t = unreal.AssetImportTask(); t.filename = os.path.join(here, "ui", "FreeMonoBold.ttf"); t.destination_path = TM + "/Font"
        t.automated = True; t.replace_existing = True; t.save = True
        tools.import_asset_tasks([t])
        face = unreal.load_asset(TM + "/Font/FreeMonoBold")
        try:
            font = tools.create_asset("F_Typewriter", TM + "/Font", unreal.Font, unreal.FontFactory())
            font.set_editor_property("font_cache_type", unreal.FontCacheType.RUNTIME)
            cf = font.get_editor_property("composite_font")
            tf = cf.get_editor_property("default_typeface")
            fd = unreal.FontData(); fd.set_editor_property("font_face_asset", face)
            te = unreal.TypefaceEntry(); te.set_editor_property("name", "Regular"); te.set_editor_property("font", fd)
            tf.set_editor_property("fonts", [te]); cf.set_editor_property("default_typeface", tf)
            font.set_editor_property("composite_font", cf)
            try:
                font.set_editor_property("legacy_font_size", 24)
            except Exception as e:
                log("font size: %s" % e)
            EAL.save_loaded_asset(font); log("font F_Typewriter created")
        except Exception as e:
            log("FONT FAILED (HUD will use Roboto): %s" % e)

    # ------------------------------------------------ tag the trash bags / drop-off in their class defaults
    for path, tag in (("/Game/TaskSystem/Tasks/TrashTask/BP_TrashBag", "Task_Trash"), ("/Game/TaskSystem/Tasks/TrashTask/BP_TrashDropOff", "Task_Dumpster")):
        b = unreal.load_asset(path); d = unreal.get_default_object(BEL.generated_class(b))
        tags = [str(x) for x in d.get_editor_property("tags")]
        if tag not in tags:
            b.modify(); d.set_editor_property("tags", [unreal.Name(x) for x in tags + [tag]])
            BEL.compile_blueprint(b); EAL.save_loaded_asset(b)
        log("%s default tags: %s" % (path.split("/")[-1], [str(x) for x in d.get_editor_property("tags")]))
    missing = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        c = a.get_class().get_name()
        want = "Task_Trash" if c == "BP_TrashBag_C" else ("Task_Dumpster" if c == "BP_TrashDropOff_C" else None)
        if want and want not in [str(x) for x in a.tags]:
            missing.append(a.get_actor_label())
    log("placed trash actors missing their tag: %s" % (missing or "none"))

    # ------------------------------------------------ BP_TaskPickup: walk into it to pick it up
    pk, new = bp_asset("BP_TaskPickup", unreal.Actor)
    if new:
        sph = subobj(pk, unreal.SphereComponent, "PickupRange")
        sph.set_editor_property("sphere_radius", 90.0); sph.set_collision_profile_name("OverlapAllDynamic")
        sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        mesh = subobj(pk, unreal.StaticMeshComponent, "Mesh")
        mug = unreal.load_asset("/Game/TaskSystem/Tasks/Coffee/CoffeeMug")
        if mug: mesh.set_editor_property("static_mesh", mug)
        mesh.set_collision_profile_name("NoCollision")
        ed = BGE.get_graph_editor(BEL.find_event_graph(pk))
        ev = BEL.add_event_override(pk, "ReceiveActorBeginOverlap", unreal.IntPoint(0, 0))
        pp = ed.add_call_function_node("/Script/Engine.GameplayStatics:GetPlayerPawn"); BEL.set_node_pos(pp, unreal.IntPoint(0, 200))
        eq = ed.add_call_function_node("/Script/Engine.KismetMathLibrary:EqualEqual_ObjectObject"); BEL.set_node_pos(eq, unreal.IntPoint(250, 150))
        PIN.try_create_connection(BEL.find_output_pin(ev, "OtherActor"), BEL.find_input_pin(eq, "A"))
        PIN.try_create_connection(BEL.find_output_pin(pp, "ReturnValue"), BEL.find_input_pin(eq, "B"))
        br = ed.add_branch_node(); BEL.set_node_pos(br, unreal.IntPoint(450, 0))
        PIN.try_create_connection(BEL.find_output_pin(ev, "then"), BEL.find_input_pin(br, "execute"))
        PIN.try_create_connection(BEL.find_output_pin(eq, "ReturnValue"), BEL.find_input_pin(br, "Condition"))
        snd = ed.add_call_function_node("/Script/Engine.GameplayStatics:PlaySound2D"); BEL.set_node_pos(snd, unreal.IntPoint(650, 0))
        PIN.set_pin_value(BEL.find_input_pin(snd, "Sound"), "/Game/Office80s/Audio/SFX_80s_TrashPickup.SFX_80s_TrashPickup")
        PIN.try_create_connection(BEL.find_output_pin(br, "then"), BEL.find_input_pin(snd, "execute"))
        de = ed.add_call_function_node("/Script/Engine.Actor:K2_DestroyActor"); BEL.set_node_pos(de, unreal.IntPoint(900, 0))
        PIN.try_create_connection(BEL.find_output_pin(snd, "then"), BEL.find_input_pin(de, "execute"))
        BEL.compile_blueprint(pk); EAL.save_loaded_asset(pk); log("BP_TaskPickup created")
    # ------------------------------------------------ BP_TaskZone: a box you walk into
    zn, new = bp_asset("BP_TaskZone", unreal.Actor)
    if new:
        box = subobj(zn, unreal.BoxComponent, "Zone")
        box.set_editor_property("box_extent", unreal.Vector(150, 150, 150)); box.set_collision_profile_name("OverlapAllDynamic")
        box.set_editor_property("line_thickness", 4.0); box.set_editor_property("shape_color", unreal.Color(r=255, g=200, b=40, a=255))
        BEL.compile_blueprint(zn); EAL.save_loaded_asset(zn); log("BP_TaskZone created")

    # ------------------------------------------------ README next to the assets
    content = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
    d = os.path.join(content, "TaskSystem", "TaskManager"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "README_TaskManager.txt"), "w").write(open(os.path.join(here, "README_TaskManager.txt")).read())
    log("README written to " + d)

try:
    main()
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "setup_task_manager.log"), "w").write("\n".join(LOG))
