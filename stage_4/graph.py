from langgraph.graph import StateGraph, END
from .state import GraphState
from .nodes import user_interaction_node, admin_approval_node, data_recording_node, final_response_node
from .router import route_after_interaction, route_after_admin

def build_workflow() -> StateGraph:
    """
    Assembles the Stage 4 orchestration graph.
    """
    workflow = StateGraph(GraphState)

    # 1. Define nodes
    workflow.add_node("user_interaction", user_interaction_node)
    workflow.add_node("admin_approval", admin_approval_node)
    workflow.add_node("data_recording", data_recording_node)
    workflow.add_node("final_response", final_response_node)

    # 2. Set entry point
    workflow.set_entry_point("user_interaction")

    # 3. Connect nodes with edges and conditional routing
    workflow.add_conditional_edges(
        "user_interaction",
        route_after_interaction,
        {
            "admin_approval": "admin_approval",
            "final_response": "final_response"
        }
    )

    workflow.add_conditional_edges(
        "admin_approval",
        route_after_admin,
        {
            "data_recording": "data_recording",
            "final_response": "final_response"
        }
    )

    workflow.add_edge("data_recording", "final_response")
    workflow.add_edge("final_response", END)

    return workflow

# Compiled application
app = build_workflow().compile()
