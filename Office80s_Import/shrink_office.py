"""Shrink the main office floor: slide the south partition north and the east partition west.
The rooms behind those walls get bigger. Everything attached to the walls (trim, doors, casings,
headers, wall decor) moves with them, and the perpendicular room walls are stretched to meet.
One undo step (Ctrl+Z) reverts it all."""
import unreal

DS = 700.0    # south wall moves north (+Y) by this much
DE = 300.0    # east wall moves west (-X) by this much
TAG = "o80s_shrunk"

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def log(m): unreal.log("[Office80s] " + m)
SKIP_CLS = ("RectLight", "PointLight", "SpotLight", "PostProcessVolume", "LocalFogVolume", "GroupActor",
            "WorldDataLayers", "WorldPartitionMiniMap", "SkyLight", "SkyAtmosphere", "DirectionalLight",
            "VolumetricCloud")

def bb(a):
    o, e = a.get_actor_bounds(False)
    return [o.x - e.x, o.y - e.y, o.z - e.z, o.x + e.x, o.y + e.y, o.z + e.z]

def shift(a, dx, dy):
    a.modify()
    p = a.get_actor_location()
    a.set_actor_location(unreal.Vector(p.x + dx, p.y + dy, p.z), False, False)

def set_extent(a, axis, lo, hi):
    """Scale an (axis-aligned-ish) actor so its world bounds along axis (0=x, 1=y) span lo..hi."""
    a.modify()
    b = bb(a)
    cur = b[3 + axis] - b[axis]
    f, r = a.get_actor_forward_vector(), a.get_actor_right_vector()
    fx = abs(f.x if axis == 0 else f.y)
    rx = abs(r.x if axis == 0 else r.y)
    s = a.get_actor_scale3d()
    k = (hi - lo) / cur
    if fx >= rx:
        a.set_actor_scale3d(unreal.Vector(s.x * k, s.y, s.z))
    else:
        a.set_actor_scale3d(unreal.Vector(s.x, s.y * k, s.z))
    b = bb(a)
    if axis == 0:
        shift(a, lo - b[0], 0)
    else:
        shift(a, 0, lo - b[1])

def mirror_door(a, axis, c):
    """Swing an open door leaf to the other side of a wall whose centre line is at c."""
    a.modify()
    p, rot = a.get_actor_location(), a.get_actor_rotation()
    if axis == 0:   # wall runs along Y, centre x = c
        a.set_actor_location(unreal.Vector(2 * c - p.x, p.y, p.z), False, False)
        a.set_actor_rotation(unreal.Rotator(0, 0, -rot.yaw), False)
    else:           # wall runs along X, centre y = c
        a.set_actor_location(unreal.Vector(p.x, 2 * c - p.y, p.z), False, False)
        a.set_actor_rotation(unreal.Rotator(0, 0, 180.0 - rot.yaw), False)

actors = [a for a in sub.get_all_level_actors() if a.get_class().get_name() not in SKIP_CLS]
if any(TAG in [str(t) for t in a.get_editor_property("tags")] for a in actors):
    raise RuntimeError("office already shrunk; undo first if you want to re-run")
by_label = {a.get_actor_label(): a for a in actors}

south_move, south_stretch, se_door, east_move, east_stretch = [], [], [], [], []
for a in actors:
    lab = a.get_actor_label()
    if a.get_class().get_name().startswith("BP_"):
        continue
    b = bb(a)
    if b[2] > 900 or (b[3] - b[0] > 5000 and b[4] - b[1] > 5000):
        continue                                          # ceiling stuff, floor, ceiling slab
    cx, cy = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
    lx, ly = b[3] - b[0], b[4] - b[1]
    folder = str(a.get_folder_path())
    # south partition (y ~ -3790..-3723) and everything hanging on it
    if b[4] > -3830 and b[1] < -3690 and 2090 < cx < 5500 and ly < 600:
        south_move.append(a); continue
    # room walls running south from that partition (and their trim) get longer
    if -3800 < b[4] < -3440 and b[1] < -4500 and 3400 < cx < 5600 and lx < 120:
        south_stretch.append(a); continue
    # the doorway on the east wall into the south-east room slides north with it
    if folder.startswith("Office80s/Doors") and b[1] > -3480 and b[4] < -3025 and b[3] > 5250 and b[0] < 5550:
        se_door.append(a); continue
    # east partition between the south-east room and the conference room
    if b[3] > 5455 and b[0] < 5540 and -2165 < cy < 1485 and lx < 600 and ly < 3000:
        east_move.append(a); continue
    # east-room dividers (and their trim) get longer toward the office
    if 5480 < b[0] < 5492 and b[3] > 6500 and -2200 < cy < 400:
        east_stretch.append(a); continue

with unreal.ScopedEditorTransaction("Shrink office floor"):
    for a in south_move:
        shift(a, 0, DS)
    for a in south_stretch:
        b = bb(a); set_extent(a, 1, b[1], b[4] + DS)
    for a in se_door:
        shift(a, 0, DS)
    # wall stub between the moved south-east doorway and the room divider
    for lab in ("SM_Cube14",):
        a = by_label[lab]; b = bb(a); set_extent(a, 1, b[1] + DS, b[4])
    for a in actors:                                       # trim on that stub
        b = bb(a)
        if str(a.get_folder_path()).startswith("Office80s/Life/") and 5470 < b[0] < 5520 and abs(b[1] + 3053) < 4 and abs(b[4] + 2150) < 4:
            set_extent(a, 1, b[1] + DS, b[4])
    a = by_label["SM_Cube212"]; b = bb(a); set_extent(a, 1, b[1] + DS, -2150.0)
    if "FileCabinet4_002" in by_label:
        shift(by_label["FileCabinet4_002"], 0, -300)
    for a in east_move:
        shift(a, -DE, 0)
    for a in east_stretch:
        b = bb(a); set_extent(a, 0, b[0] - DE, b[3])
    # doors that used to swing into the office now swing into their rooms
    for lab, axis, c in (("RoomDoor_05", 1, -3757.0 + DS), ("RoomDoor_10", 0, 5500.0 - DE),
                         ("RoomDoor_11", 0, 5500.0 - DE), ("RoomDoor_13", 0, 5490.0 - DE)):
        if lab in by_label:
            mirror_door(by_label[lab], axis, c)
    m = by_label["SM_Cube213"]
    m.set_editor_property("tags", list(m.get_editor_property("tags")) + [unreal.Name(TAG)])

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
log("shrink: south moved %d, stretched %d, SE door %d, east moved %d, stretched %d; still unsaved: %d"
    % (len(south_move), len(south_stretch), len(se_door), len(east_move), len(east_stretch), len(left)))
