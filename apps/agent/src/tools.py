"""Public facade for MediTalk Phase 1 Clinical Tools.

Exposes deterministic, independently testable functions for:
1. screen_red_flags
2. extract_clinical_facts
3. detect_conflicts_and_timeline
4. synthesize_clinical_draft
"""

from __future__ import annotations

from .extractor import extract_clinical_facts
from .models import (
    AllergyFact,
    ClinicalConflict,
    ClinicalDraft,
    ConditionFact,
    ConflictSeverity,
    ExtractionResult,
    IntakeSession,
    LabResultFact,
    MedicationFact,
    MissingInfoIndicator,
    ProvenanceRecord,
    ProvenanceType,
    RedFlagResult,
    TimelineAndConflictResult,
    TimelineEvent,
)
from .red_flags import screen_red_flags
from .summary import synthesize_clinical_draft
from .timeline import detect_conflicts_and_timeline

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
