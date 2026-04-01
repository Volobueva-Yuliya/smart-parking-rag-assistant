from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional
import sqlite3
from stage_2.db import get_reservation_by_code, update_reservation_status

app = FastAPI(title="Admin Reservation API", description="Minimal API for parking reservation approvals")

# Pydantic models for request/response validation
class DecisionRequest(BaseModel):
    decision: str = Field(..., description="The decision for the reservation: 'approved' or 'rejected'")
    comment: Optional[str] = Field(None, description="Optional administrative comment")

    @validator("decision")
    def validate_decision(cls, v):
        if v not in ["approved", "rejected"]:
            raise ValueError("decision must be either 'approved' or 'rejected'")
        return v

@app.get("/admin/reservation/{reservation_code}")
async def get_reservation(reservation_code: str):
    """
    Retrieves full reservation data by its unique code.
    
    Example response:
    {
        "id": 1,
        "reservation_code": "R-20260401-001",
        "first_name": "Lila",
        "last_name": "Ivanova",
        "vehicle_plate": "SDS-100",
        "status": "pending_admin_approval",
        ...
    }
    """
    try:
        reservation = get_reservation_by_code(reservation_code)
        if not reservation:
            raise HTTPException(status_code=404, detail=f"Reservation {reservation_code} not found")
        return reservation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/admin/reservation/{reservation_code}/decision")
async def update_reservation(reservation_code: str, request: DecisionRequest):
    """
    Updates the status of a reservation based on admin decision.
    
    Example request body:
    {
        "decision": "approved",
        "comment": "Slot confirmed"
    }
    """
    try:
        # Business logic: Check if reservation exists first
        reservation = get_reservation_by_code(reservation_code)
        if not reservation:
            raise HTTPException(status_code=404, detail=f"Reservation {reservation_code} not found")

        # Update the status in DB
        success = update_reservation_status(
            reservation_code, 
            request.decision, 
            comment=request.comment
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update reservation status in DB")
            
        # Return the updated reservation
        updated_reservation = get_reservation_by_code(reservation_code)
        return updated_reservation
        
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Example usage and testing:
# --------------------------
# To run the server:
# uvicorn stage_2.admin_api:app --reload --port 8000
#
# Testing with curl:
# 1. Get reservation:
#    curl -X GET http://localhost:8000/admin/reservation/R-20260401-001
#
# 2. Approve reservation:
#    curl -X POST http://localhost:8000/admin/reservation/R-20260401-001/decision \
#         -H "Content-Type: application/json" \
#         -d '{"decision": "approved", "comment": "Verified"}'
#
# 3. Reject reservation:
#    curl -X POST http://localhost:8000/admin/reservation/R-20260401-001/decision \
#         -H "Content-Type: application/json" \
#         -d '{"decision": "rejected", "comment": "No capacity"}'
