"""MediTalk Autonomous Clinical Preparation Agent — Agentverse Hosted Bundle.

Decentralized Clinical Intake and History Preparation
Repository: https://github.com/rohiittrajj/MediTalk

CLINICAL SAFETY MANDATES:
1. MediTalk does NOT autonomously diagnose, treat, or prescribe.
2. All generated summaries remain unverified drafts until reviewed and accepted by a clinician.
3. Emergency warning screening is rule-based and non-exhaustive; absence of an alert never rules out an emergency.
4. Never invent missing facts, dosages, units, or dates.
5. Preserves provenance across patient-reported, document-extracted, and clinician-entered data.
6. Explicit informed consent is mandatory prior to clinical intake.
7. Emergency state persists permanently across the entire conversation.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
import os
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union
from uuid import UUID, uuid4

# uAgents and Agent Chat Protocol (ACP) dependencies
try:
    from uagents import Agent, Context, Protocol
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement,
        ChatMessage,
        TextContent,
        chat_protocol_spec,
    )
    UAGENTS_AVAILABLE = True
except ImportError:
    UAGENTS_AVAILABLE = False

logger = logging.getLogger("meditalk.agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Default to hosted mode when running bundle on Agentverse
os.environ.setdefault("AGENTVERSE_HOSTED", "true")

# ===========================================================================
# SECTION: models.py
# ===========================================================================



from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ProvenanceType(str, Enum):
    """Source provenance classification."""
    PATIENT_REPORTED = "patient_reported"
    DOCUMENT_EXTRACTED = "document_extracted"
    CLINICIAN_ENTERED = "clinician_entered"
    GENERATED_NORMALIZED = "generated_normalized"


class ConflictSeverity(str, Enum):
    """Severity classification for clinical conflicts."""
    CRITICAL = "critical"  # e.g., allergy contradiction, conflicting dosages of narrow therapeutic index drug
    WARNING = "warning"    # e.g., conflicting dosages of standard medications, conflicting event dates
    INFORMATIONAL = "info" # e.g., minor wording variance, undated previous report


@dataclass
class ProvenanceRecord:
    """Provenance tracking for any clinical fact."""
    source_type: ProvenanceType
    source_ref: str | None = None
    extracted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_type"] = self.source_type.value
        return data


@dataclass
class RedFlagResult:
    """Outcome of emergency warning pattern screening."""
    is_emergency: bool
    matched_indicators: list[str] = field(default_factory=list)
    safety_message: str = ""
    suggested_action: str = ""
    disclaimer: str = (
        "Rule-based safety screening only. The absence of a detected warning pattern does not "
        "rule out a medical emergency. If you feel unwell or suspect an urgent medical condition, "
        "seek professional emergency medical care immediately."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MedicationFact:
    """Structured representation of a medication fact."""
    name: str
    dosage: str | None = None
    unit: str | None = None
    frequency: str | None = None
    route: str | None = None
    status: str = "active"  # active, discontinued, historical, unknown
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=ProvenanceType.PATIENT_REPORTED)
    )
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["provenance"] = self.provenance.to_dict()
        return data


@dataclass
class ConditionFact:
    """Structured representation of a diagnosed condition or symptom."""
    name: str
    status: str = "active"  # active, resolved, historical, suspect
    onset_date: str | None = None
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=ProvenanceType.PATIENT_REPORTED)
    )
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["provenance"] = self.provenance.to_dict()
        return data


@dataclass
class AllergyFact:
    """Structured representation of an allergy or adverse reaction."""
    allergen: str
    reaction: str | None = None
    severity: str | None = None  # mild, moderate, severe, anaphylaxis, unknown
    is_denied: bool = False      # e.g., "No known drug allergies" (NKDA)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=ProvenanceType.PATIENT_REPORTED)
    )
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["provenance"] = self.provenance.to_dict()
        return data


@dataclass
class LabResultFact:
    """Structured representation of a laboratory investigation."""
    test_name: str
    numeric_value: float | None = None
    string_value: str | None = None
    unit: str | None = None
    reference_range: str | None = None
    is_abnormal: bool | None = None
    test_date: str | None = None
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=ProvenanceType.DOCUMENT_EXTRACTED)
    )
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["provenance"] = self.provenance.to_dict()
        return data


@dataclass
class ClinicalConflict:
    """Conflict identified across sources or within the narrative."""
    entity_name: str
    category: str  # medication_dosage, allergy_statement, date_discrepancy, lab_unit
    description: str
    severity: ConflictSeverity
    conflicting_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass
class MissingInfoIndicator:
    """Identifies missing but clinically relevant items without fabricating values."""
    field_name: str
    context: str
    reason: str = "Not provided or missing in source text"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineEvent:
    """An event placed chronologically."""
    event_date: str | None  # ISO format string or descriptive date if partially known
    title: str
    description: str
    provenance: ProvenanceRecord

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["provenance"] = self.provenance.to_dict()
        return data


@dataclass
class ExtractionResult:
    """Aggregated result of extracting facts from input text."""
    conditions: list[ConditionFact] = field(default_factory=list)
    medications: list[MedicationFact] = field(default_factory=list)
    allergies: list[AllergyFact] = field(default_factory=list)
    lab_results: list[LabResultFact] = field(default_factory=list)
    raw_text: str = ""
    unparsed_segments: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "conditions": [c.to_dict() for c in self.conditions],
            "medications": [m.to_dict() for m in self.medications],
            "allergies": [a.to_dict() for a in self.allergies],
            "lab_results": [l.to_dict() for l in self.lab_results],
            "raw_text": self.raw_text,
            "unparsed_segments": self.unparsed_segments,
        }


@dataclass
class TimelineAndConflictResult:
    """Organized chronological timeline, detected conflicts, and missing items."""
    dated_timeline: list[TimelineEvent] = field(default_factory=list)
    undated_events: list[TimelineEvent] = field(default_factory=list)
    conflicts: list[ClinicalConflict] = field(default_factory=list)
    missing_information: list[MissingInfoIndicator] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dated_timeline": [e.to_dict() for e in self.dated_timeline],
            "undated_events": [e.to_dict() for e in self.undated_events],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "missing_information": [m.to_dict() for m in self.missing_information],
        }


@dataclass
class IntakeSession:
    """Patient intake state aggregated during the conversation."""
    session_id: str
    patient_id: str | None = None
    consent_granted: bool = False
    consent_timestamp: str | None = None
    chief_complaint: str = ""
    hpi_narrative: str = ""
    extracted_facts: ExtractionResult = field(default_factory=ExtractionResult)
    timeline_result: TimelineAndConflictResult = field(default_factory=TimelineAndConflictResult)
    red_flag_triggered: bool = False
    red_flag_details: RedFlagResult | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "consent_granted": self.consent_granted,
            "consent_timestamp": self.consent_timestamp,
            "chief_complaint": self.chief_complaint,
            "hpi_narrative": self.hpi_narrative,
            "extracted_facts": self.extracted_facts.to_dict(),
            "timeline_result": self.timeline_result.to_dict(),
            "red_flag_triggered": self.red_flag_triggered,
            "red_flag_details": self.red_flag_details.to_dict() if self.red_flag_details else None,
            "notes": self.notes,
        }


@dataclass
class ClinicalDraft:
    """Synthesized clinical preparation draft for clinician review."""
    formatted_markdown: str
    summary_status: str = "DRAFT_PENDING_CLINICIAN_REVIEW"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    fact_count: int = 0
    conflict_count: int = 0
    missing_items_count: int = 0
    has_emergency_warning: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ===========================================================================
# SECTION: red_flags.py
# ===========================================================================



import re
from typing import NamedTuple



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


# ===========================================================================
# SECTION: extractor.py
# ===========================================================================



import re
from typing import Any


# Regex patterns for clinical extraction
_DOSAGE_PATTERN = re.compile(
    r"\b(?P<dose>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|micrograms?|milligrams?|g|grams?|ml|units?|IU|tablets?|capsules?|drops?)\b",
    re.IGNORECASE,
)

_FREQUENCY_PATTERN = re.compile(
    r"\b(?P<freq>once\s+daily|twice\s+daily|three\s+times\s+daily|four\s+times\s+daily|"
    r"daily|every\s+\d+\s+hours?|at\s+bedtime|in\s+the\s+morning|as\s+needed|prn|"
    r"bid|tid|qid|qd|qhs|q8h|q6h|q12h|weekly|monthly)\b",
    re.IGNORECASE,
)

_KNOWN_DRUG_NAMES = [
    "Metformin", "Lisinopril", "Amlodipine", "Atorvastatin", "Simvastatin",
    "Losartan", "Levothyroxine", "Omeprazole", "Pantoprazole", "Paracetamol",
    "Acetaminophen", "Ibuprofen", "Aspirin", "Furosemide", "Hydrochlorothiazide",
    "Amoxicillin", "Azithromycin", "Ciprofloxacin", "Doxycycline", "Metoprolol",
    "Atenolol", "Carvedilol", "Insulin", "Glipizide", "Gabapentin", "Sertraline",
    "Escitalopram", "Albuterol", "Prednisone", "Warfarin", "Apixaban", "Rivaroxaban",
    "Cetirizine", "Loratadine", "Montelukast", "Tramadol", "Codeine", "Morphine",
]

_KNOWN_CONDITIONS = [
    "Hypertension", "High Blood Pressure", "Type 2 Diabetes", "Type 1 Diabetes",
    "Diabetes Mellitus", "Heart Failure", "Congestive Heart Failure", "Coronary Artery Disease",
    "Asthma", "COPD", "Chronic Obstructive Pulmonary Disease", "Hypothyroidism",
    "Hyperthyroidism", "GERD", "Acid Reflux", "Chronic Kidney Disease", "Depression",
    "Anxiety", "Migraine", "Osteoarthritis", "Rheumatoid Arthritis", "Dyslipidemia",
    "Hyperlipidemia", "High Cholesterol", "Stroke", "Atrial Fibrillation", "Pneumonia",
]

_ALLERGY_NEGATION_PATTERN = re.compile(
    r"\b(no\s+known\s+drug\s+allergies|no\s+known\s+allergies|nkda|nka|no\s+allergies|denies\s+allergies)\b",
    re.IGNORECASE,
)

_ALLERGY_PATTERN = re.compile(
    r"\b(?:allergic\s+to|allergy\s+to|allergy:?)\s+(?P<allergen>[A-Za-z0-9\-]+)"
    r"(?:[:,\.\-]\s*|\s+(?:causes?|reaction:?|with)\s+)?(?P<reaction>[A-Za-z0-9\s\-]+?)?"
    r"(?=(?:;|\.|\n|$|\band\b|\balso\b))",
    re.IGNORECASE,
)

_LAB_PATTERN = re.compile(
    r"\b(?P<test>[A-Za-z0-9\s\-]+?)\s*[:=]\s*(?P<val>\d+(?:\.\d+)?|\d+/\d+)\s*"
    r"(?P<unit>%|mg/dL|g/dL|mmol/L|mEq/L|mIU/L|IU/L|ng/mL|pg/mL|mcg/dL|mmHg|U/L|cells/mcL)?\s*"
    r"(?:\((?:ref|reference|normal)?\s*(?P<ref>[^)]+)\))?",
    re.IGNORECASE,
)

_COMMON_LAB_NAMES = [
    "HbA1c", "A1C", "Blood Sugar", "Fasting Glucose", "Glucose", "Serum Creatinine",
    "Creatinine", "BUN", "eGFR", "Sodium", "Potassium", "Chloride", "Calcium",
    "Total Cholesterol", "LDL", "HDL", "Triglycerides", "TSH", "Free T4", "Hemoglobin",
    "WBC", "Platelets", "ALT", "AST", "Bilirubin", "Blood Pressure", "BP", "Pulse", "Heart Rate",
]

_DATE_PATTERN = re.compile(
    r"\b(?P<date>\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\b",
    re.IGNORECASE,
)


def extract_clinical_facts(
    text: str | None,
    source_type: ProvenanceType | str = ProvenanceType.PATIENT_REPORTED,
    source_ref: str | None = None,
) -> ExtractionResult:
    """Extract clinical entities deterministically from natural language or structured notes.

    Args:
        text: Raw clinical narrative or pasted medical note text.
        source_type: Provenance classification (patient-reported or document-extracted).
        source_ref: Optional document identifier, file name, or turn reference.

    Returns:
        ExtractionResult containing conditions, medications, allergies, and lab results.
    """
    if isinstance(source_type, str):
        try:
            source_type = ProvenanceType(source_type)
        except ValueError:
            source_type = ProvenanceType.PATIENT_REPORTED

    result = ExtractionResult(raw_text=text or "")
    if not text or not isinstance(text, str) or not text.strip():
        return result

    raw_text = text.strip()
    provenance = ProvenanceRecord(source_type=source_type, source_ref=source_ref)

    # 1. Check for explicit allergy negations (e.g., NKDA)
    if _ALLERGY_NEGATION_PATTERN.search(raw_text):
        result.allergies.append(
            AllergyFact(
                allergen="No Known Drug Allergies",
                reaction="None",
                is_denied=True,
                provenance=provenance,
                raw_text=raw_text,
            )
        )
    else:
        # Extract specific allergies
        for match in _ALLERGY_PATTERN.finditer(raw_text):
            allergen = match.group("allergen").strip()
            # Filter out non-allergen words
            if allergen.lower() not in {"none", "no", "denies", "nil"}:
                reaction = match.group("reaction").strip() if match.group("reaction") else None
                result.allergies.append(
                    AllergyFact(
                        allergen=allergen,
                        reaction=reaction,
                        is_denied=False,
                        provenance=provenance,
                        raw_text=match.group(0),
                    )
                )

    # 2. Extract Medications
    # Scan for known drug names
    for drug in _KNOWN_DRUG_NAMES:
        drug_pattern = re.compile(rf"\b{re.escape(drug)}\b", re.IGNORECASE)
        for match in drug_pattern.finditer(raw_text):
            start = match.start()
            end = match.end()
            # Look ahead in the immediate segment following drug name for dosage and frequency
            context_window = raw_text[start:min(len(raw_text), end + 90)]
            
            # Find dosage in context
            dose_val = None
            unit_val = None
            dose_match = _DOSAGE_PATTERN.search(context_window)
            if dose_match:
                dose_val = dose_match.group("dose")
                unit_val = dose_match.group("unit")

            # Find frequency in context
            freq_val = None
            freq_match = _FREQUENCY_PATTERN.search(context_window)
            if freq_match:
                freq_val = freq_match.group("freq")

            # Detect discontinued status
            status = "active"
            if re.search(r"\b(discontinued|stopped|no\s+longer\s+taking|past)\b", raw_text[:start] + context_window, re.IGNORECASE):
                status = "discontinued"

            # Avoid duplicate extraction of exact same mention in close range
            if not any(m.name.lower() == drug.lower() and m.dosage == dose_val and m.raw_text == context_window.strip() for m in result.medications):
                result.medications.append(
                    MedicationFact(
                        name=drug,
                        dosage=dose_val,
                        unit=unit_val,
                        frequency=freq_val,
                        status=status,
                        provenance=provenance,
                        raw_text=context_window.strip(),
                    )
                )

    # 3. Extract Diagnoses / Conditions
    for cond in _KNOWN_CONDITIONS:
        cond_pattern = re.compile(rf"\b{re.escape(cond)}\b", re.IGNORECASE)
        if cond_pattern.search(raw_text):
            status = "active"
            if re.search(rf"\b(history\s+of|resolved|previous|prior)\s+{re.escape(cond)}\b", raw_text, re.IGNORECASE):
                status = "historical"
            result.conditions.append(
                ConditionFact(
                    name=cond,
                    status=status,
                    provenance=provenance,
                    raw_text=cond,
                )
            )

    # 4. Extract Laboratory Results & Investigations
    matched_lab_spans: list[tuple[int, int]] = []
    # Sort lab names by length descending so longer names (e.g. 'Serum Creatinine') match before 'Creatinine'
    sorted_lab_names = sorted(_COMMON_LAB_NAMES, key=len, reverse=True)
    for lab_name in sorted_lab_names:
        # Match test name followed by value
        lab_pattern = re.compile(
            rf"\b{re.escape(lab_name)}\b\s*[:=]?\s*(?P<val>\d+/\d+|\d+(?:\.\d+)?)\s*(?P<unit>%|mg/dL|g/dL|mmol/L|mEq/L|mIU/L|IU/L|ng/mL|pg/mL|mcg/dL|mmHg|U/L)?(?:\s*\((?:ref|reference)?\s*(?P<ref>[^)]+)\))?",
            re.IGNORECASE,
        )
        for match in lab_pattern.finditer(raw_text):
            start, end = match.span()
            if any(s <= start < e or s < end <= e for s, e in matched_lab_spans):
                continue
            matched_lab_spans.append((start, end))

            val_str = match.group("val")
            numeric_val = None
            string_val = None
            if "/" in val_str:
                string_val = val_str
            else:
                try:
                    numeric_val = float(val_str)
                except ValueError:
                    string_val = val_str

            unit = match.group("unit") if match.group("unit") else None
            ref_range = match.group("ref") if match.group("ref") else None

            # Detect date near the lab if available
            date_match = _DATE_PATTERN.search(raw_text)
            test_date = date_match.group("date") if date_match else None

            result.lab_results.append(
                LabResultFact(
                    test_name=lab_name,
                    numeric_value=numeric_val,
                    string_value=string_val,
                    unit=unit,
                    reference_range=ref_range,
                    test_date=test_date,
                    provenance=provenance,
                    raw_text=match.group(0).strip(),
                )
            )

    return result


# ===========================================================================
# SECTION: timeline.py
# ===========================================================================



from collections import defaultdict
from typing import Any

def detect_conflicts_and_timeline(
    extraction_input: ExtractionResult | list[Any],
) -> TimelineAndConflictResult:
    """Analyze clinical facts, build chronological timeline, and identify conflicts.

    Args:
        extraction_input: An ExtractionResult or list of heterogeneous clinical facts.

    Returns:
        TimelineAndConflictResult containing dated events, undated events, conflicts, and missing data indicators.
    """
    result = TimelineAndConflictResult()

    if not extraction_input:
        return result

    # Normalize input
    if isinstance(extraction_input, ExtractionResult):
        medications = extraction_input.medications
        conditions = extraction_input.conditions
        allergies = extraction_input.allergies
        lab_results = extraction_input.lab_results
    else:
        medications = [f for f in extraction_input if isinstance(f, MedicationFact)]
        conditions = [f for f in extraction_input if isinstance(f, ConditionFact)]
        allergies = [f for f in extraction_input if isinstance(f, AllergyFact)]
        lab_results = [f for f in extraction_input if isinstance(f, LabResultFact)]

    # 1. Timeline Organization
    # A. Process dated lab results
    for lab in lab_results:
        desc = f"Result: {lab.numeric_value or lab.string_value} {lab.unit or '[Missing unit]'}"
        if lab.reference_range:
            desc += f" (Ref: {lab.reference_range})"
        event = TimelineEvent(
            event_date=lab.test_date,
            title=f"Lab: {lab.test_name}",
            description=desc,
            provenance=lab.provenance,
        )
        if lab.test_date:
            result.dated_timeline.append(event)
        else:
            result.undated_events.append(event)

    # B. Process conditions
    for cond in conditions:
        event = TimelineEvent(
            event_date=cond.onset_date,
            title=f"Condition: {cond.name}",
            description=f"Status: {cond.status}",
            provenance=cond.provenance,
        )
        if cond.onset_date:
            result.dated_timeline.append(event)
        else:
            result.undated_events.append(event)

    # C. Sort dated timeline chronologically (string sort on ISO dates)
    result.dated_timeline.sort(key=lambda e: e.event_date or "")

    # 2. Conflict Detection: Medication Dosages
    # Group medications by standardized drug name
    med_groups: dict[str, list[MedicationFact]] = defaultdict(list)
    for med in medications:
        med_groups[med.name.lower()].append(med)

    for drug_name, meds in med_groups.items():
        # Check for multiple active mentions with different dosages
        active_meds = [m for m in meds if m.status == "active" and m.dosage is not None]
        distinct_doses = {f"{m.dosage}{m.unit or ''}" for m in active_meds}

        if len(distinct_doses) > 1:
            sources = [
                f"{m.provenance.source_type.value}: {m.name} {m.dosage}{m.unit or ''} ({m.frequency or 'unspecified freq'})"
                for m in active_meds
            ]
            result.conflicts.append(
                ClinicalConflict(
                    entity_name=meds[0].name,
                    category="medication_dosage",
                    description=(
                        f"Conflicting dosage instructions reported for {meds[0].name}: "
                        f"found different active dosages: {', '.join(sorted(distinct_doses))}."
                    ),
                    severity=ConflictSeverity.CRITICAL,
                    conflicting_sources=sources,
                )
            )

        # Check for missing dosages in active medications
        for m in meds:
            if m.status == "active" and m.dosage is None:
                result.missing_information.append(
                    MissingInfoIndicator(
                        field_name="dosage",
                        context=f"Medication '{m.name}' listed without dosage or strength.",
                        reason="Missing in provided narrative or document",
                    )
                )

    # 3. Conflict Detection: Allergy Statements vs Allergy Denials
    has_allergy_denial = any(a.is_denied for a in allergies)
    specific_allergies = [a for a in allergies if not a.is_denied]

    if has_allergy_denial and specific_allergies:
        allergen_names = [a.allergen for a in specific_allergies]
        result.conflicts.append(
            ClinicalConflict(
                entity_name="Allergy History",
                category="allergy_statement",
                description=(
                    f"Contradictory allergy history: Patient record indicates 'No known allergies' "
                    f"but simultaneously reports specific allergy to: {', '.join(allergen_names)}."
                ),
                severity=ConflictSeverity.CRITICAL,
                conflicting_sources=["Allergy Denial (NKDA)", *[a.raw_text for a in specific_allergies]],
            )
        )

    # 4. Check for Missing Information in Labs
    for lab in lab_results:
        if lab.unit is None:
            result.missing_information.append(
                MissingInfoIndicator(
                    field_name="unit",
                    context=f"Lab test '{lab.test_name}' recorded with value {lab.numeric_value or lab.string_value} but without units.",
                    reason="Missing in input text; units are not inferred to preserve clinical safety.",
                )
            )
        if lab.test_date is None:
            result.missing_information.append(
                MissingInfoIndicator(
                    field_name="test_date",
                    context=f"Lab test '{lab.test_name}' has no recorded investigation date.",
                    reason="Date not specified in provided report",
                )
            )

    return result


# ===========================================================================
# SECTION: summary.py
# ===========================================================================



from datetime import datetime, timezone
from typing import Any



def synthesize_clinical_draft(session: IntakeSession) -> ClinicalDraft:
    """Synthesize an intake session into a formatted clinical preparation draft.

    Args:
        session: Completed or in-progress IntakeSession.

    Returns:
        ClinicalDraft containing formatted Markdown and audit metadata.
    """
    facts = session.extracted_facts
    timeline = session.timeline_result
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: list[str] = []

    # 1. Prominent Safety & Governance Header
    lines.append("# MEDITALK CLINICAL PREPARATION DRAFT")
    lines.append("> **IMPORTANT NOTICE FOR CLINICIANS:**")
    lines.append("> This document is a structured intake draft compiled to assist clinical preparation.")
    lines.append("> MediTalk does not autonomously diagnose, treat, or prescribe. All statements,")
    lines.append("> extracted values, and detected conflicts must be reviewed and accepted by an authorized clinician.\n")

    lines.append(f"**Session ID:** `{session.session_id}` | **Generated:** {now_str}  ")
    lines.append(f"**Status:** `DRAFT_PENDING_CLINICIAN_REVIEW`  ")
    if session.consent_granted:
        lines.append(f"Consent Status: Explicit patient consent recorded at `{session.consent_timestamp or 'Timestamp verified'}`  ")
    else:
        lines.append("Consent Status: ⚠️ *Pending or not recorded*  ")

    # 2. Emergency Warning Banner (if triggered)
    if session.red_flag_triggered and session.red_flag_details:
        lines.append("\n> 🚨 **EMERGENCY WARNING PATTERN DETECTED**")
        lines.append(f"> {session.red_flag_details.safety_message}")
        lines.append(f"> **Action Recommended:** {session.red_flag_details.suggested_action}\n")

    # 3. Chief Complaint & HPI
    lines.append("## 1. Chief Complaint & History of Present Illness (HPI)")
    if session.chief_complaint:
        lines.append(f"**Chief Complaint:** {session.chief_complaint}\n")
    else:
        lines.append("**Chief Complaint:** *Not explicitly stated*\n")

    if session.hpi_narrative:
        lines.append(f"**HPI Narrative:**\n{session.hpi_narrative}\n")
    else:
        lines.append("**HPI Narrative:** *No detailed narrative provided*\n")

    # 4. Critical Conflicts & Discrepancies (Prominent Alert Box)
    lines.append("## 2. Identified Clinical Conflicts & Discrepancies")
    if timeline.conflicts:
        lines.append("⚠️ **The following discrepancies require clinician clarification before finalizing:**\n")
        for idx, conf in enumerate(timeline.conflicts, 1):
            severity_badge = "🔴 CRITICAL" if conf.severity == ConflictSeverity.CRITICAL else "🟡 WARNING"
            lines.append(f"### Discrepancy #{idx}: {conf.entity_name} ({severity_badge})")
            lines.append(f"- **Description:** {conf.description}")
            if conf.conflicting_sources:
                lines.append("- **Conflicting Data Points:**")
                for src in conf.conflicting_sources:
                    lines.append(f"  - `{src}`")
            lines.append("")
    else:
        lines.append("No active contradictions or conflicting dosages detected across supplied inputs.\n")

    # 5. Medications
    lines.append("## 3. Medications")
    if facts.medications:
        lines.append("| Medication | Dosage | Frequency | Status | Source Provenance |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for med in facts.medications:
            dose_str = f"{med.dosage} {med.unit}" if (med.dosage and med.unit) else (med.dosage or "*Not specified*")
            freq_str = med.frequency or "*Not specified*"
            prov_str = f"`{med.provenance.source_type.value}`"
            lines.append(f"| **{med.name}** | {dose_str} | {freq_str} | {med.status.title()} | {prov_str} |")
        lines.append("")
    else:
        lines.append("*No medications reported or identified in provided text.*\n")

    # 6. Allergies & Adverse Reactions
    lines.append("## 4. Allergies & Adverse Reactions")
    if facts.allergies:
        for allergy in facts.allergies:
            if allergy.is_denied:
                lines.append(f"- **{allergy.allergen}** (Patient confirms no known adverse drug reactions)")
            else:
                reaction_str = f" — *Reaction:* {allergy.reaction}" if allergy.reaction else ""
                lines.append(f"- **{allergy.allergen}**{reaction_str} (`{allergy.provenance.source_type.value}`)")
        lines.append("")
    else:
        lines.append("*Allergy status not documented. Must be verified with patient.*\n")

    # 7. Diagnoses & Past Medical History
    lines.append("## 5. Diagnoses & Medical History")
    if facts.conditions:
        for cond in facts.conditions:
            lines.append(f"- **{cond.name}** (Status: *{cond.status}*, Source: `{cond.provenance.source_type.value}`)")
        lines.append("")
    else:
        lines.append("*No prior medical conditions documented.*\n")

    # 8. Laboratory Investigations
    lines.append("## 6. Laboratory Results & Diagnostic Investigations")
    if facts.lab_results:
        lines.append("| Investigation | Result | Reference Range | Date | Source |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for lab in facts.lab_results:
            val_str = f"{lab.numeric_value or lab.string_value} {lab.unit or '[Missing unit]'}"
            ref_str = lab.reference_range or "—"
            date_str = lab.test_date or "*Undated*"
            lines.append(f"| **{lab.test_name}** | {val_str} | {ref_str} | {date_str} | `{lab.provenance.source_type.value}` |")
        lines.append("")
    else:
        lines.append("*No laboratory investigations extracted from input.*\n")

    # 9. Chronological Timeline
    lines.append("## 7. Medical Timeline")
    if timeline.dated_timeline:
        lines.append("### Dated Events (Chronological)")
        for ev in timeline.dated_timeline:
            lines.append(f"- **{ev.event_date}**: {ev.title} — {ev.description} (`{ev.provenance.source_type.value}`)")
        lines.append("")
    if timeline.undated_events:
        lines.append("### Undated Observations")
        for ev in timeline.undated_events:
            lines.append(f"- {ev.title}: {ev.description} (`{ev.provenance.source_type.value}`)")
        lines.append("")
    if not timeline.dated_timeline and not timeline.undated_events:
        lines.append("*No timeline events recorded.*\n")

    # 10. Missing Information & Review Checklist
    lines.append("## 8. Missing Information & Clinical Verification Checklist")
    if timeline.missing_information:
        lines.append("The following clinical items were not specified in the input and require clinician verification:")
        for missing in timeline.missing_information:
            lines.append(f"- [ ] **{missing.field_name.upper()}**: {missing.context} *(Reason: {missing.reason})*")
        lines.append("")
    else:
        lines.append("All primary fields contain baseline entries; routine clinical review required.\n")

    # 11. Provenance Breakdown
    lines.append("## 9. Provenance Summary")
    patient_reported_count = sum(
        1 for f in [*facts.medications, *facts.conditions, *facts.allergies, *facts.lab_results]
        if f.provenance.source_type == ProvenanceType.PATIENT_REPORTED
    )
    document_extracted_count = sum(
        1 for f in [*facts.medications, *facts.conditions, *facts.allergies, *facts.lab_results]
        if f.provenance.source_type == ProvenanceType.DOCUMENT_EXTRACTED
    )
    lines.append(f"- **Patient-Reported Facts:** {patient_reported_count}")
    lines.append(f"- **Document-Extracted Facts:** {document_extracted_count}")
    lines.append(f"- **Detected Conflicts:** {len(timeline.conflicts)}")
    lines.append(f"- **Missing Information Flags:** {len(timeline.missing_information)}\n")

    # 12. Clinician Acceptance Placeholder
    lines.append("---")
    lines.append("### Clinician Review & Acceptance")
    lines.append("- [ ] **Clinician Signature / Acceptance:** ___________________________")
    lines.append("- [ ] **Date Reviewed:** ___________________________")
    lines.append("- [ ] **Action:** `[ ] Accept with edits` | `[ ] Accept as is` | `[ ] Return for clarification`\n")

    formatted_md = "\n".join(lines)
    total_facts = len(facts.medications) + len(facts.conditions) + len(facts.allergies) + len(facts.lab_results)

    return ClinicalDraft(
        formatted_markdown=formatted_md,
        summary_status="DRAFT_PENDING_CLINICIAN_REVIEW",
        fact_count=total_facts,
        conflict_count=len(timeline.conflicts),
        missing_items_count=len(timeline.missing_information),
        has_emergency_warning=session.red_flag_triggered,
    )


# ===========================================================================
# SECTION: tools.py
# ===========================================================================




__all__ = [
    # Core Tools
    "screen_red_flags",
    "extract_clinical_facts",
    "detect_conflicts_and_timeline",
    "synthesize_clinical_draft",
    # Domain Models
    "RedFlagResult",
    "ExtractionResult",
    "TimelineAndConflictResult",
    "ClinicalDraft",
    "IntakeSession",
    "MedicationFact",
    "ConditionFact",
    "AllergyFact",
    "LabResultFact",
    "ClinicalConflict",
    "ConflictSeverity",
    "MissingInfoIndicator",
    "TimelineEvent",
    "ProvenanceRecord",
    "ProvenanceType",
]


# ===========================================================================
# SECTION: session.py
# ===========================================================================



import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


logger = logging.getLogger("meditalk.agent.session")


# Try importing official uagents-core ACP models; fallback to identical pure-python schemas
try:
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement as OfficialChatAcknowledgement,
        ChatMessage as OfficialChatMessage,
        TextContent as OfficialTextContent,
    )
    HAS_UAGENTS_CORE = True
except ImportError:
    HAS_UAGENTS_CORE = False


@dataclass
class TextContent:
    """Standardized text content block matching ACP specification."""
    text: str
    type: str = "text"


@dataclass
class ChatMessage:
    """Standardized message model matching ACP specification."""
    msg_id: UUID | str
    timestamp: datetime
    content: list[Any]


@dataclass
class ChatAcknowledgement:
    """Receipt acknowledgement matching ACP specification."""
    timestamp: datetime
    acknowledged_msg_id: UUID | str


class ConversationState(str, Enum):
    """Lifecycle states of a patient intake session."""
    AWAITING_CONSENT = "awaiting_consent"
    INTAKE_ACTIVE = "intake_active"
    DRAFT_SYNTHESIZED = "draft_synthesized"


@dataclass
class AgentSession:
    """Per-sender isolated intake session state."""
    sender_id: str
    state: ConversationState = ConversationState.AWAITING_CONSENT
    consent_granted: bool = False
    consent_timestamp: str | None = None
    chief_complaint: str = ""
    hpi_narrative: str = ""
    red_flag_triggered: bool = False
    red_flag_details: RedFlagResult | None = None
    extracted_facts: ExtractionResult = field(default_factory=ExtractionResult)
    timeline_result: TimelineAndConflictResult = field(default_factory=TimelineAndConflictResult)
    last_interaction: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "state": self.state.value if isinstance(self.state, ConversationState) else str(self.state),
            "consent_granted": self.consent_granted,
            "consent_timestamp": self.consent_timestamp,
            "chief_complaint": self.chief_complaint,
            "hpi_narrative": self.hpi_narrative,
            "red_flag_triggered": self.red_flag_triggered,
            "red_flag_details": self.red_flag_details.to_dict() if self.red_flag_details else None,
            "extracted_facts": self.extracted_facts.to_dict(),
            "timeline_result": self.timeline_result.to_dict(),
            "last_interaction": self.last_interaction,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentSession:
        session = cls(sender_id=data.get("sender_id", ""))
        try:
            session.state = ConversationState(data.get("state", ConversationState.AWAITING_CONSENT.value))
        except ValueError:
            session.state = ConversationState.AWAITING_CONSENT
        session.consent_granted = data.get("consent_granted", False)
        session.consent_timestamp = data.get("consent_timestamp")
        session.chief_complaint = data.get("chief_complaint", "")
        session.hpi_narrative = data.get("hpi_narrative", "")
        session.red_flag_triggered = data.get("red_flag_triggered", False)
        if data.get("red_flag_details"):
            rf = data["red_flag_details"]
            session.red_flag_details = RedFlagResult(
                is_emergency=rf.get("is_emergency", False),
                matched_indicators=rf.get("matched_indicators", []),
                safety_message=rf.get("safety_message", ""),
                suggested_action=rf.get("suggested_action", ""),
                disclaimer=rf.get("disclaimer", ""),
            )
        session.last_interaction = data.get("last_interaction", "")
        return session


class SessionManager:
    """In-memory session registry with per-sender isolation."""

    def __init__(self) -> None:
        self._sessions: dict[str, AgentSession] = {}

    def get_or_create(self, sender: str) -> AgentSession:
        if sender not in self._sessions:
            self._sessions[sender] = AgentSession(sender_id=sender)
        return self._sessions[sender]

    def reset_session(self, sender: str) -> AgentSession:
        self._sessions[sender] = AgentSession(sender_id=sender)
        return self._sessions[sender]

    def session_count(self) -> int:
        return len(self._sessions)


# Global session manager instance
session_manager = SessionManager()

_CONSENT_POSITIVE_KEYWORDS = {
    "consent", "i consent", "yes", "i agree", "agree", "accept",
    "i accept", "proceed", "sure", "ok", "okay", "start",
}

_SUMMARY_TRIGGER_KEYWORDS = {
    "summary", "draft", "prepare draft", "clinical summary", "prepare my history",
    "ready", "doctor visit", "done", "finished", "generate report",
}


def process_user_turn(sender: str, raw_text: str | None, ctx: Any = None) -> str:
    """Process a single turn from a sender and return the agent's textual response.

    Args:
        sender: Unique sender address or user identifier.
        raw_text: Text extracted from incoming ACP ChatMessage.
        ctx: Optional uAgents Context providing persistent ctx.storage.

    Returns:
        Structured response string adhering to MediTalk clinical guidelines.
    """
    # 0. Load session from ctx.storage if available, else in-memory manager
    if ctx and hasattr(ctx, "storage") and ctx.storage:
        stored = ctx.storage.get(f"session_{sender}")
        if stored and isinstance(stored, dict):
            session = AgentSession.from_dict(stored)
        else:
            session = session_manager.get_or_create(sender)
    else:
        session = session_manager.get_or_create(sender)

    session.last_interaction = datetime.now(timezone.utc).isoformat()

    def _persist_and_return(text: str) -> str:
        if ctx and hasattr(ctx, "storage") and ctx.storage:
            ctx.storage.set(f"session_{sender}", session.to_dict())
        return text

    # 1. Handle empty / whitespace inputs
    if not raw_text or not raw_text.strip():
        logger.info("Empty turn received for sender=%s", sender)
        return _persist_and_return(
            "Hello! I am MediTalk, your clinical history preparation assistant. "
            "I didn't receive any text. Please type your message, symptoms, or "
            "paste your medical notes to begin."
        )

    clean_text = raw_text.strip()
    lower_text = clean_text.lower()

    # 2. EMERGENCY RED-FLAG SCREENING (Evaluated on every incoming turn)
    red_flag_check = screen_red_flags(clean_text)
    if red_flag_check.is_emergency:
        session.red_flag_triggered = True
        session.red_flag_details = red_flag_check
        logger.warning(
            "Emergency warning triggered for sender=%s: %s",
            sender,
            "; ".join(red_flag_check.matched_indicators),
        )
        return _persist_and_return(
            f"🚨 **{red_flag_check.safety_message}**\n\n"
            f"👉 **Action Required:** {red_flag_check.suggested_action}\n\n"
            f"> *{red_flag_check.disclaimer}*"
        )

    # 3. CONSENT VERIFICATION
    if not session.consent_granted:
        # Check if the user is granting consent
        if any(kw in lower_text for kw in _CONSENT_POSITIVE_KEYWORDS):
            session.consent_granted = True
            session.consent_timestamp = datetime.now(timezone.utc).isoformat()
            session.state = ConversationState.INTAKE_ACTIVE
            logger.info("Consent recorded for sender=%s", sender)
            return _persist_and_return(
                "✅ **Consent Recorded.** Thank you.\n\n"
                "Please tell me what brings you in today — what is your **main symptom or chief complaint**? "
                "You can also paste any prescriptions, discharge summaries, or laboratory test reports."
            )
        else:
            # Inform user of purpose and boundaries and request explicit consent
            return _persist_and_return(
                "👋 **Welcome to MediTalk.**\n\n"
                "I am a clinical preparation assistant designed to help you organize your medical "
                "history, medications, and records into a structured draft for your healthcare provider.\n\n"
                "**Clinical Safety Notice & Limitations:**\n"
                "- MediTalk does not autonomously diagnose conditions or prescribe medications.\n"
                "- MediTalk does not provide emergency intervention. If you are experiencing an acute medical emergency, call emergency services immediately.\n"
                "- All summaries are drafts that require review and verification by your clinician.\n\n"
                "To begin, **do you consent** to sharing your health information for clinical preparation? "
                "(Reply **'Yes'** or **'I consent'** to proceed)."
            )

    # 4. ACTIVE INTAKE FLOW (Consent is confirmed)
    # Prefix response with emergency reminder if session previously triggered an alert
    emergency_prefix = ""
    if session.red_flag_triggered and session.red_flag_details:
        emergency_prefix = (
            "⚠️ **PRIOR EMERGENCY ALERT:** Critical symptoms were previously detected during this intake. "
            "If you are experiencing acute distress, seek emergency medical care immediately.\n\n---\n\n"
        )

    # A. Check if the user is requesting draft synthesis
    if any(kw in lower_text for kw in _SUMMARY_TRIGGER_KEYWORDS) and (
        session.chief_complaint or session.extracted_facts.medications or session.extracted_facts.lab_results
    ):
        session.state = ConversationState.DRAFT_SYNTHESIZED
        # Build IntakeSession domain model
        intake_domain_session = IntakeSession(
            session_id=f"sess_{sender[:12]}",
            consent_granted=session.consent_granted,
            consent_timestamp=session.consent_timestamp,
            chief_complaint=session.chief_complaint,
            hpi_narrative=session.hpi_narrative,
            extracted_facts=session.extracted_facts,
            timeline_result=session.timeline_result,
            red_flag_triggered=session.red_flag_triggered,
            red_flag_details=session.red_flag_details,
        )
        draft = synthesize_clinical_draft(intake_domain_session)
        logger.info(
            "Clinical draft synthesized for sender=%s (facts=%d, conflicts=%d)",
            sender,
            draft.fact_count,
            draft.conflict_count,
        )
        return _persist_and_return(
            f"{emergency_prefix}Here is your structured clinical preparation draft for your doctor:\n\n{draft.formatted_markdown}"
        )

    # B. Extract facts from user message
    # Classify source: if text looks like a report or prescription, classify as document_extracted
    source_type = ProvenanceType.PATIENT_REPORTED
    source_ref = "chat_message"
    if any(header in lower_text for header in ["rx:", "prescription:", "discharge summary:", "lab report:", "test results:"]):
        source_type = ProvenanceType.DOCUMENT_EXTRACTED
        source_ref = "pasted_document"

    new_facts = extract_clinical_facts(clean_text, source_type=source_type, source_ref=source_ref)

    # Merge facts into session
    session.extracted_facts.medications.extend(new_facts.medications)
    session.extracted_facts.conditions.extend(new_facts.conditions)
    session.extracted_facts.allergies.extend(new_facts.allergies)
    session.extracted_facts.lab_results.extend(new_facts.lab_results)

    # If chief complaint is not yet recorded and user describes a symptom/complaint
    if not session.chief_complaint:
        session.chief_complaint = clean_text[:200]
    else:
        session.hpi_narrative += ("\n" if session.hpi_narrative else "") + clean_text

    # Run timeline and conflict detection over all accumulated facts
    session.timeline_result = detect_conflicts_and_timeline(session.extracted_facts)

    # Build constructive conversational reply
    reply_lines: list[str] = []

    # Report acknowledged extractions
    items_found: list[str] = []
    if new_facts.medications:
        med_names = [f"{m.name} ({m.dosage or 'dose unstated'}{m.unit or ''})" for m in new_facts.medications]
        items_found.append(f"Medications: {', '.join(med_names)}")
    if new_facts.conditions:
        items_found.append(f"Conditions: {', '.join(c.name for c in new_facts.conditions)}")
    if new_facts.allergies:
        allergy_names = [a.allergen for a in new_facts.allergies]
        items_found.append(f"Allergies: {', '.join(allergy_names)}")
    if new_facts.lab_results:
        lab_names = [f"{l.test_name} ({l.numeric_value or l.string_value} {l.unit or 'no unit'})" for l in new_facts.lab_results]
        items_found.append(f"Investigations: {', '.join(lab_names)}")

    if items_found:
        reply_lines.append("📋 **Noted:** " + "; ".join(items_found) + ".")
    else:
        reply_lines.append("Got it. I have added that to your history.")

    # Prominently surface any critical discrepancies detected
    critical_conflicts = [c for c in session.timeline_result.conflicts if c.severity == ConflictSeverity.CRITICAL]
    if critical_conflicts:
        reply_lines.append("\n⚠️ **Discrepancy Detected:**")
        for conf in critical_conflicts:
            reply_lines.append(f"- {conf.description}")
        reply_lines.append("*I have flagged this discrepancy for your doctor to clarify.*")

    # Missing information prompt
    if session.timeline_result.missing_information:
        missing_sample = session.timeline_result.missing_information[0]
        reply_lines.append(f"\n💡 *Note:* {missing_sample.context}")

    reply_lines.append(
        "\nDo you have any other symptoms, previous lab reports, or allergies to add? "
        "Or type **'summary'** when you are ready to generate your doctor's draft."
    )

    return _persist_and_return(emergency_prefix + "\n".join(reply_lines))


def parse_incoming_text(msg: Any) -> str:
    """Extract plain text payload from an ACP ChatMessage or dict."""
    if hasattr(msg, "content"):
        contents = msg.content
    elif isinstance(msg, dict):
        contents = msg.get("content", [])
    else:
        return ""

    if not isinstance(contents, list):
        return str(contents)

    text_parts: list[str] = []
    for item in contents:
        if isinstance(item, TextContent) or (HAS_UAGENTS_CORE and isinstance(item, OfficialTextContent)):
            text_parts.append(item.text)
        elif hasattr(item, "text"):
            text_parts.append(str(item.text))
        elif isinstance(item, dict) and item.get("type") == "text":
            text_parts.append(str(item.get("text", "")))
        elif isinstance(item, str):
            text_parts.append(item)

    return "\n".join(text_parts).strip()


def create_acknowledgement(msg_id: UUID | str) -> ChatAcknowledgement:
    """Construct an ACP receipt acknowledgement referencing msg_id."""
    return ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc),
        acknowledged_msg_id=msg_id,
    )


def create_reply_message(reply_text: str) -> ChatMessage:
    """Construct an ACP ChatMessage payload containing TextContent."""
    return ChatMessage(
        msg_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        content=[TextContent(type="text", text=reply_text)],
    )


# ===========================================================================
# SECTION: agent.py
# ===========================================================================



import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Ensure agent package root is in sys.path


logger = logging.getLogger("meditalk.agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Environment configuration
AGENT_NAME = os.getenv("AGENT_NAME", "meditalk_agent")
AGENT_SEED = os.getenv("AGENT_SEED", "meditalk_dev_agent_seed_default_dev_only")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8001"))
AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY")

try:
    from uagents import Agent, Context, Protocol
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement,
        ChatMessage,
        TextContent,
        chat_protocol_spec,
    )

    UAGENTS_AVAILABLE = True
except ImportError:
    UAGENTS_AVAILABLE = False


async def on_chat_message(ctx: Any, sender: str, msg: Any) -> None:
    """Handle incoming ACP chat message from ASI:One or peer agent."""
    msg_id = getattr(msg, "msg_id", None) or uuid4()
    logger.info("Received ACP message from sender=%s msg_id=%s", sender, msg_id)

    # 1. Acknowledge receipt immediately (<100ms mandate)
    ack = ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc),
        acknowledged_msg_id=msg_id,
    )
    await ctx.send(sender, ack)

    # 2. Extract text content
    user_text = parse_incoming_text(msg)

    # 3. Process turn through MediTalk state machine
    try:
        reply_text = process_user_turn(sender=sender, raw_text=user_text, ctx=ctx)
    except Exception as exc:
        logger.error("Error processing turn for sender=%s: %s", sender, exc, exc_info=True)
        reply_text = (
            "An unexpected error occurred while processing your message. "
            "Your intake state has been preserved. Please try rephrasing your message."
        )

    # 4. Construct and dispatch ACP ChatMessage reply
    reply_msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=reply_text)],
    )
    await ctx.send(sender, reply_msg)
    logger.info("Dispatched ACP reply to sender=%s", sender)


async def on_chat_ack(ctx: Any, sender: str, msg: Any) -> None:
    """Handle receipt confirmations from client/peer."""
    ack_id = getattr(msg, "acknowledged_msg_id", None)
    logger.info("Sender=%s acknowledged receipt of msg_id=%s", sender, ack_id)


def create_agent() -> Any:
    """Instantiate and configure the MediTalk uAgent with ACP protocol."""
    if not UAGENTS_AVAILABLE:
        raise RuntimeError(
            "uagents library is not installed in the current environment. "
            "Install with: pip install 'uagents>=0.25.5'"
        )

    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Initialize agent (configure mailbox if key is provided)
    agent_kwargs: dict[str, Any] = {
        "name": AGENT_NAME,
        "seed": AGENT_SEED,
        "port": AGENT_PORT,
        "loop": loop,
    }
    if AGENT_MAILBOX_KEY:
        agent_kwargs["mailbox"] = AGENT_MAILBOX_KEY

    agent = Agent(**agent_kwargs)

    # Instantiate the official Chat Protocol
    chat_proto = Protocol(spec=chat_protocol_spec)

    # Register handlers
    chat_proto.on_message(ChatMessage)(on_chat_message)
    chat_proto.on_message(ChatAcknowledgement)(on_chat_ack)

    # Include protocol with manifest publication for Agentverse/ASI:One discovery
    agent.include(chat_proto, publish_manifest=True)
    return agent


# Module-level agent instance for Agentverse Hosted environment
agent: Any = None
if UAGENTS_AVAILABLE and os.getenv("AGENTVERSE_HOSTED", "false").lower() in ("true", "1"):
    try:
        agent = create_agent()
    except Exception as exc:
        logger.warning("Could not auto-instantiate module-level agent: %s", exc)


if __name__ == "__main__":
    if not UAGENTS_AVAILABLE:
        print("\n" + "=" * 70)
        print("MediTalk Clinical Preparation Agent (ACP Adapter)")
        print("=" * 70)
        print("\nNotice: The 'uagents' library is required to run the live networking agent.")
        print("All clinical tools, state machine, and tests are available standalone.")
        print("\nTo run the live agent on Agentverse:")
        print("  1. pip install 'uagents>=0.25.5'")
        print("  2. python -m apps.agent.src.agent")
        print("=" * 70 + "\n")
        sys.exit(0)

    agent_instance = create_agent()
    print(f"Starting {AGENT_NAME} on port {AGENT_PORT}...")
    agent_instance.run()
