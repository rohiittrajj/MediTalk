"""Deterministic Emergency Red-Flag Screener for MediTalk.

Screens patient narratives for high-risk clinical presentations that require
immediate emergency medical care.

CLINICAL SAFETY MANDATES:
1. This screener is strictly rule-based and non-exhaustive.
2. The absence of a detected warning pattern NEVER rules out a medical emergency.
3. Does not provide medical diagnoses or replace emergency medical assessment.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from .models import RedFlagResult


class RedFlagRule(NamedTuple):
    indicator_id: str
    description: str
    patterns: list[re.Pattern]


# Precompiled regular expressions for emergency indicators
_RULES: list[RedFlagRule] = [
    RedFlagRule(
        indicator_id="ACUTE_CHEST_PAIN_CARDIAC",
        description="Acute or crushing chest pain/pressure, especially with shortness of breath or radiating pain",
        patterns=[
            re.compile(r"\b(crushing|heavy|tight|severe|squeezing)\s+(chest\s+pain|chest\s+pressure)\b", re.IGNORECASE),
            re.compile(r"\b(tightness|pressure|pain|discomfort)\s+(in|across)\s+(my\s+)?chest\b.*\b(shortness\s+of\s+breath|difficulty\s+breathing|dyspnea|sweating)\b", re.IGNORECASE),
            re.compile(r"\b(shortness\s+of\s+breath|difficulty\s+breathing|dyspnea|sweating)\b.*\b(tightness|pressure|pain|discomfort)\s+(in|across)\s+(my\s+)?chest\b", re.IGNORECASE),
            re.compile(r"\bchest\s+pain\b.*\b(shortness\s+of\s+breath|difficulty\s+breathing|dyspnea|sweating|arm\s+pain|jaw\s+pain)\b", re.IGNORECASE),
            re.compile(r"\b(shortness\s+of\s+breath|difficulty\s+breathing)\b.*\bchest\s+pain\b", re.IGNORECASE),
            re.compile(r"\bpain\s+(radiating|spreading)\s+to\s+(left\s+arm|jaw|back|neck)\b", re.IGNORECASE),
        ],
    ),
    RedFlagRule(
        indicator_id="ACUTE_STROKE_SIGNS",
        description="Acute neurological deficits, facial drooping, one-sided weakness, or speech impairment (FAST)",
        patterns=[
            re.compile(r"\b(facial\s+droop|face\s+droop(ing)?|droop(ing)?\s+face)\b", re.IGNORECASE),
            re.compile(r"\b(sudden\s+weakness|numbness|paralysis)\s+(in|on|of)\s+(one\s+side|arm|leg|face)\b", re.IGNORECASE),
            re.compile(r"\b(slurred\s+speech|unable\s+to\s+speak|difficulty\s+speaking|loss\s+of\s+speech)\b", re.IGNORECASE),
            re.compile(r"\bsudden(ly)?\s+(cannot|can't|unable\s+to)\s+(move|talk|see|walk)\b", re.IGNORECASE),
        ],
    ),
    RedFlagRule(
        indicator_id="SEVERE_RESPIRATORY_DISTRESS",
        description="Severe acute respiratory distress or inability to breathe",
        patterns=[
            re.compile(r"\b(can'?t\s+breathe|gasping\s+for\s+air|cannot\s+catch\s+(my\s+)?breath|suffocating)\b", re.IGNORECASE),
            re.compile(r"\b(blue|cyanotic)\s+(lips|fingers|skin|face)\b", re.IGNORECASE),
            re.compile(r"\bsevere\s+stridor\b", re.IGNORECASE),
            re.compile(r"\bunable\s+to\s+speak\s+in\s+sentences\b", re.IGNORECASE),
        ],
    ),
    RedFlagRule(
        indicator_id="ANAPHYLAXIS_SIGNS",
        description="Signs of severe acute allergic reaction or airway compromise",
        patterns=[
            re.compile(r"\b(swelling|swollen)\s+(of\s+)?(lips|tongue|throat|airway)\b", re.IGNORECASE),
            re.compile(r"\bthroat\s+(closing|closing\s+up|tightening)\b", re.IGNORECASE),
            re.compile(r"\b(anaphylaxis|anaphylactic\s+shock)\b", re.IGNORECASE),
            re.compile(r"\bhives\b.*\b(difficulty\s+breathing|throat\s+swelling)\b", re.IGNORECASE),
        ],
    ),
    RedFlagRule(
        indicator_id="SEVERE_HEMORRHAGE",
        description="Uncontrolled active hemorrhage, coughing blood, or vomiting blood",
        patterns=[
            re.compile(r"\b(coughing\s+up|vomiting)\s+(large\s+amounts\s+of\s+)?blood\b", re.IGNORECASE),
            re.compile(r"\b(uncontrolled|profuse|massive|spurting)\s+(bleeding|hemorrhage)\b", re.IGNORECASE),
        ],
    ),
    RedFlagRule(
        indicator_id="ALTERED_CONSCIOUSNESS",
        description="Loss of consciousness, unresponsiveness, or severe acute disorientation",
        patterns=[
            re.compile(r"\b(unconscious|unresponsive|passed\s+out|collapsed|loss\s+of\s+consciousness)\b", re.IGNORECASE),
            re.compile(r"\bsudden\s+(severe\s+confusion|inability\s+to\s+wake)\b", re.IGNORECASE),
        ],
    ),
    RedFlagRule(
        indicator_id="CRISIS_SELF_HARM",
        description="Active acute crisis, self-harm, or suicidal intent",
        patterns=[
            re.compile(r"\b(want\s+to\s+(kill\s+myself|end\s+my\s+life)|suicidal\s+thoughts?|plan\s+to\s+commit\s+suicide)\b", re.IGNORECASE),
            re.compile(r"\b(overdosed\s+on|poisoned)\b", re.IGNORECASE),
        ],
    ),
]


def screen_red_flags(text: str | None) -> RedFlagResult:
    """Evaluate patient narrative or text against configured emergency warning patterns.

    Args:
        text: Clinical narrative, symptom statement, or message text.

    Returns:
        RedFlagResult containing flag status, matched indicators, and urgent routing advice.
    """
    if not text or not isinstance(text, str) or not text.strip():
        return RedFlagResult(
            is_emergency=False,
            matched_indicators=[],
            safety_message="",
            suggested_action="No input provided for safety screening.",
        )

    matched_indicators: list[str] = []
    clean_text = text.strip()

    for rule in _RULES:
        for pattern in rule.patterns:
            if pattern.search(clean_text):
                matched_indicators.append(f"{rule.indicator_id}: {rule.description}")
                break  # Record rule once if matched

    if matched_indicators:
        safety_message = (
            "CRITICAL EMERGENCY ALERT: High-risk warning signs were detected in the input: "
            + "; ".join(matched_indicators)
        )
        suggested_action = (
            "SEEK IMMEDIATE EMERGENCY MEDICAL CARE. Call local emergency services (e.g., 911, "
            "112, 108) or proceed immediately to the nearest hospital emergency room. "
            "MediTalk is a preparation tool and does not provide emergency intervention or diagnosis."
        )
        return RedFlagResult(
            is_emergency=True,
            matched_indicators=matched_indicators,
            safety_message=safety_message,
            suggested_action=suggested_action,
        )

    return RedFlagResult(
        is_emergency=False,
        matched_indicators=[],
        safety_message="",
        suggested_action="No configured emergency patterns detected. Proceed with structured history intake.",
    )
