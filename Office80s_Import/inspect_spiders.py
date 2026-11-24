"""Read-only: quest spiders + where they are, spider props, widget blueprint list, BP_QuestSpider logic."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
L = []
try:
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    for a in acts:
        cn = a.get_class().get_name()
        lab = a.get_actor_label()
        tags = [str(t) for t in a.tags]
        loc = a.get_actor_location()
        mesh = ""
        if isinstance(a, unreal.StaticMeshActor):
            m = a.static_mesh_component.static_mesh
            mesh = m.get_name() if m else ""
        if "spider" in (cn + lab + mesh).lower() or "Task_Spider" in tags or "web" in mesh.lower() or "cocoon" in mesh.lower() or "egg" in mesh.lower():
            L.append("ACTOR %-34s class=%-22s mesh=%-26s loc=(%d,%d,%d) tags=%s folder=%s path=%s" % (lab, cn, mesh, loc.x, loc.y, loc.z, tags, a.get_folder_path(), a.get_path_name()))
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for ad in ar.get_assets_by_path("/Game", recursive=True):
        if str(ad.asset_class_path.asset_name) == "WidgetBlueprint":
            L.append("WIDGET %s" % ad.package_name)
    bp = unreal.load_asset("/Game/_TASKS/BP_QuestSpider")
    L.append("QuestSpider vars: %s" % [str(v) for v in BEL.list_member_variable_names(bp) if "/" not in str(v)])
    ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
    for n in ed.list_all_nodes():
        outs = []
        for p in BEL.list_all_pins(n, unreal.EdGraphPinDirection.EGPD_OUTPUT):
            for q in PIN.list_connected_pins(p):
                outs.append("%s->%s.%s" % (PIN.get_pin_name(p), str(BEL.get_node_title(PIN.get_owning_node(q))).replace("\n", " "), PIN.get_pin_name(q)))
        vals = []
        for p in BEL.list_all_pins(n, unreal.EdGraphPinDirection.EGPD_INPUT):
            v = PIN.get_pin_value(p)
            if v and not PIN.list_connected_pins(p): vals.append("%s=%s" % (PIN.get_pin_name(p), v))
        L.append("  QS %s %s OUT %s" % (str(BEL.get_node_title(n)).replace("\n", " "), vals, outs))
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "inspect_spiders.log"), "w").write("\n".join(L))
