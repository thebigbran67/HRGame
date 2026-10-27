"""Shrink the WHOLE Office building toward the entrance corner (walls, rooms, trim, doors, ceiling, floor),
keeping furniture full size and in place inside each room. Uses shrink2_core.py next to this file.
One undo step (Edit > Undo) reverts it."""
import os, sys, unreal
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import importlib, shrink2_core
importlib.reload(shrink2_core)

SX, SY = 0.88, 0.80
AX, AY = 680.0, -5820.0
TAG = "o80s_shrunk2"
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def log(m): unreal.log("[Office80s] " + m)

actors, recs = [], []
for a in sub.get_all_level_actors():
    if a.get_attach_parent_actor():
        continue
    o, e = a.get_actor_bounds(False)
    r = {"label": a.get_actor_label(), "cls": a.get_class().get_name(), "folder": str(a.get_folder_path()),
         "loc": [a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z],
         "yaw": a.get_actor_rotation().yaw,
         "bmin": [o.x - e.x, o.y - e.y, o.z - e.z], "bmax": [o.x + e.x, o.y + e.y, o.z + e.z], "mesh": ""}
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        r["mesh"] = a.static_mesh_component.static_mesh.get_path_name()
    if TAG in [str(t) for t in a.get_editor_property("tags")]:
        raise RuntimeError("already shrunk; undo first to re-run")
    actors.append(a); recs.append(r)

kinds, ops, walls, cinfo = shrink2_core.plan(recs, SX, SY, AX, AY)

def bb(a):
    o, e = a.get_actor_bounds(False)
    return [o.x - e.x, o.y - e.y, o.x + e.x, o.y + e.y]

def shift(a, dx, dy):
    p = a.get_actor_location()
    a.set_actor_location(unreal.Vector(p.x + dx, p.y + dy, p.z), False, False)

def world_axis_local(a, axis):
    f, r = a.get_actor_forward_vector(), a.get_actor_right_vector()
    fx = abs(f.x if axis == 0 else f.y); rx = abs(r.x if axis == 0 else r.y)
    return 0 if fx >= rx else 1

def scale_local(a, k, factor):
    s = a.get_actor_scale3d()
    v = [s.x, s.y, s.z]; v[k] *= factor
    a.set_actor_scale3d(unreal.Vector(*v))

def set_extent(a, axis, lo, hi):
    b = bb(a)
    cur = b[2 + axis] - b[axis]
    if cur < 0.01:
        return
    scale_local(a, world_axis_local(a, axis), (hi - lo) / cur)
    b = bb(a)
    if axis == 0: shift(a, lo - b[0], 0)
    else: shift(a, 0, lo - b[1])

n = {}
with unreal.ScopedEditorTransaction("Shrink whole office"):
    for i, o in ops.items():
        a = actors[i]
        a.modify()
        k = o["op"]
        n[k] = n.get(k, 0) + 1
        if k == "move":
            shift(a, o["d"][0], o["d"][1])
        elif k == "span":
            set_extent(a, o["axis"], o["lo"], o["hi"])
            shift(a, o["d"][0], o["d"][1])
        elif k == "slab":
            set_extent(a, 0, o["lo"][0], o["hi"][0])
            set_extent(a, 1, o["lo"][1], o["hi"][1])
        elif k == "door":
            m = recs[i]["mesh"]
            if "RoomDoor" in m or "GlassDoor" in m:
                scale_local(a, 1, o["s"])
            else:
                scale_local(a, world_axis_local(a, o["axis"]), o["s"])
            shift(a, o["d"][0], o["d"][1])
    for i, k in enumerate(kinds):
        if k == "slab" and "SM_Plane" in recs[i]["mesh"]:
            actors[i].set_editor_property("tags", list(actors[i].get_editor_property("tags")) + [unreal.Name(TAG)])
            break

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
log("whole office shrunk %.2f x %.2f: %s, clusters %d; still unsaved: %d" % (SX, SY, n, len(cinfo), len(left)))
