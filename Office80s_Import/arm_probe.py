import unreal, os
BEL = unreal.BlueprintEditorLibrary
out = []
bp = unreal.load_asset("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    o = lib.get_object(lib.get_data(h))
    if o is None: continue
    line = "%s %s" % (o.get_name(), o.get_class().get_name())
    if isinstance(o, unreal.SkeletalMeshComponent):
        for k in ("skeletal_mesh_asset", "anim_class", "animation_mode", "visible", "only_owner_see", "first_person_primitive_type"):
            try: line += " | %s=%s" % (k, o.get_editor_property(k))
            except Exception as e: line += " | %s=?" % k
    out.append(line)
par = BEL.get_blueprint_parent_class(bp); out.append("parent %s" % par)
cdo = unreal.get_default_object(BEL.generated_class(bp))
for c in cdo.get_components_by_class(unreal.SkeletalMeshComponent):
    out.append("cdo comp %s anim=%s mode=%s mesh=%s" % (c.get_name(), c.get_editor_property("anim_class"), c.get_editor_property("animation_mode"), c.get_editor_property("skeletal_mesh_asset")))
for p in unreal.EditorAssetLibrary.list_assets("/Game/Characters", recursive=True):
    n = p.split("/")[-1].lower()
    if "idle" in n or n.startswith("abp") or "fp_" in n:
        out.append("asset " + p)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "arm_probe.txt"), "w").write("\n".join(out))
