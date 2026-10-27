"""Remove some cubicles: clears a straight aisle from the south wall to the conference glass doors,
plus two in the north-west wing, and deletes two duplicate desks stacked on top of others.
One undo step reverts it."""
import math, unreal
TARGETS = ["Desk80s_27", "Desk80s_05", "RoundTable_002",       # south block, middle column
           "Desk80s_21", "Desk80s_24", "Desk80s_37",           # north block, middle column
           "Desk80s_46", "Desk80s_34"]                         # north-west wing
DUPES = ["Desk80s_22", "Desk80s_06"]
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def log(m): unreal.log("[Office80s] " + m)
KEEP_LIFE = ("Baseboard", "ChairRail", "Wainscot", "CeilingLight")

def ctr(a):
    o, e = a.get_actor_bounds(False)
    return (o.x, o.y), o.z - e.z

acts = sub.get_all_level_actors()
by = {}
for a in acts:
    by.setdefault(a.get_actor_label(), []).append(a)
units = [a for a in acts if str(a.get_folder_path()) == "Office80s/Desks" or
         (str(a.get_folder_path()).startswith("Office80s/CubicleFills") and not str(a.get_folder_path()).endswith("/Chair"))]
uc = {a.get_actor_label() + "#" + str(i): (a, ctr(a)[0]) for i, a in enumerate(units)}
tset = []
for t in TARGETS:
    if len(by.get(t, [])) != 1:
        raise RuntimeError("target %s not unique/found" % t)
    tset.append(by[t][0])

def nearest_unit(p):
    return min(units, key=lambda u: math.dist(ctr(u)[0], p))

kill = set()
for t in tset:
    tc = ctr(t)[0]
    kill.add(t)
    for a in acts:
        f = str(a.get_folder_path())
        ok = f == "Office80s/Cubicles" or f.startswith("Office80s/CubicleFills") or f == "Office80s/Desks" or \
             (f.startswith("Office80s/Life/") and not f.split("/")[-1] in KEEP_LIFE)
        if not ok or a.get_class().get_name().startswith("BP_"):
            continue
        p, zmin = ctr(a)
        if f == "Office80s/Cubicles":
            if math.dist(p, tc) < 220 and nearest_unit(p) is t:
                kill.add(a)
        elif math.dist(p, tc) < 185 and (a not in units or a is t):
            kill.add(a)
for dname in DUPES:
    for a in by.get(dname, []):
        kill.add(a)
with unreal.ScopedEditorTransaction("Remove some desks"):
    names = sorted(a.get_actor_label() for a in kill)
    sub.destroy_actors(list(kill))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
left = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) + list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
log("removed %d actors: %s; still unsaved: %d" % (len(names), ", ".join(names), len(left)))
