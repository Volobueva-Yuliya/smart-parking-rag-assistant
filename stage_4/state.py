from typing import TypedDict, Optional, Dict, Any

class GraphState(TypedDict):
    """
    Represents the state of the Stage 4 orchestration graph.
    """
    user_message: str
    intent: Optional[str]            # info | booking | greeting | out_of_scope | sensitive | unknown
    reservation_data: Optional[Dict[str, Any]]
    
    # Specific fields for Stage 3 export
    first_name: Optional[str]
    last_name: Optional[str]
    car_number: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    approval_time: Optional[str]
    
    reservation_code: Optional[str]
    admin_decision: Optional[str]    # approved | rejected
    export_result: Optional[Dict[str, Any]]
    response: Optional[str]
    status: str                      # processing | completed | error | exported | skipped
    error: Optional[str]
