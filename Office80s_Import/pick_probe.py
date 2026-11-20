"""Test only (in Office80s/Temp): can a data asset hold a picked level actor, and does it resolve in Play?"""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; EAL = unreal.EditorAssetLibrary; tools = unreal.AssetToolsHelpers.get_asset_tools()
LOG = []
def log(m): LOG.append(str(m)); unreal.log("[Probe] " + str(m))
try:
    log("BEL type fns: %s" % [a for a in dir(BEL) if "type" in a.lower()])
    log("BEL tip/meta fns: %s" % [a for a in dir(BEL) if "tool" in a.lower() or "meta" in a.lower() or "desc" in a.lower()])
    P = "/Game/Office80s/Temp/BPD_PickProbe"
    bp = unreal.load_asset(P) if EAL.does_asset_exist(P) else BEL.create_blueprint_asset_with_parent(P, unreal.PrimaryDataAsset)
    pt = None
    if hasattr(BEL, "get_soft_object_reference_type"):
        pt = BEL.get_soft_object_reference_type(unreal.Actor.static_class()); log("used get_soft_object_reference_type")
    else:
        pt = BEL.get_object_reference_type(unreal.Actor.static_class())
        try:
            pt.set_editor_property("pin_category", "softobject"); log("set pin_category softobject")
        except Exception as e:
            log("pin_category set failed: %s" % e)
    log("pin type: %s" % pt)
    have = [str(x) for x in BEL.list_member_variable_names(bp)]
    if "Pick" not in have:
        log("add Pick: %s" % BEL.add_member_variable(bp, "Pick", pt))
        log("add Picks: %s" % BEL.add_member_variable(bp, "Picks", BEL.get_array_type(pt)))
    BEL.set_blueprint_variable_instance_editable(bp, "Pick", True)
    BEL.set_blueprint_variable_instance_editable(bp, "Picks", True)
    BEL.compile_blueprint(bp); EAL.save_loaded_asset(bp)
    cls = BEL.generated_class(bp)
    for pr in ("Pick", "Picks"):
        try:
            log("%s default value: %r" % (pr, unreal.get_default_object(cls).get_editor_property(pr)))
        except Exception as e:
            log("%s read failed %s" % (pr, e))
    D = "/Game/Office80s/Temp/DA_PickProbe"
    if EAL.does_asset_exist(D):
        da = unreal.load_asset(D)
    else:
        f = unreal.DataAssetFactory(); f.set_editor_property("data_asset_class", cls)
        da = tools.create_asset("DA_PickProbe", "/Game/Office80s/Temp", None, f)
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    bag = [a for a in acts if "TrashBag" in a.get_class().get_name()][:2]
    log("bags: %s" % [b.get_path_name() for b in bag])
    if bag:
        for how in ("actor", "softpath"):
            try:
                v = bag[0] if how == "actor" else unreal.SoftObjectPath(bag[0].get_path_name())
                da.set_editor_property("Pick", v); log("set Pick via %s ok -> %r" % (how, da.get_editor_property("Pick"))); break
            except Exception as e:
                log("set Pick via %s failed: %s" % (how, e))
        try:
            da.set_editor_property("Picks", bag); log("Picks -> %r" % (da.get_editor_property("Picks"),))
        except Exception as e:
            log("set Picks failed: %s" % e)
    EAL.save_loaded_asset(da)
    log("probe ready")
except Exception:
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "pick_probe.log"), "w").write("\n".join(LOG))
