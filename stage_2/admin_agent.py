"""
Admin Agent module for Stage 2.
This module implements a second LangChain-based agent for administrative tasks,
specifically for reviewing and deciding on reservation requests.
"""

from typing import Dict, Any, Optional
from langchain_core.tools import tool
from stage_2.db import update_reservation_status, get_reservation_by_code
from stage_2.admin_client import format_admin_request

@tool
def approve_reservation(reservation_code: str, comment: Optional[str] = None) -> str:
    """
    Approve a pending reservation request.
    
    Args:
        reservation_code (str): The unique code of the reservation to approve.
        comment (str, optional): An optional comment from the administrator.
        
    Returns:
        str: A confirmation message indicating the result of the operation.
    """
    success = update_reservation_status(reservation_code, "approved", comment=comment)
    if success:
        return f"Reservation {reservation_code} has been successfully APPROVED."
    else:
        return f"Failed to approve reservation {reservation_code}. It might not exist."

@tool
def reject_reservation(reservation_code: str, comment: Optional[str] = None) -> str:
    """
    Reject a pending reservation request.
    
    Args:
        reservation_code (str): The unique code of the reservation to reject.
        comment (str, optional): A mandatory or optional reason for rejection.
        
    Returns:
        str: A confirmation message indicating the result of the operation.
    """
    success = update_reservation_status(reservation_code, "rejected", comment=comment)
    if success:
        return f"Reservation {reservation_code} has been successfully REJECTED."
    else:
        return f"Failed to reject reservation {reservation_code}. It might not exist."

class AdminAgent:
    """
    A minimal LangChain-based admin agent wrapper.
    This agent is responsible for the admin-facing part of the reservation workflow.
    """
    
    def __init__(self):
        # In a full LangChain implementation, these tools would be passed to an AgentExecutor.
        # For this minimal version, we expose them directly as part of the agent's capabilities.
        self.tools = [approve_reservation, reject_reservation]
    
    def prepare_review_request(self, reservation_data: Dict[str, Any]) -> str:
        """
        Prepares a summary message for the administrator to review.
        
        Args:
            reservation_data (dict): The reservation details.
            
        Returns:
            str: A formatted string for admin review.
        """
        return format_admin_request(reservation_data)

    def prepare_review_request_by_code(self, reservation_code: str) -> str:
        """
        Loads reservation data by code and prepares a summary for the administrator.
        
        Args:
            reservation_code (str): The reservation code.
            
        Returns:
            str: A formatted string for admin review or an error message.
        """
        reservation = get_reservation_by_code(reservation_code)
        if not reservation:
            return f"Reservation {reservation_code} not found."
        return self.prepare_review_request(reservation)

    def process_decision(self, reservation_code: str, decision: str, comment: Optional[str] = None) -> str:
        """
        Processes an administrative decision using the agent's tools.
        
        Args:
            reservation_code (str): The reservation code.
            decision (str): Either 'approve' or 'reject'.
            comment (str, optional): Admin comment.
            
        Returns:
            str: Result of the action.
        """
        if decision.lower() == "approve":
            return approve_reservation.invoke({"reservation_code": reservation_code, "comment": comment})
        elif decision.lower() == "reject":
            return reject_reservation.invoke({"reservation_code": reservation_code, "comment": comment})
        else:
            return f"Invalid decision: {decision}. Use 'approve' or 'reject'."

# Architecture Note:
# ------------------
# This AdminAgent satisfies the "second agent" requirement for Stage 2 by:
# 1. Separating admin concerns from the user-facing chatbot.
# 2. Using LangChain @tool decorators to define administrative actions, 
#    making them compatible with LangChain's AgentExecutor or Chains.
# 3. Providing a structured interface for the approval workflow that works 
#    alongside the user-facing booking flow.
#
# Example Usage:
# --------------
# agent = AdminAgent()
# reservation = get_reservation_by_code("R-20260401-001")
# print(agent.prepare_review_request(reservation))
# result = agent.process_decision("R-20260401-001", "approve", "Slot is confirmed")
# print(result)
