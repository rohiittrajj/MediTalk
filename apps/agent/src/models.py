"""Core domain models and data contracts for MediTalk Clinical Preparation Agent.

Preserves provenance, distinguishes known/unknown facts, and enforces strict
boundaries around clinical drafts and safety screening.
"""

from __future__ import annotations

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
