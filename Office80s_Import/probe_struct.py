import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
out = []
names = [n for n in dir(unreal) if "Struct" in n or "DataTable" in n]
out.append("unreal names: " + ", ".join(names))
for cls in ("StructureEditorLibrary", "UserDefinedStructEditorLibrary", "DataTableFunctionLibrary", "EditorDataTableLibrary"):
    c = getattr(unreal, cls, None)
    if c:
        out.append("%s: %s" % (cls, [m for m in dir(c) if not m.startswith("_")]))
s = unreal.load_asset("/Game/TaskSystem/ST_Task")
out.append("ST_Task: %s" % s)
bel = unreal.BlueprintEditorLibrary
out.append("BEL: %s" % [m for m in dir(bel) if not m.startswith("_")])
# monster names in the level
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if "Monster" in a.get_class().get_name():
        props = {}
        for p in ("MonsterName", "Dialogue", "Option1", "Option2", "Option3"):
            try:
                props[p] = str(a.get_editor_property(p))
            except Exception as e:
                props[p] = "ERR"
        out.append("%s %s tags=%s %s" % (a.get_actor_label(), a.get_class().get_name(), [str(t) for t in a.tags], props))
open(os.path.join(here, "probe_struct.txt"), "w").write("\n".join(out))
