from fastapi import FastAPI, Depends, Security
from stage_3.app.auth import validate_token
from stage_3.app.models import ConfirmedReservation
from stage_3.app.service import process_confirmed_reservation, sync_approved_reservations

app = FastAPI(
    title="Stage 3: Reservation Storage Service",
    description="External service to process and store confirmed reservations."
)

@app.get("/health")
def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}

@app.post("/confirm", dependencies=[Security(validate_token)])
def confirm_reservation(reservation: ConfirmedReservation):
    """
    Endpoint for receiving confirmed reservations from other stages/services.
    Requires Bearer token authentication.
    """
    return process_confirmed_reservation(reservation)

@app.post("/sync-confirmed", dependencies=[Security(validate_token)])
def sync_confirmed():
    """
    Triggers synchronization of approved reservations from the shared SQLite database.
    Requires Bearer token authentication.
    """
    return sync_approved_reservations()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("stage_3.app.mcp_server:app", host="0.0.0.0", port=8001, reload=True)
