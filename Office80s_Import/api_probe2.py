import unreal, os
out = []
for cname in ("BlueprintEditorLibrary", "BlueprintGraphPinLibrary", "BlueprintGraphEditor", "BlueprintGraphPin", "EdGraphPinType", "ToolsetRegistry"):
    c = getattr(unreal, cname)
    for m in dir(c):
        if m.startswith("_"): continue
        doc = (getattr(c, m).__doc__ or "").strip().replace("\n", " ")[:400]
        out.append("%s.%s :: %s" % (cname, m, doc))
try:
    out.append("SCHEMAS:: " + str(unreal.ToolsetRegistry.get_all_toolset_json_schemas())[:20000])
except Exception as e:
    out.append("schema err %s" % e)
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_probe2.txt")
open(p, "w", encoding="utf-8").write("\n".join(out))
unreal.log("[Office80s] api probe2 %d" % len(out))
