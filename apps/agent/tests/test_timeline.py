"""Tests for detect_conflicts_and_timeline.

Verifies chronological sequencing, detection of conflicting medication dosages,
identification of contradictory allergy statements, and tracking of missing information.
All patient data is synthetic.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure apps/agent root is in sys.path
_agent_root = str(Path(__file__).resolve().parent.parent)
if _agent_root not in sys.path:
    sys.path.insert(0, _agent_root)

from src.models import (
    AllergyFact,
    ConditionFact,
    ConflictSeverity,
    ExtractionResult,
    LabResultFact,
    MedicationFact,
    ProvenanceRecord,
    ProvenanceType,
)
from src.timeline import detect_conflicts_and_timeline


def test_empty_input_timeline() -> None:
    """Empty extraction returns clean, empty result."""
    res = detect_conflicts_and_timeline(ExtractionResult())
    assert res.dated_timeline == []
    assert res.undated_events == []
    assert res.conflicts == []
    assert res.missing_information == []


def test_chronological_sorting_of_dated_events() -> None:
    """Dated events must be organized chronologically."""
    facts = ExtractionResult(
        lab_results=[
            LabResultFact(
                test_name="Serum Creatinine",
                numeric_value=1.4,
                unit="mg/dL",
                test_date="2024-06-15",
            ),
            LabResultFact(
                test_name="HbA1c",
                numeric_value=6.8,
                unit="%",
                test_date="2024-01-10",
            ),
        ],
        conditions=[
            ConditionFact(
                name="Hypertension",
                onset_date="2023-11-01",
            ),
        ],
    )

    res = detect_conflicts_and_timeline(facts)
    assert len(res.dated_timeline) == 3
    # Earliest date first
    dates = [e.event_date for e in res.dated_timeline]
    assert dates == ["2023-11-01", "2024-01-10", "2024-06-15"]


def test_detect_medication_dosage_conflict() -> None:
    """Conflicting active dosages for the same medication must be flagged as CRITICAL conflicts."""
    facts = ExtractionResult(
        medications=[
            MedicationFact(
                name="Lisinopril",
                dosage="10",
                unit="mg",
                frequency="daily",
                status="active",
                provenance=ProvenanceRecord(source_type=ProvenanceType.DOCUMENT_EXTRACTED, source_ref="discharge_2023.pdf"),
            ),
            MedicationFact(
                name="Lisinopril",
                dosage="20",
                unit="mg",
                frequency="daily",
                status="active",
                provenance=ProvenanceRecord(source_type=ProvenanceType.PATIENT_REPORTED, source_ref="chat_turn_2"),
            ),
        ]
    )

    res = detect_conflicts_and_timeline(facts)
    assert len(res.conflicts) == 1
    conflict = res.conflicts[0]
    assert conflict.entity_name == "Lisinopril"
    assert conflict.category == "medication_dosage"
    assert conflict.severity == ConflictSeverity.CRITICAL
    assert "10mg" in conflict.description and "20mg" in conflict.description
    assert len(conflict.conflicting_sources) == 2


def test_detect_allergy_contradiction() -> None:
    """Simultaneous allergy denial (NKDA) and specific allergy must be flagged as CRITICAL."""
    facts = ExtractionResult(
        allergies=[
            AllergyFact(
                allergen="No Known Drug Allergies",
                is_denied=True,
                raw_text="No known allergies",
            ),
            AllergyFact(
                allergen="Amoxicillin",
                reaction="Hives and facial swelling",
                is_denied=False,
                raw_text="Allergic to Amoxicillin",
            ),
        ]
    )

    res = detect_conflicts_and_timeline(facts)
    assert len(res.conflicts) == 1
    conflict = res.conflicts[0]
    assert conflict.category == "allergy_statement"
    assert conflict.severity == ConflictSeverity.CRITICAL
    assert "Amoxicillin" in conflict.description


def test_missing_information_detection() -> None:
    """Missing dosages, units, and dates must be tracked in missing_information."""
    facts = ExtractionResult(
        medications=[
            MedicationFact(
                name="Aspirin",
                dosage=None,  # Missing dose
                status="active",
            ),
        ],
        lab_results=[
            LabResultFact(
                test_name="Serum Creatinine",
                numeric_value=1.5,
                unit=None,  # Missing unit
                test_date=None,  # Missing date
            ),
        ],
    )

    res = detect_conflicts_and_timeline(facts)
    missing_fields = [m.field_name for m in res.missing_information]
    assert "dosage" in missing_fields
    assert "unit" in missing_fields
    assert "test_date" in missing_fields
