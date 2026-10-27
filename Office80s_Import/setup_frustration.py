"""Frustration bar setup:
 - WBP_Frustraion_Bar gets a Percent variable that drives its progress bar (red fill, dark back).
 - BP_Monster gets a screen-space FrustrationBar widget component above its head (hidden by default;
   BP_TaskHUD shows it on the janitor once the trash task is active).
 - The janitor BP_Monster in the Office gets the actor tag "Janitor"."""
import os, unreal
BEL = unreal.BlueprintEditorLibrary; PIN = unreal.BlueprintGraphPinLibrary; BGE = unreal.BlueprintGraphEditor
here = os.path.dirname(os.path.abspath(__file__))
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))

try:
    # ---------------- widget
    wbp = unreal.load_asset("/Game/FrustrationBar/WBP_Frustraion_Bar")
    if "Percent" not in [str(x) for x in BEL.list_member_variable_names(wbp, False)]:
        BEL.add_member_variable(wbp, "Percent", BEL.get_basic_type_by_name("real"))
    ged = BGE.get_graph_editor_by_name(wbp, "GetPercent")
    res = list(ged.list_nodes_of_class(unreal.K2Node_FunctionResult))[0]
    rp = BEL.find_input_pin(res, "ReturnValue")
    PIN.break_pin_links(rp)
    g = ged.add_get_member_variable_node("Percent", "")
    BEL.set_node_pos(g, unreal.IntPoint(-250, 120))
    log("percent bound: %s" % PIN.try_create_connection(BEL.find_output_pin(g, "Percent"), rp))
    bar = unreal.load_object(None, "/Game/FrustrationBar/WBP_Frustraion_Bar.WBP_Frustraion_Bar:WidgetTree.ProgressBar_68")
    if bar:
        bar.set_editor_property("fill_color_and_opacity", unreal.LinearColor(0.9, 0.12, 0.04, 1.0))
        try:
            st = bar.get_editor_property("widget_style")
            bg = st.get_editor_property("background_image")
            bg.set_editor_property("tint_color", unreal.SlateColor(unreal.LinearColor(0.03, 0.02, 0.02, 0.85)))
            st.set_editor_property("background_image", bg)
            bar.set_editor_property("widget_style", st)
        except Exception as e:
            log("bar style: %s" % e)
    BEL.compile_blueprint(wbp)
    unreal.EditorAssetLibrary.save_loaded_asset(wbp)

    # ---------------- widget component on BP_Monster
    mbp = unreal.load_asset("/Game/Blueprints/Dialogue/Blueprints/BP_Monster")
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sds.k2_gather_subobject_data_for_blueprint(mbp)
    comp = None
    for h in handles:
        o = lib.get_object(lib.get_data(h))
        if isinstance(o, unreal.WidgetComponent) and "FrustrationBar" in o.get_name():
            comp = o
    if comp is None:
        params = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=unreal.WidgetComponent, blueprint_context=mbp)
        nh, fail = sds.add_new_subobject(params)
        log("add component: fail=%s" % fail)
        sds.rename_subobject(nh, unreal.Text("FrustrationBar"))
        comp = lib.get_object(lib.get_data(nh))
    # head height from the placed janitor's sprite
    top = 430.0
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    jan = None
    for a in sub.get_all_level_actors():
        if a.get_class().get_name() == "BP_Monster_C":
            try:
                nm = str(a.get_editor_property("monster_name"))
            except Exception:
                nm = ""
            log("monster %s name '%s'" % (a.get_actor_label(), nm))
            if "janitor" in nm.lower():
                jan = a
    if jan:
        for c in jan.get_components_by_class(unreal.PrimitiveComponent):
            if c.get_class().get_name().startswith("PaperSprite"):
                o, e, r = unreal.SystemLibrary.get_component_bounds(c)
                top = (o.z + e.z) - jan.get_actor_location().z
                log("sprite top %.0f" % top)
    comp.set_editor_property("widget_class", unreal.load_asset("/Game/FrustrationBar/WBP_Frustraion_Bar").generated_class())
    comp.set_editor_property("space", unreal.WidgetSpace.SCREEN)
    comp.set_editor_property("draw_size", unreal.IntPoint(220, 22))
    comp.set_editor_property("relative_location", unreal.Vector(0, 0, top + 40))
    comp.set_editor_property("visible", False)
    comp.set_editor_property("collision_profile_name", "NoCollision")
    BEL.compile_blueprint(mbp)
    unreal.EditorAssetLibrary.save_loaded_asset(mbp)

    # ---------------- tag the janitor
    if jan:
        tags = list(jan.get_editor_property("tags"))
        if "Janitor" not in [str(t) for t in tags]:
            jan.modify(); tags.append(unreal.Name("Janitor")); jan.set_editor_property("tags", tags)
        log("janitor tagged: %s" % jan.get_actor_label())
    else:
        log("ERR no janitor found")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("frustration setup done")
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "setup_frustration.log"), "w").write("\n".join(LOG))
