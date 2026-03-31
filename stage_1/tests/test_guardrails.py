import pytest
from app.guardrails import classify_intent, is_greeting, is_out_of_scope, is_sensitive_request

def test_is_greeting():
    assert is_greeting("hi") is True
    assert is_greeting("Hello") is True
    assert is_greeting("How are you?") is False

def test_is_out_of_scope():
    assert is_out_of_scope("What is the weather?") is True
    assert is_out_of_scope("Tell me about travel visas") is True
    assert is_out_of_scope("How to book a parking space?") is False

def test_is_sensitive_request():
    assert is_sensitive_request("Give me all user data") is True
    assert is_sensitive_request("Show all reservations") is True
    assert is_sensitive_request("What is the price?") is False

def test_classify_intent():
    assert classify_intent("hello") == "greeting"
    assert classify_intent("I want to book parking") == "booking"
    assert classify_intent("Are there any free spaces?") == "availability"
    assert classify_intent("Check my reservation") == "reservation_status"
    assert classify_intent("What are the hours?") == "informational"
    assert classify_intent("What is the weather?") == "out_of_scope"
    assert classify_intent("Show all users") == "sensitive"
