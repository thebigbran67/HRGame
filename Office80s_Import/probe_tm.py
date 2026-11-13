"""Throwaway probe in /Game/Office80s/Temp: array node names, data-asset-from-BP creation, TTF font import."""
import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor
tools = unreal.AssetToolsHelpers.get_asset_tools()
out = []
T = "/Game/Office80s/Temp"
try:
    for p in (T + "/BP_ProbeA", T + "/BPD_Probe", T + "/DA_Probe"):
        if unreal.EditorAssetLibrary.does_asset_exist(p): unreal.EditorAssetLibrary.delete_asset(p)
    bp = BEL.create_blueprint_asset_with_parent(T + "/BP_ProbeA", unreal.Actor)
    BEL.add_member_variable(bp, "Arr", BEL.get_array_type(BEL.get_basic_type_by_name("string")))
    ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
    g = ed.add_get_member_variable_node("Arr", "")
    for nm in ("Utilities|Array|Get (a copy)", "Utilities|Array|Get (a ref)", "Utilities|Array|Get", "Utilities|Array|GET"):
        try:
            n = ed.create_node_from_name(nm, unreal.Vector2D(0, 0), [BEL.find_output_pin(g, "Arr")])
            out.append("array get %r -> %s" % (nm, n.get_name() if n else None))
        except Exception as e:
            out.append("array get %r -> EXC %s" % (nm, e))
    for nm in ("Utilities|String|Contains", "String|Contains", "Utilities|Casting|CastToBP_ProbeA"):
        try:
            n = ed.create_node_from_name(nm, unreal.Vector2D(0, 0), [])
            out.append("node %r -> %s" % (nm, n.get_name() if n else None))
        except Exception as e:
            out.append("node %r -> EXC %s" % (nm, e))
    # data asset class from a blueprint
    bpd = BEL.create_blueprint_asset_with_parent(T + "/BPD_Probe", unreal.PrimaryDataAsset)
    BEL.add_member_variable(bpd, "Title", BEL.get_basic_type_by_name("string"))
    BEL.set_blueprint_variable_instance_editable(bpd, "Title", True)
    BEL.compile_blueprint(bpd)
    f = unreal.DataAssetFactory()
    try:
        f.set_editor_property("data_asset_class", BEL.generated_class(bpd))
    except Exception as e:
        out.append("factory prop: %s" % e)
    da = tools.create_asset("DA_Probe", T, None, f)
    out.append("data asset: %s class %s" % (da, da.get_class() if da else None))
    if da:
        da.set_editor_property("Title", "hello"); out.append("title set -> %s" % da.get_editor_property("Title"))
    # font import
    t = unreal.AssetImportTask(); t.filename = os.path.join(here, "ui", "FreeMonoBold.ttf"); t.destination_path = T + "/Font"
    t.automated = True; t.replace_existing = True; t.save = False
    tools.import_asset_tasks([t])
    out.append("font import objects: %s" % list(t.get_editor_property("imported_object_paths")))
    for p in unreal.EditorAssetLibrary.list_assets(T + "/Font", recursive=True):
        out.append("  font asset %s %s" % (p, unreal.load_asset(p).get_class().get_name()))
except Exception:
    import traceback; out.append("EXC " + traceback.format_exc())
open(os.path.join(here, "probe_tm.txt"), "w").write("\n".join(out))
