import unreal, os
BEL = unreal.BlueprintEditorLibrary; PIN = unreal.BlueprintGraphPinLibrary; BGE = unreal.BlueprintGraphEditor
out = []
for p in unreal.EditorAssetLibrary.list_assets("/Game", recursive=True):
    ad = unreal.EditorAssetLibrary.find_asset_data(p)
    if str(ad.asset_class_path.asset_name) not in ("Blueprint", "WidgetBlueprint"):
        continue
    bp = unreal.load_asset(p)
    try:
        graphs = BEL.list_graphs(bp)
    except Exception as e:
        continue
    for g in graphs:
        try:
            ed = BGE.get_graph_editor(g)
            nodes = ed.list_all_nodes()
        except Exception:
            continue
        for n in nodes:
            for pin in BEL.list_all_pins(n):
                nm = str(PIN.get_pin_name(pin))
                if nm in ("MaxWalkSpeed", "MaxWalkSpeedCrouched", "NewMaxWalkSpeed") or "WalkSpeed" in nm:
                    if PIN.get_pin_direction(pin) == unreal.EdGraphPinDirection.EGPD_INPUT:
                        out.append("%s | %s | %s | %s | value=%s | linked=%d" % (p.split(".")[0], g.get_name(), n.get_name(), nm, PIN.get_pin_value(pin), len(PIN.list_connected_pins(pin))))
for bpp in ("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter", "/Game/Variant_Horror/Blueprints/BP_HorrorCharacter"):
    bp = unreal.load_asset(bpp)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        o = lib.get_object(lib.get_data(h))
        if isinstance(o, unreal.CharacterMovementComponent):
            out.append("TEMPLATE %s walk=%s accel=%s" % (bpp, o.get_editor_property("max_walk_speed"), o.get_editor_property("max_acceleration")))
    cdo = unreal.get_default_object(BEL.generated_class(bp))
    out.append("CDO %s walk=%s" % (bpp, cdo.get_editor_property("character_movement").get_editor_property("max_walk_speed")))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "speed_scan.txt"), "w").write("\n".join(out))
unreal.log("[Office80s] speed scan %d" % len(out))
