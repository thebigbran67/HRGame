"""Give all slime (puddles + wall drips) a real glowing material."""
import unreal
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

def glow_mat(name, base, emis, rough):
    path = "/Game/Office80s/Materials/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.load_asset(path); mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset(name, "/Game/Office80s/Materials", unreal.Material, unreal.MaterialFactoryNew())
    def v3(c, y):
        e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, y)
        e.set_editor_property("constant", unreal.LinearColor(c[0], c[1], c[2], 1.0)); return e
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 300)
    r.set_editor_property("r", rough)
    mel.connect_material_property(v3(base, 0), "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(v3(emis, 150), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

bright = glow_mat("M_80s_SlimeGlow", (0.05, 0.25, 0.01), (0.6, 4.0, 0.15), 0.1)
dark = glow_mat("M_80s_SlimeGlowDark", (0.02, 0.08, 0.005), (0.15, 1.2, 0.04), 0.15)
done = []
for p in unreal.EditorAssetLibrary.list_assets("/Game/Office80s/Props/Monster", recursive=True):
    sm = unreal.load_asset(p)
    if not isinstance(sm, unreal.StaticMesh) or "Slime" not in sm.get_name():
        continue
    mats = sm.get_editor_property("static_materials")
    for m in mats:
        slot = str(m.get_editor_property("material_slot_name"))
        if "SlimeDark" in slot:
            m.set_editor_property("material_interface", dark)
        elif "Slime" in slot:
            m.set_editor_property("material_interface", bright)
    sm.set_editor_property("static_materials", mats)
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
    done.append(sm.get_name())
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log("[Office80s] slime glow on %s" % done)
