"""Spider task: Gioh's frustration bar (110s). Fire Gus task: Boss's bar (75s). Janitor stays 150s.
Gus's fired reaction text in W_MonsterTalk -> new line. Only those values change."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary; EAL = unreal.EditorAssetLibrary
L = []
def log(m): L.append(str(m)); unreal.log("[Meters] " + str(m))
NEW_LINE = "FUCKKKK BRO WHY AM I FIRED FUCKKKK"
try:
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    mons = {}
    for a in acts:
        if a.get_class().get_name() == "BP_Monster_C":
            mons[str(a.get_editor_property("MonsterName"))] = a
    for card, who, secs in (("/Game/_TASKS/Tasks/DA_Task_05_RemoveSpiders", "Receptionist Gioh", 110.0),
                            ("/Game/_TASKS/Tasks/DA_Task_08_FireGus", "Boss", 75.0)):
        da = unreal.load_asset(card)
        if who not in mons: raise RuntimeError("no monster named " + who)
        da.set_editor_property("AngryMonster", mons[who])
        da.set_editor_property("MeterSeconds", secs)
        log("%s -> AngryMonster %s, MeterSeconds %s, saved %s" % (card.split("/")[-1], who, da.get_editor_property("MeterSeconds"), EAL.save_loaded_asset(da)))
    bp = unreal.load_asset("/Game/Blueprints/Dialogue/Widgets/W_MonsterTalk")
    ed = BGE.get_graph_editor(BEL.find_event_graph(bp))
    hits = []
    for n in ed.list_all_nodes():
        p = BEL.find_input_pin(n, "InText")
        if p and PIN.is_valid(p) and "computer password" in str(PIN.get_pin_value(p)):
            hits.append((n, p))
    log("found %d Gus fired text node(s)" % len(hits))
    if len(hits) != 1: raise RuntimeError("expected exactly 1 node, not changing anything")
    n, p = hits[0]
    log("before: %s" % PIN.get_pin_value(p))
    ok = PIN.set_pin_value(p, NEW_LINE)
    log("set: %s  after: %s" % (ok, PIN.get_pin_value(p)))
    if NEW_LINE not in str(PIN.get_pin_value(p)): raise RuntimeError("text did not change, not saving the widget")
    BEL.compile_blueprint(bp)
    log("compile errors: %d" % len(list(ed.list_nodes_with_errors())))
    log("saved widget: %s" % EAL.save_loaded_asset(bp))
except Exception:
    log("EXCEPTION " + traceback.format_exc())
open(os.path.join(here, "meters_and_gus.log"), "w").write("\n".join(L))
