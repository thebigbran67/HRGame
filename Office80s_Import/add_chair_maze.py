"""Chair maze: replaces the floating physics chairs in the east room with a maze of piled-up office chairs
that leads to BP_TrashBag4. Each wall is a chair-pile mesh (no collision) plus an invisible blocker box.
Re-runnable: clears the Office80s/ChairMaze folder first."""
import os, unreal
here = os.path.dirname(os.path.abspath(__file__))
FOLDER = "Office80s/ChairMaze"
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
LOG = []
def log(m):
    LOG.append(str(m)); unreal.log("[Office80s] " + str(m))
MAZE = {"seed": 2074, "wv": [[1, 2], [1, 3], [1, 5], [1, 6], [1, 8], [1, 11], [2, 1], [2, 2], [2, 3], [2, 4], [2, 7], [2, 9], [2, 10], [3, 1], [3, 3], [3, 5], [3, 8], [3, 9], [3, 10], [4, 0], [4, 4], [4, 5], [4, 6], [4, 9], [4, 10], [4, 11]], "wh": [[0, 1], [0, 4], [0, 8], [1, 2], [1, 7], [1, 9], [1, 10], [2, 1], [2, 5], [2, 6], [2, 7], [2, 8], [3, 2], [3, 3], [3, 4], [3, 7], [3, 8], [4, 3]], "path": [[0, 3], [0, 2], [0, 1], [1, 1], [1, 0], [2, 0], [3, 0], [3, 1], [4, 1], [4, 2], [3, 2], [2, 2], [2, 3], [2, 4], [3, 4], [3, 5], [3, 6], [2, 6], [1, 6], [1, 5], [1, 4], [0, 4], [0, 5], [0, 6], [0, 7], [1, 7], [1, 8], [2, 8], [2, 9], [2, 10], [2, 11], [3, 11], [3, 10], [3, 9], [3, 8], [4, 8], [4, 9], [4, 10]], "COLS": 5, "ROWS": 12, "X0": 4955.0, "X1": 6240.0, "YT": -2903.0, "YB": -5796.0}
X0, X1, YT, YB, COLS, ROWS = MAZE["X0"], MAZE["X1"], MAZE["YT"], MAZE["YB"], MAZE["COLS"], MAZE["ROWS"]
CW, CH = (X1 - X0) / COLS, (YT - YB) / ROWS
ROOM = (4945, -5805, 6250, -2895)   # x0, y0, x1, y1
CLEAR = ("FileCabinet4_005", "FileCabinet4_006", "SnakePlant_006", "SnakePlant_007", "FileBank_011", "FileBank_012", "FileBank_013")

def imp(name):
    dest = "/Game/Office80s/Props/Maze/" + name
    t = unreal.AssetImportTask()
    t.filename = os.path.join(here, name + ".glb"); t.destination_path = dest
    t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t])
    for p in unreal.EditorAssetLibrary.list_assets(dest, recursive=True):
        x = unreal.load_asset(p)
        if isinstance(x, unreal.StaticMesh):
            unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).remove_collisions(x)
            unreal.EditorAssetLibrary.save_loaded_asset(x)
            return x
    raise RuntimeError("import failed " + name)

def main():
    piles = [imp("SM_80s_ChairPile_" + k) for k in "ABC"]
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    n_walls = 0
    with unreal.ScopedEditorTransaction("Chair maze"):
        old = [a for a in sub.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]
        if old:
            sub.destroy_actors(old)
        # the floating chairs and the props along the east wall go
        gone = []
        for a in sub.get_all_level_actors():
            l = a.get_actor_location()
            if not (ROOM[0] < l.x < ROOM[2] and ROOM[1] < l.y < ROOM[3]):
                continue
            mesh = ""
            if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
                mesh = a.static_mesh_component.static_mesh.get_name()
            if mesh == "SM_OfficeChair80s" or a.get_actor_label() in CLEAR:
                gone.append(a)
        log("removing %d chairs/props: %s" % (len(gone), sorted(a.get_actor_label() for a in gone)))
        sub.destroy_actors(gone)

        k = [0]
        def wall(cx, cy, length, along_y, label):
            k[0] += 1
            yaw = 90.0 if along_y else 0.0
            if k[0] % 2:
                yaw += 180.0
            p = sub.spawn_actor_from_object(piles[k[0] % 3], unreal.Vector(cx, cy, 20.0), unreal.Rotator(0, 0, yaw))
            p.set_actor_scale3d(unreal.Vector((length + 12.0) / 224.0, 1.0, 1.0))
            c = p.static_mesh_component
            c.set_mobility(unreal.ComponentMobility.STATIC)
            c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            p.set_actor_label("ChairPile_" + label); p.set_folder_path(FOLDER)
            b = sub.spawn_actor_from_object(cube, unreal.Vector(cx, cy, 160.0), unreal.Rotator(0, 0, 90.0 if along_y else 0.0))
            b.set_actor_scale3d(unreal.Vector((length + 50.0) / 100.0, 0.9, 2.8))
            bc = b.static_mesh_component
            bc.set_mobility(unreal.ComponentMobility.STATIC)
            bc.set_collision_profile_name("BlockAll")
            bc.set_editor_property("visible", False)
            b.set_actor_hidden_in_game(True)
            b.set_actor_label("ChairPileBlock_" + label); b.set_folder_path(FOLDER + "/Blockers")

        for c, r in MAZE["wv"]:      # wall on the west side of cell (c, r), runs along Y
            wall(X0 + c * CW, YT - (r + 0.5) * CH, CH, True, "V%d_%d" % (c, r)); n_walls += 1
        for c, r in MAZE["wh"]:      # wall on the north side of cell (c, r), runs along X
            wall(X0 + (c + 0.5) * CW, YT - r * CH, CW, False, "H%d_%d" % (c, r)); n_walls += 1
        # close the lower half of the hallway doorway (the maze entrance is the cell above it)
        wall(X0, YT - 4.5 * CH, CH, True, "DoorBlock"); n_walls += 1
        # barricade the outside double door in the south wall
        for c in (0, 1):
            wall(X0 + (c + 0.5) * CW, YB + 48.0, CW, False, "OutsideDoor%d" % c); n_walls += 1

        # the trash bag waits in the far cell, under a dim red light
        gx, gy = X0 + (MAZE["path"][-1][0] + 0.5) * CW, YT - (MAZE["path"][-1][1] + 0.5) * CH
        for a in sub.get_all_level_actors():
            if a.get_actor_label() == "BP_TrashBag4":
                a.modify(); z = a.get_actor_location().z
                a.set_actor_location(unreal.Vector(gx, gy, z), False, True)
                log("BP_TrashBag4 moved to %.0f, %.0f" % (gx, gy))
        lt = sub.spawn_actor_from_class(unreal.PointLight, unreal.Vector(gx, gy, 330.0))
        pl = lt.point_light_component
        pl.set_mobility(unreal.ComponentMobility.MOVABLE)
        pl.set_editor_property("intensity", 6.0)
        pl.set_editor_property("light_color", unreal.Color(r=255, g=60, b=40, a=255))
        pl.set_editor_property("attenuation_radius", 520.0)
        lt.set_actor_label("ChairMaze_GoalLight"); lt.set_folder_path(FOLDER)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("chair maze: %d walls, solution %d cells" % (n_walls, len(MAZE["path"])))

try:
    main()
except Exception:
    import traceback
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "chair_maze.log"), "w").write("\n".join(LOG))
