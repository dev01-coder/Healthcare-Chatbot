"""Tests for the emergency detection module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.safety.emergency import detect_emergency, get_disclaimer, is_advice_query


def test_no_emergency():
    result = detect_emergency("What is diabetes?")
    assert result is None


def test_no_emergency_symptoms():
    result = detect_emergency("I have a headache and runny nose")
    assert result is None


def test_cardiac_emergency():
    result = detect_emergency("I'm having chest pain and pain in my left arm")
    assert result is not None
    assert result["type"] == "cardiac"
    assert "emergency" in str(result["actions"]).lower()


def test_stroke_emergency():
    result = detect_emergency("My face is drooping and I can't speak properly")
    assert result is not None
    assert result["type"] == "stroke"


def test_breathing_emergency():
    result = detect_emergency("I can't breathe, my throat is closing")
    assert result is not None
    assert result["type"] == "breathing"


def test_suicide_emergency():
    result = detect_emergency("I want to kill myself")
    assert result is not None
    assert result["type"] == "suicide"
    assert "crisis" in str(result["actions"]).lower() or "helpline" in str(result["actions"]).lower()


def test_overdose_emergency():
    result = detect_emergency("I took too many pills")
    assert result is not None
    assert result["type"] == "overdose"


def test_unconscious_emergency():
    result = detect_emergency("He is unconscious and not responding")
    assert result is not None
    assert result["type"] == "unconscious"


def test_severe_bleeding():
    result = detect_emergency("There is severe bleeding that won't stop")
    assert result is not None
    assert result["type"] == "severe_bleeding"


def test_disclaimer_contains_warning():
    disclaimer = get_disclaimer()
    assert "educational" in disclaimer.lower()
    assert "consult" in disclaimer.lower()


def test_is_advice_query_positive():
    assert is_advice_query("What treatment should I take?")
    assert is_advice_query("Can I take ibuprofen?")
    assert is_advice_query("Is it safe to drink while on antibiotics?")
    assert is_advice_query("Recommend a good painkiller")
    assert is_advice_query("What medicine is best for cold?")


def test_is_advice_query_negative():
    assert not is_advice_query("What is diabetes?")
    assert not is_advice_query("Tell me about heart disease")
    assert not is_advice_query("Explain how insulin works")
    assert not is_advice_query("chest pain")
    assert not is_advice_query("")


if __name__ == "__main__":
    test_no_emergency()
    test_cardiac_emergency()
    test_stroke_emergency()
    test_breathing_emergency()
    test_suicide_emergency()
    test_overdose_emergency()
    test_unconscious_emergency()
    test_severe_bleeding()
    test_disclaimer_contains_warning()
    print("All emergency tests passed!")
