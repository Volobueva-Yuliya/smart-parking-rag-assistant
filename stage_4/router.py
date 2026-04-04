from .state import GraphState

def route_after_interaction(state: GraphState) -> str:
    """
    Decides whether to go to Admin Approval or directly to Final Response.
    """
    if state.get("intent") == "booking":
        return "admin_approval"
    return "final_response"

def route_after_admin(state: GraphState) -> str:
    """
    Decides whether to record data based on admin decision.
    """
    if state.get("admin_decision") == "approved":
        return "data_recording"
    return "final_response"
