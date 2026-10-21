"""Tests for screen_red_flags emergency screener.

Verifies detection of configured emergency warning patterns, handling of
normal non-urgent symptoms, empty/malformed inputs, and mandatory disclaimer presence.
All patient scenarios are synthetic.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure apps/agent root is in sys.path
_agent_root = str(Path(__file__).resolve().parent.parent)
if _agent_root not in sys.path:
    sys.path.insert(0, _agent_root)

from src.models import RedFlagResult
from src.red_flags import screen_red_flags


def test_empty_and_malformed_inputs() -> None:
    """Empty, whitespace, or non-string inputs should not trigger emergency flags."""
    res_empty = screen_red_flags("")
    assert not res_empty.is_emergency
    assert res_empty.matched_indicators == []
    assert res_empty.disclaimer != ""

    res_whitespace = screen_red_flags("   \n\t  ")
    assert not res_whitespace.is_emergency
    assert res_whitespace.matched_indicators == []

    res_none = screen_red_flags(None)
    assert not res_none.is_emergency


def test_non_urgent_synthetic_presentations() -> None:
    """Non-emergency complaints should pass without emergency flags."""
    scenarios = [
        "I have had a mild headache for 2 days after staring at my computer screen.",
        "Routine checkup for blood pressure medication refill.",
        "Mild knee pain after jogging yesterday in the park.",
        "Dry cough for 3 days without fever or difficulty breathing.",
    ]
    for text in scenarios:
        res = screen_red_flags(text)
        assert not res.is_emergency, f"False positive on non-emergency: {text}"
        assert len(res.matched_indicators) == 0
        assert "Rule-based safety screening only" in res.disclaimer


def test_cardiac_red_flags() -> None:
    """Crushing chest pain and radiating chest pressure must trigger emergency alerts."""
    scenarios = [
        "I have crushing chest pain and shortness of breath for the last 30 minutes.",
        "Severe chest pressure with pain radiating to left arm and jaw.",
        "Experiencing tightness in my chest and difficulty breathing while sweating cold.",
    ]
    for text in scenarios:
        res = screen_red_flags(text)
        assert res.is_emergency, f"Failed to trigger on cardiac red flag: {text}"
        assert any("ACUTE_CHEST_PAIN_CARDIAC" in ind for ind in res.matched_indicators)
        assert "CRITICAL EMERGENCY ALERT" in res.safety_message
        assert "SEEK IMMEDIATE EMERGENCY MEDICAL CARE" in res.suggested_action


def test_stroke_red_flags() -> None:
    """Sudden facial droop, one-sided weakness, or speech loss must trigger emergency alerts."""
    scenarios = [
        "My mother suddenly has a facial droop and cannot speak clearly.",
        "Sudden weakness on one side of my body and slurred speech since 10 minutes ago.",
        "Suddenly unable to move my right arm and slurred speech.",
    ]
    for text in scenarios:
        res = screen_red_flags(text)
        assert res.is_emergency, f"Failed to trigger on stroke red flag: {text}"
        assert any("ACUTE_STROKE_SIGNS" in ind for ind in res.matched_indicators)
        assert "emergency" in res.suggested_action.lower()


def test_respiratory_distress_red_flags() -> None:
    """Severe acute respiratory distress and cyanosis must trigger emergency alerts."""
    scenarios = [
        "Patient is gasping for air and has blue lips.",
        "I can't breathe and cannot catch my breath at all.",
        "Severe stridor and unable to speak in sentences.",
    ]
    for text in scenarios:
        res = screen_red_flags(text)
        assert res.is_emergency, f"Failed to trigger on respiratory red flag: {text}"
        assert any("SEVERE_RESPIRATORY_DISTRESS" in ind for ind in res.matched_indicators)


def test_anaphylaxis_red_flags() -> None:
    """Airway swelling and anaphylactic symptoms must trigger emergency alerts."""
    scenarios = [
        "Swelling of tongue and throat closing after eating peanuts.",
        "Hives and difficulty breathing with swollen lips.",
        "Experiencing anaphylaxis after bee sting.",
    ]
    for text in scenarios:
        res = screen_red_flags(text)
        assert res.is_emergency, f"Failed to trigger on anaphylaxis red flag: {text}"
        assert any("ANAPHYLAXIS_SIGNS" in ind for ind in res.matched_indicators)


def test_hemorrhage_and_crisis_red_flags() -> None:
    """Coughing blood, profuse bleeding, or suicidal intent must trigger emergency alerts."""
    hemorrhage_text = "Coughing up large amounts of blood and feeling faint."
    res_hem = screen_red_flags(hemorrhage_text)
    assert res_hem.is_emergency
    assert any("SEVERE_HEMORRHAGE" in ind for ind in res_hem.matched_indicators)

    crisis_text = "I am in crisis and want to kill myself."
    res_crisis = screen_red_flags(crisis_text)
    assert res_crisis.is_emergency
    assert any("CRISIS_SELF_HARM" in ind for ind in res_crisis.matched_indicators)


def test_disclaimer_always_present() -> None:
    """The safety disclaimer stating this is rule-based and not exhaustive must always be present."""
    res_pos = screen_red_flags("Crushing chest pain and gasping for air.")
    res_neg = screen_red_flags("Feeling mildly tired today.")
    assert "absence of a detected warning pattern does not rule out a medical emergency" in res_pos.disclaimer
    assert "absence of a detected warning pattern does not rule out a medical emergency" in res_neg.disclaimer
