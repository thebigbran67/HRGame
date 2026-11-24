"""Read-only: who references BP_QuestSpider / Task_Spider, and dump those graphs' spider-related nodes."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
L = []
try:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    opts = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True, include_searchable_names=False, include_soft_management_references=False, include_hard_management_references=False)
    for pk in ("/Game/_TASKS/BP_QuestSpider",):
        L.append("refs of %s: %s" % (pk, [str(r) for r in ar.get_referencers(pk, opts)]))
    a = unreal.load_asset("/Game/_TASKS/BP_QuestSpider")
    L.append("QuestSpider class %s parent %s" % (a.get_class().get_name(), BEL.generated_class(a).get_super_class().get_name() if hasattr(BEL.generated_class(a), "get_super_class") else "?"))
    for pk in [str(r) for r in ar.get_referencers("/Game/_TASKS/BP_QuestSpider", opts)]:
        bp = unreal.load_asset(pk)
        if not isinstance(bp, unreal.Blueprint): continue
        for gname in [str(g) for g in BEL.list_graph_names(bp)] if hasattr(BEL, "list_graph_names") else ["EventGraph"]:
            try:
                ed = BGE.get_graph_editor_by_name(bp, gname) or BGE.get_graph_editor(BEL.find_event_graph(bp))
            except Exception: continue
            for n in ed.list_all_nodes():
                t = str(BEL.get_node_title(n)).replace("\n", " ")
                vals = []
                for p in BEL.list_all_pins(n, unreal.EdGraphPinDirection.EGPD_INPUT):
                    v = PIN.get_pin_value(p)
                    if v and not PIN.list_connected_pins(p): vals.append("%s=%s" % (PIN.get_pin_name(p), v))
                L.append("  %s/%s [%s] %s %s" % (pk.split("/")[-1], gname, n.get_name(), t, vals))
except Exception:
    L.append("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "find_spider_spawn.log"), "w").write("\n".join(L))
