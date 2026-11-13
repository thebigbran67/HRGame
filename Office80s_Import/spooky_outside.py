"""Makes the whole outside spooky while keeping the parking lot and road usable: gravestones in the yard
and past the street, dead trees, an iron fence around the property, rocks and dead grass, glowing
jack-o'-lanterns, slime and claw tracks on the lot, a giant spider on the roof, a big moon, and a couple
of burnt-out lot lamps. No fog added. Re-runnable: clears Office80s/OutsideSpooky first."""
import os, math, random, unreal
here = os.path.dirname(os.path.abspath(__file__))
FOLDER = "Office80s/OutsideSpooky"
DEST = "/Game/Office80s/OutsideSpooky"
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))
rng = random.Random(4242)
O = "/Game/Office80s/Outdoor/"
MN = "/Game/Office80s/Props/Monster/"
def asset(base, name):
    return unreal.load_asset("%s%s/%s/StaticMeshes/%s" % (base, name, name, name))

def imp(name, collide):
    dest = DEST + "/" + name
    t = unreal.AssetImportTask()
    t.filename = os.path.join(here, name + ".glb"); t.destination_path = dest
    t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t])
    for p in unreal.EditorAssetLibrary.list_assets(dest, recursive=True):
        x = unreal.load_asset(p)
        if isinstance(x, unreal.StaticMesh):
            sms.remove_collisions(x)
            if collide:
                sms.add_simple_collisions(x, unreal.ScriptCollisionShapeType.BOX)
            unreal.EditorAssetLibrary.save_loaded_asset(x)
            return x
    raise RuntimeError("import failed " + name)

# no-go zones (x0, y0, x1, y1)
BUILDING = (500, -5950, 6500, 1250)
LOT = (100, -9420, 7400, -5780)
ROAD = (-40000, -10780, 40000, -9740)
SIDE_PATH = (6450, -5950, 7150, 1300)
def inside(x, y, r):
    return r[0] <= x <= r[2] and r[1] <= y <= r[3]
def free(x, y, extra=()):
    return not any(inside(x, y, r) for r in (BUILDING, LOT, ROAD, SIDE_PATH) + tuple(extra))

def main():
    graves = [imp("SM_80s_Grave_" + k, True) for k in ("Round", "Slab", "Cross")]
    jack = imp("SM_80s_JackOLantern", False)
    moon = imp("SM_80s_Moon", False)
    trees = [asset(O, "SM_80s_DeadTree_" + k) for k in "ABC"]
    grass = [asset(O, "SM_80s_GrassPatch_" + k) for k in "AB"]
    rocks = [asset(O, "SM_80s_Rocks_" + k) for k in "AB"]
    fences = [asset(O, "SM_80s_IronFence"), asset(O, "SM_80s_IronFence_B")]
    slime = [asset(MN, "SM_80s_Slime_A"), asset(MN, "SM_80s_Slime_B")]
    tracks = asset(MN, "SM_80s_ClawTracks"); bones = asset(MN, "SM_80s_Bones"); spider = asset(MN, "SM_80s_SpiderBig")
    n = {}
    with unreal.ScopedEditorTransaction("Spooky outside"):
        old = [a for a in sub.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]
        if old:
            sub.destroy_actors(old)
        acts = sub.get_all_level_actors()
        yard_blockers = [(a.get_actor_location().x, a.get_actor_location().y) for a in acts
                         if str(a.get_folder_path()) in ("Office80s/Outdoor/DeadTree", "Office80s/Outdoor/Rocks", "Office80s/Outdoor/LampPost")]
        drop = next(a for a in acts if a.get_actor_label() == "BP_TrashDropOff").get_actor_location()

        def put(mesh, x, y, z, yaw, kind, scale=1.0, collide=False, shadow=True, pitch=0.0, roll=0.0):
            a = sub.spawn_actor_from_object(mesh, unreal.Vector(x, y, z), unreal.Rotator(roll, pitch, yaw))
            if scale != 1.0:
                a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
            c = a.static_mesh_component; c.set_mobility(unreal.ComponentMobility.STATIC)
            if not collide:
                c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            c.set_editor_property("cast_shadow", shadow)
            n[kind] = n.get(kind, 0) + 1
            a.set_actor_label("%s_%03d" % (kind, n[kind])); a.set_folder_path(FOLDER + "/" + kind)
            return a
        def glow(x, y, z, inten=1.6, radius=420.0, color=unreal.Color(r=255, g=140, b=40, a=255)):
            lt = sub.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, z))
            pl = lt.point_light_component; pl.set_mobility(unreal.ComponentMobility.MOVABLE)
            pl.set_editor_property("intensity", inten); pl.set_editor_property("attenuation_radius", radius)
            pl.set_editor_property("light_color", color); pl.set_editor_property("cast_shadows", False)
            n["Glow"] = n.get("Glow", 0) + 1
            lt.set_actor_label("PumpkinGlow_%02d" % n["Glow"]); lt.set_folder_path(FOLDER + "/Lights")

        # ---- graveyard: rows of crooked headstones, kept off the walk to the dumpster
        placed = []
        tries = 0
        while len(placed) < 52 and tries < 4000:
            tries += 1
            x, y = rng.uniform(800, 6900), rng.uniform(1700, 10900)
            if abs(x - drop.x) < 520 or math.hypot(x - drop.x, y - drop.y) < 900:
                continue
            if any(math.hypot(x - bx, y - by) < 260 for bx, by in yard_blockers + placed):
                continue
            placed.append((x, y))
            put(rng.choice(graves), x, y, 22.9, rng.uniform(-14, 14), "Grave", rng.uniform(0.9, 1.25), True)
        # ---- more graves across the street (seen from the lot and in the intro)
        for i in range(18):
            x, y = rng.uniform(-3500, 9500), rng.uniform(-13600, -11200)
            put(rng.choice(graves), x, y, 19.0, 180 + rng.uniform(-20, 20), "Grave", rng.uniform(0.9, 1.3))
        # ---- dead trees all around
        spots = [(rng.uniform(-1300, 300), rng.uniform(-9300, 11800)) for _ in range(16)] + \
                [(rng.uniform(7300, 8500), rng.uniform(-9300, 11800)) for _ in range(16)] + \
                [(rng.uniform(-6000, 12000), rng.uniform(-16000, -11000)) for _ in range(18)] + \
                [(rng.uniform(-4000, 11000), rng.uniform(12300, 17000)) for _ in range(14)] + \
                [(rng.uniform(-9000, -1700), rng.uniform(-9000, 12000)) for _ in range(12)] + \
                [(rng.uniform(8900, 15000), rng.uniform(-9000, 12000)) for _ in range(12)]
        for x, y in spots:
            if free(x, y):
                put(rng.choice(trees), x, y, 19.0, rng.uniform(0, 360), "DeadTree", rng.uniform(0.8, 1.35))
        # ---- dead grass and rocks on the open ground
        for i in range(90):
            x, y = rng.uniform(-3000, 10500), rng.uniform(-14000, 13500)
            if free(x, y) and not inside(x, y, (600, 1150, 7080, 11170)):
                put(rng.choice(grass), x, y, 19.0, rng.uniform(0, 360), "DeadGrass", rng.uniform(0.7, 1.3), shadow=False)
        for i in range(45):
            x, y = rng.uniform(-2500, 10000), rng.uniform(-13500, 13000)
            if free(x, y):
                put(rng.choice(rocks), x, y, 19.0, rng.uniform(0, 360), "Rocks", rng.uniform(0.8, 1.8))
        # ---- crooked iron fence around the whole property (the road gap stays open for the car)
        def fence_run(x0, y0, x1, y1, skip=None):
            L = math.hypot(x1 - x0, y1 - y0); k = max(1, int(L / 312)); yaw = math.degrees(math.atan2(y1 - y0, x1 - x0))
            for i in range(k):
                t = (i + 0.5) / k; x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                if skip and skip[0] <= x <= skip[1]:
                    continue
                put(rng.choice(fences), x, y, 19.0, yaw + rng.uniform(-2.5, 2.5), "PerimeterFence", 1.0, shadow=False, roll=rng.uniform(-3, 3))
        fence_run(-1380, -9440, 8580, -9440, skip=(2350, 3050))
        fence_run(-1380, -9440, -1380, 11980)
        fence_run(8580, -9440, 8580, 11980)
        fence_run(-1380, 11980, 8580, 11980)
        # ---- jack-o'-lanterns: by the front door, on the lot edges, in the yard
        jacks = [(700, -6060, 160), (1250, -6060, 200), (300, -6500, 120), (300, -8200, 100), (7200, -6600, 250), (7200, -8400, 240),
                 (2300, -9300, 170), (3100, -9300, 190), (3700, 1600, 180), (2000, 4200, 160), (5600, 6800, 200), (3300, 9300, 175),
                 (4400, 9400, 185), (6900, -300, 260)]
        for i, (x, y, yaw) in enumerate(jacks):
            z = 28.0 if y > -6170 and y < -5830 else (22.9 if y > 1150 else 19.0)
            put(jack, x, y, z, yaw + rng.uniform(-15, 15), "JackOLantern", rng.uniform(0.9, 1.3), shadow=False)
            if i % 2 == 0:
                glow(x, y, z + 45)
        # ---- monster mess on the lot and road
        for x, y, yaw in ((2050, -8850, 30), (4600, -7100, 110), (6200, -8900, 200), (900, -6900, 60), (3900, -10200, 15)):
            put(rng.choice(slime), x, y, 21.3, yaw, "LotSlime", rng.uniform(1.0, 1.6), shadow=False)
        for x, y, yaw in ((3600, -8700, 95), (3650, -7600, 92), (1100, -6250, 150), (5200, -10350, 0)):
            put(tracks, x, y, 21.3, yaw, "LotClawTracks", 1.0, shadow=False)
        put(bones, BUILDING[0] + 4300, -8750, 21.0, 40, "LotBones")
        put(bones, -600, 3000, 19.0, 130, "LotBones")
        # ---- giant spider on the roof edge, staring down at the lot
        put(spider, 4500, -5700, 1096.0, -90, "RoofSpider", 3.2)
        # ---- moon over the building (seen in the intro wide shot)
        put(moon, -7000, 42000, 17000, 0, "Moon", 1.0, shadow=False)
        # ---- burnt-out and sickly lot lamps (steady, no flicker)
        for a in sub.get_all_level_actors():
            l = a.get_actor_label()
            if l in ("LotLampLight_3", "LotLampLight_5", "StreetLampLight_1", "StreetLampLight_4"):
                a.point_light_component.set_editor_property("intensity", 0.0)
            elif l in ("LotLampLight_2", "StreetLampLight_2"):
                a.point_light_component.set_editor_property("light_color", unreal.Color(r=150, g=255, b=120, a=255))
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("spooky outside: %s" % n)

try:
    main()
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "spooky_outside.log"), "w").write("\n".join(LOG))
