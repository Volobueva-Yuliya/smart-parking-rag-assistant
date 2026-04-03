from pydantic import BaseModel
from datetime import datetime

class ConfirmedReservation(BaseModel):
    """
    Model for confirmed reservation payload for Stage 3.
    Contains details to be saved to a persistent text storage.
    """
    reservation_code: str
    first_name: str
    last_name: str
    car_number: str
    start_time: str
    end_time: str
    approval_time: datetime
