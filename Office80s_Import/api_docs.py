import unreal, os
here = os.path.dirname(os.path.abspath(__file__))
out = []
B = unreal.BlueprintGraphEditor; L = unreal.BlueprintEditorLibrary; P = unreal.BlueprintGraphPinLibrary
for cls, names in ((B, ["create_and_edit_function_graph", "add_graph_input_parameter", "add_graph_output_parameter", "add_return_node",
                        "find_graph_entry_pin", "add_local_variable", "get_graph_editor_by_name", "create_node_from_name",
                        "add_get_local_variable_node", "add_set_local_variable_node", "list_available_nodes", "add_member_variable"]),
                   (L, ["add_function_graph", "find_graph", "get_object_reference_type", "add_member_variable", "set_node_pos"]),
                   (P, [a for a in dir(P) if not a.startswith("_")])):
    for n in names:
        f = getattr(cls, n, None)
        out.append("=== %s.%s\n%s" % (cls.__name__, n, (f.__doc__ or "")[:700] if f else "MISSING"))
open(os.path.join(here, "api_docs.log"), "w").write("\n".join(out))
