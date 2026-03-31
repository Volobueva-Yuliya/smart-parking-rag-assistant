import pytest
from app.chatbot import validate_name, validate_car_number, validate_datetime, validate_times, BookingState

def test_validate_name():
    assert validate_name("John")[0] is True
    assert validate_name("J")[0] is False
    assert validate_name("John123")[0] is False

def test_validate_car_number():
    assert validate_car_number("ABC-123")[0] is True
    assert validate_car_number("A")[0] is False

def test_validate_datetime():
    assert validate_datetime("2026-04-01T10:00:00")[0] is True
    assert validate_datetime("invalid")[0] is False

def test_validate_times():
    assert validate_times("2026-04-01T10:00:00", "2026-04-01T11:00:00")[0] is True
    assert validate_times("2026-04-01T11:00:00", "2026-04-01T10:00:00")[0] is False

def test_booking_state_reset():
    state = BookingState()
    state.active = True
    state.booking_data = {"name": "John"}
    state.reset()
    assert state.active is False
    assert state.booking_data == {}
