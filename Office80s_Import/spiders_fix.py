"""1) Move the 5 quest-spider spawn spots in BP_TaskHUD to the most open floor nearby (same room, clear line from old spot), scale 0.65 -> 1.0
   2) Delete the 7 decorative spider props (BigSpider_1-3, DanglingSpider_1-4). Webs / cocoons / egg sacs stay.
   3) W_MonsterTalk back button: 'Cower' and 'Fuck off' -> 'Continue'."""
import unreal, os, math, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary; EAL = unreal.EditorAssetLibrary
L = []
def log(m): L.append(str(m)); unreal.log("[Spiders] " + str(m))
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
VIS = unreal.TraceTypeQuery.TRACE_TYPE_QUERY1
def hit(a, b):
    r = unreal.SystemLibrary.line_trace_single(world, a, b, VIS, False, [], unreal.DrawDebugTrace.NONE, True)
    if isinstance(r, tuple): r = r[-1] if r and not isinstance(r[0], bool) else (r[1] if len(r) > 1 and r[0] else None)
    if r is None: return None
    t = r.to_tuple()
    if not t[0]: return None
    loc = t[4]
    return math.sqrt((loc.x - a.x) ** 2 + (loc.y - a.y) ** 2 + (loc.z - a.z) ** 2)
def free_dist(p, z, length=500.0):
    tot = 0.0; mn = 1e9
    for k in range(16):
        ang = k * math.pi / 8
        a = unreal.Vector(p.x, p.y, z); b = unreal.Vector(p.x + math.cos(ang) * length, p.y + math.sin(ang) * length, z)
        d = hit(a, b)
        d = length if d is None else d
        tot += d; mn = min(mn, d)
    return tot / 16.0, mn
def floor_z(x, y, zguess):
    d = hit(unreal.Vector(x, y, zguess + 120), unreal.Vector(x, y, zguess - 200))
    return None if d is None else zguess + 120 - d
try:
    # ---------------- 1) spider spots
    hud = unreal.load_asset("/Game/TaskSystem/BP_TaskHUD")
    ed = BGE.get_graph_editor(BEL.find_event_graph(hud))
    mts = []
    for n in ed.list_all_nodes():
        if str(BEL.get_node_title(n)).startswith("MakeTransform"):
            lp = BEL.find_input_pin(n, "Location"); sp = BEL.find_input_pin(n, "Scale")
            if lp and sp and "0.65" in str(PIN.get_pin_value(sp)):
                outs = [PIN.get_owning_node(q) for p in BEL.list_all_pins(n, unreal.EdGraphPinDirection.EGPD_OUTPUT) for q in PIN.list_connected_pins(p)]
                if any("BP_QuestSpider" in str(PIN.get_pin_value(BEL.find_input_pin(o, "ActorClass")) or "") for o in outs if BEL.find_input_pin(o, "ActorClass")):
                    mts.append((n, lp, sp))
    log("spider spawn transforms found: %d" % len(mts))
    if len(mts) != 5: raise RuntimeError("expected 5 spider spawns, stopping without changes")
    for n, lp, sp in mts:
        v = str(PIN.get_pin_value(lp))  # (X=..,Y=..,Z=..)
        d = dict(kv.split("=") for kv in v.strip("()").split(","))
        ox, oy, oz = float(d["X"]), float(d["Y"]), float(d["Z"])
        o = unreal.Vector(ox, oy, oz)
        o_avg, o_min = free_dist(o, oz + 40)
        best = (o_avg + 0.5 * o_min, ox, oy, o_avg, o_min)
        for r in (80, 160, 240, 320, 400):
            for k in range(16):
                ang = k * math.pi / 8
                cx, cy = ox + math.cos(ang) * r, oy + math.sin(ang) * r
                if hit(unreal.Vector(ox, oy, oz + 40), unreal.Vector(cx, cy, oz + 40)) is not None: continue   # wall/desk in the way
                if hit(unreal.Vector(ox, oy, oz + 160), unreal.Vector(cx, cy, oz + 160)) is not None: continue
                fz = floor_z(cx, cy, oz)
                if fz is None or abs(fz - (oz - 1)) > 25: continue                                              # same floor height
                if hit(unreal.Vector(cx, cy, oz + 40), unreal.Vector(cx, cy, oz + 260)) is not None: continue    # nothing right above (desk top)
                a_, m_ = free_dist(unreal.Vector(cx, cy, 0), oz + 40)
                if m_ < 90: continue                                                                             # not tucked against anything
                score = a_ + 0.5 * m_
                if score > best[0]: best = (score, cx, cy, a_, m_)
        nx, ny = round(best[1]), round(best[2])
        log("spider (%d,%d,%d) open avg %.0f min %.0f  ->  (%d,%d) open avg %.0f min %.0f" % (ox, oy, oz, o_avg, o_min, nx, ny, best[3], best[4]))
        PIN.set_pin_value(lp, "(X=%d,Y=%d,Z=%d)" % (nx, ny, int(oz)))
        PIN.set_pin_value(sp, "(X=1.0,Y=1.0,Z=1.0)")
    BEL.compile_blueprint(hud)
    errs = list(ed.list_nodes_with_errors())
    log("HUD compile errors: %d" % len(errs))
    if errs: raise RuntimeError("HUD has compile errors, not saving")
    log("HUD saved: %s" % EAL.save_loaded_asset(hud))

    # ---------------- 3) Continue buttons
    w = unreal.load_asset("/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk")
    wed = BGE.get_graph_editor(BEL.find_event_graph(w))
    sel = [n for n in wed.list_all_nodes() if str(BEL.get_node_title(n)).startswith("SelectString")
           and "Cower" in str(PIN.get_pin_value(BEL.find_input_pin(n, "B")))]
    log("Cower select nodes: %d" % len(sel))
    for n in sel:
        PIN.set_pin_value(BEL.find_input_pin(n, "A"), "Continue"); PIN.set_pin_value(BEL.find_input_pin(n, "B"), "Continue")
        log("now A=%s B=%s" % (PIN.get_pin_value(BEL.find_input_pin(n, "A")), PIN.get_pin_value(BEL.find_input_pin(n, "B"))))
    BEL.compile_blueprint(w)
    log("widget compile errors: %d, saved: %s" % (len(list(wed.list_nodes_with_errors())), EAL.save_loaded_asset(w)))

    # ---------------- 2) decorative spider props
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    kill = [a for a in eas.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh
            and a.static_mesh_component.static_mesh.get_name() in ("SM_80s_SpiderBig", "SM_80s_SpiderDangle_A", "SM_80s_SpiderDangle_B")]
    log("deleting props: %s" % sorted(a.get_actor_label() for a in kill))
    if len(kill) != 7: raise RuntimeError("expected 7 spider props, found %d - not deleting" % len(kill))
    for a in kill: eas.destroy_actor(a)
    log("saved map: %s" % unreal.EditorLoadingAndSavingUtils.save_map(world, "/Game/Maps/Office"))
    log("done")
except Exception:
    log("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "spiders_fix.log"), "w").write("\n".join(L))
