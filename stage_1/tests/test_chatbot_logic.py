import pytest
from datetime import datetime, timedelta
from app.chatbot import validate_name, validate_car_number, validate_datetime, validate_times, BookingState

def test_validate_name():
    assert validate_name("John")[0] is True
    assert validate_name("J")[0] is False
    assert validate_name("John123")[0] is False

def test_validate_car_number():
    assert validate_car_number("ABC-123")[0] is True
    assert validate_car_number("A")[0] is False

def test_validate_datetime():
    future_dt = (datetime.now() + timedelta(days=1)).isoformat(timespec='seconds')
    past_dt = (datetime.now() - timedelta(days=1)).isoformat(timespec='seconds')
    
    assert validate_datetime(future_dt)[0] is True
    assert validate_datetime(past_dt)[0] is False
    assert validate_datetime("invalid")[0] is False

def test_validate_times():
    base_time = datetime.now() + timedelta(days=1)
    start_time = base_time.isoformat(timespec='seconds')
    end_time = (base_time + timedelta(hours=1)).isoformat(timespec='seconds')
    earlier_time = (base_time - timedelta(hours=1)).isoformat(timespec='seconds')

    assert validate_times(start_time, end_time)[0] is True
    assert validate_times(end_time, start_time)[0] is False
    assert validate_times(start_time, earlier_time)[0] is False

def test_booking_state_reset():
    state = BookingState()
    state.active = True
    state.booking_data = {"name": "John"}
    state.reset()
    assert state.active is False
    assert state.booking_data == {}
