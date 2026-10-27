import unreal, os
out = []
for cname in dir(unreal):
    low = cname.lower()
    if any(k in low for k in ("blueprinteditor", "k2node", "edgraph", "graphnode", "toolset", "blueprintgraph", "kismet", "bpgraph", "nodeutil")):
        c = getattr(unreal, cname)
        meths = [m for m in dir(c) if not m.startswith("_")][:80]
        out.append(cname + ": " + ", ".join(meths))
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_probe.txt")
open(p, "w").write("\n".join(out))
unreal.log("[Office80s] api probe %d" % len(out))
