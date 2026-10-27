"""Spooky dressing for the Office (no fog): two desks stuck to the ceiling, flickering lights,
a red-lit janitor closet, a ring of chairs facing each other in reception, a chair facing the corner,
knocked-over chairs, scattered paperwork and a message on the wall. Re-runnable: clears Office80s/Spooky first."""
import os, math, unreal
FOLDER = "Office80s/Spooky"
here = os.path.dirname(os.path.abspath(__file__))
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
def log(m): unreal.log("[Office80s] " + m)
FLOOR, CEIL = 20.0, 994.5

DESK_T = unreal.load_asset("/Game/Office80s/Meshes/SM_Desk80s_Terminal/SM_Desk80s_Terminal/StaticMeshes/SM_Desk80s_Terminal")
DESK_C = unreal.load_asset("/Game/Office80s/Meshes/SM_Desk80s_Clerical/SM_Desk80s_Clerical/StaticMeshes/SM_Desk80s_Clerical")
CHAIR = unreal.load_asset("/Game/Office80s/Meshes/SM_OfficeChair80s/SM_OfficeChair80s/StaticMeshes/SM_OfficeChair80s")

def import_mesh(name):
    t = unreal.AssetImportTask()
    t.filename = os.path.join(here, name + ".glb"); t.destination_path = "/Game/Office80s/Props/Spooky/" + name
    t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t])
    for p in unreal.EditorAssetLibrary.list_assets("/Game/Office80s/Props/Spooky/" + name, recursive=True):
        x = unreal.load_asset(p)
        if isinstance(x, unreal.StaticMesh):
            unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).remove_collisions(x)
            unreal.EditorAssetLibrary.save_loaded_asset(x)
            return x

def flicker_material(name, f1, f2, bias):
    path = "/Game/Office80s/Materials/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.load_asset(path); mel.delete_all_material_expressions(mat)
    else:
        mat = tools.create_asset(name, "/Game/Office80s/Materials", unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_LIGHT_FUNCTION)
    def node(cls, x, y):
        return mel.create_material_expression(mat, cls, x, y)
    def const(v, x, y):
        e = node(unreal.MaterialExpressionConstant, x, y); e.set_editor_property("r", v); return e
    t = node(unreal.MaterialExpressionTime, -1200, 0)
    sins = []
    for k, f in enumerate((f1, f2)):
        m = node(unreal.MaterialExpressionMultiply, -1000, k * 150)
        mel.connect_material_expressions(t, "", m, "A"); mel.connect_material_expressions(const(f, -1150, 80 + k * 150), "", m, "B")
        s = node(unreal.MaterialExpressionSine, -850, k * 150)
        mel.connect_material_expressions(m, "", s, "")
        sins.append(s)
    p = node(unreal.MaterialExpressionMultiply, -700, 60)
    mel.connect_material_expressions(sins[0], "", p, "A"); mel.connect_material_expressions(sins[1], "", p, "B")
    a = node(unreal.MaterialExpressionAdd, -550, 60)
    mel.connect_material_expressions(p, "", a, "A"); mel.connect_material_expressions(const(bias, -650, 200), "", a, "B")
    g = node(unreal.MaterialExpressionMultiply, -400, 60)
    mel.connect_material_expressions(a, "", g, "A"); mel.connect_material_expressions(const(5.0, -500, 200), "", g, "B")
    c = node(unreal.MaterialExpressionClamp, -250, 60)
    mel.connect_material_expressions(g, "", c, "")
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

made = []
def spawn(mesh, x, y, z, rot, label, settle=False, collide=True):
    a = sub.spawn_actor_from_object(mesh, unreal.Vector(x, y, z), rot)
    if settle:
        o, e = a.get_actor_bounds(False)
        p = a.get_actor_location()
        a.set_actor_location(unreal.Vector(p.x, p.y, p.z + (FLOOR - (o.z - e.z))), False, False)
    c = a.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.STATIC)
    if not collide:
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.set_actor_label(label); a.set_folder_path(FOLDER)
    made.append(label)
    return a

paperA = import_mesh("SM_80s_PaperScatter_A")
paperB = import_mesh("SM_80s_PaperScatter_B")
flA = flicker_material("M_80s_LightFlicker_A", 23.0, 7.1, 0.62)
flB = flicker_material("M_80s_LightFlicker_B", 17.3, 4.7, 0.55)

with unreal.ScopedEditorTransaction("Office spooky dressing"):
    old = [a for a in sub.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]
    if old:
        sub.destroy_actors(old)

    # desks (and their chairs) stuck to the ceiling, upside down
    for i, (mesh, x, y, yaw) in enumerate(((DESK_T, 3450, -3050, 25.0), (DESK_C, 3700, -850, -62.0))):
        spawn(mesh, x, y, CEIL, unreal.Rotator(180, 0, yaw), "CeilingDesk_%d" % (i + 1))
        r = math.radians(yaw)
        cx, cy = x + 120 * math.sin(r) + 30 * math.cos(r), y - 120 * math.cos(r)
        spawn(CHAIR, cx, cy, CEIL, unreal.Rotator(180, 0, yaw + 160), "CeilingChair_%d" % (i + 1))

    # reception: six chairs in a circle, facing each other, papers in the middle
    cx, cy, R = 1300.0, -2700.0, 175.0
    for k in range(6):
        ang = math.radians(k * 60 + 15)
        x, y = cx + R * math.cos(ang), cy + R * math.sin(ang)
        yaw = math.degrees(math.atan2(-math.cos(ang), math.sin(ang)))
        spawn(CHAIR, x, y, FLOOR, unreal.Rotator(0, 0, yaw), "CircleChair_%d" % (k + 1))
    spawn(paperB, cx, cy, FLOOR, unreal.Rotator(0, 0, 40), "Papers_Circle", collide=False)
    # one chair pushed into the corner, facing the wall
    spawn(CHAIR, 805, -1785, FLOOR, unreal.Rotator(0, 0, -135), "CornerChair")

    # knocked-over chairs
    spawn(CHAIR, 2700, -3750, FLOOR, unreal.Rotator(90, 0, 30), "FallenChair_1", settle=True)
    spawn(CHAIR, 4100, -3770, FLOOR, unreal.Rotator(0, 90, -70), "FallenChair_2", settle=True)
    spawn(CHAIR, 3830, -450, FLOOR, unreal.Rotator(-90, 0, 115), "FallenChair_3", settle=True)

    # scattered paperwork
    spawn(paperA, 3450, -3300, FLOOR, unreal.Rotator(0, 0, 0), "Papers_1", collide=False)
    spawn(paperB, 3700, -1000, FLOOR, unreal.Rotator(0, 0, 70), "Papers_2", collide=False)
    spawn(paperA, 2600, -3760, FLOOR, unreal.Rotator(0, 0, 130), "Papers_3", collide=False)

    # message on the east wall of the main office, up high
    t = sub.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(4887.5, -2365, 560), unreal.Rotator(-3, 0, 180))
    tc = t.get_component_by_class(unreal.TextRenderComponent)
    tc.set_text(unreal.Text("THEY NEVER CLOCKED OUT"))
    tc.set_world_size(58.0)
    tc.set_text_render_color(unreal.Color(r=120, g=10, b=8, a=255))
    try:
        tc.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    except Exception:
        pass
    t.set_actor_label("WallMessage"); t.set_folder_path(FOLDER); made.append("WallMessage")

    # lights: three flicker, the janitor closet glows red
    lights = {}
    for a in sub.get_all_level_actors():
        if isinstance(a, unreal.RectLight):
            lights[a.get_actor_label()] = a
    for lab, mat in (("RectLight5", flA), ("RectLight10", flB), ("RectLight16", flA)):
        if lab in lights:
            c = lights[lab].get_component_by_class(unreal.RectLightComponent)
            lights[lab].modify(); c.modify()
            c.set_editor_property("light_function_material", mat)
    if "RectLight" in lights:
        c = lights["RectLight"].get_component_by_class(unreal.RectLightComponent)
        lights["RectLight"].modify(); c.modify()
        c.set_editor_property("light_color", unreal.Color(r=255, g=38, b=28, a=255))

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
log("spooky: placed %d (%s); still unsaved: %d" % (len(made), ", ".join(made), len(left)))
