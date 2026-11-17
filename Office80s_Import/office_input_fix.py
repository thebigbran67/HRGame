"""Office Level Blueprint: on BeginPlay set Input Mode Game Only and hide the mouse cursor, so control comes back
after arriving from the main menu (which sets UI Only). Keeps anything already hooked to BeginPlay (runs after)."""
import unreal, os, traceback
here = os.path.dirname(os.path.abspath(__file__))
BEL = unreal.BlueprintEditorLibrary; BGE = unreal.BlueprintGraphEditor; PIN = unreal.BlueprintGraphPinLibrary
LOG = []
def log(m): LOG.append(str(m)); unreal.log("[Office80s] " + str(m))
try:
    lsb = unreal.load_object(None, "/Game/Maps/Office.Office:PersistentLevel.Office")
    ed = BGE.get_graph_editor(BEL.find_event_graph(lsb))
    nodes = list(ed.list_all_nodes())
    if any("SetInputMode_GameOnly" in str(BEL.get_node_title(n)) or "Game Only" in str(BEL.get_node_title(n)) for n in nodes):
        log("already has Set Input Mode Game Only - nothing to do")
    else:
        bp = None
        for n in nodes:
            if isinstance(n, unreal.K2Node_Event) and "BeginPlay" in str(BEL.get_node_title(n)).replace(" ", ""):
                bp = n
        if bp is None:
            bp = BEL.add_event_override(lsb, "ReceiveBeginPlay", unreal.IntPoint(0, 0))
            log("added BeginPlay")
        then = BEL.find_output_pin(bp, "then")
        old_next = list(PIN.list_connected_pins(then))
        PIN.break_pin_links(then)
        p = BEL.get_node_pos(bp)
        def at(n, dx, dy): BEL.set_node_pos(n, unreal.IntPoint(p.x + dx, p.y + dy)); return n
        pc = at(ed.add_call_function_node("/Script/Engine.GameplayStatics:GetPlayerController"), 250, 250)
        gm = at(ed.add_call_function_node("/Script/UMG.WidgetBlueprintLibrary:SetInputMode_GameOnly"), 300, 0)
        sc = at(ed.add_set_member_variable_node("bShowMouseCursor", "/Script/Engine.PlayerController"), 650, 0)
        ok = [PIN.try_create_connection(then, BEL.find_input_pin(gm, "execute")),
              PIN.try_create_connection(BEL.find_output_pin(pc, "ReturnValue"), BEL.find_input_pin(gm, "PlayerController")),
              PIN.try_create_connection(BEL.find_output_pin(gm, "then"), BEL.find_input_pin(sc, "execute")),
              PIN.try_create_connection(BEL.find_output_pin(pc, "ReturnValue"), BEL.find_input_pin(sc, "self"))]
        PIN.set_pin_value(BEL.find_input_pin(sc, "bShowMouseCursor"), "false")
        for q in old_next:
            ok.append(PIN.try_create_connection(BEL.find_output_pin(sc, "then"), q))
        log("links ok: %s (kept %d existing BeginPlay links)" % (ok, len(old_next)))
        ed.add_comment_node("Coming from the main menu leaves input in UI Only mode - give control back to the player",
                            unreal.Vector2D(p.x - 40, p.y - 80), unreal.Vector2D(1000, 420))
    BEL.compile_blueprint(lsb)
    errs = list(ed.list_nodes_with_errors()); log("compile errors: %d" % len(errs))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    log("open map: %s" % world.get_path_name())
    if "/Game/Maps/Office" in world.get_path_name():
        log("saved map: %s" % unreal.EditorLoadingAndSavingUtils.save_map(world, "/Game/Maps/Office"))
    else:
        log("Office isn't the open map, saving its package")
        unreal.EditorAssetLibrary.save_asset("/Game/Maps/Office")
except Exception:
    log("EXCEPTION " + traceback.format_exc())
finally:
    open(os.path.join(here, "office_input_fix.log"), "w").write("\n".join(LOG))
