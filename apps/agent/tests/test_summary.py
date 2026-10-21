"""Tests for synthesize_clinical_draft.

Verifies generation of structured, source-aware clinical drafts, ensuring
safety notices, conflict alerts, provenance breakdown, and clinician sign-off
placeholders are always included.
All data is synthetic.
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
    ClinicalConflict,
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
from src.summary import synthesize_clinical_draft


def test_empty_session_draft_synthesis() -> None:
    """An empty session produces a valid draft with clear missing-field indicators and safety notices."""
    session = IntakeSession(session_id="test_sess_001")
    draft = synthesize_clinical_draft(session)

    assert draft.summary_status == "DRAFT_PENDING_CLINICIAN_REVIEW"
    assert "MEDITALK CLINICAL PREPARATION DRAFT" in draft.formatted_markdown
    assert "does not autonomously diagnose, treat, or prescribe" in draft.formatted_markdown
    assert "Clinician Signature / Acceptance" in draft.formatted_markdown
    assert draft.fact_count == 0


def test_comprehensive_synthetic_patient_draft() -> None:
    """Synthesize complete patient session with medications, conflicts, and provenance."""
    session = IntakeSession(
        session_id="sess_patient_synth_42",
        patient_id="synth_pt_101",
        consent_granted=True,
        consent_timestamp="2026-10-20T10:00:00Z",
        chief_complaint="Increasing shortness of breath on exertion and bilateral ankle swelling for 3 weeks.",
        hpi_narrative="Patient reports gradual onset of exertional dyspnea when climbing stairs.",
        extracted_facts=ExtractionResult(
            conditions=[
                ConditionFact(name="Hypertension", status="active"),
                ConditionFact(name="Heart Failure", status="active"),
            ],
            medications=[
                MedicationFact(
                    name="Lisinopril",
                    dosage="10",
                    unit="mg",
                    frequency="daily",
                    provenance=ProvenanceRecord(source_type=ProvenanceType.DOCUMENT_EXTRACTED, source_ref="discharge_2023.txt"),
                ),
                MedicationFact(
                    name="Lisinopril",
                    dosage="20",
                    unit="mg",
                    frequency="daily",
                    provenance=ProvenanceRecord(source_type=ProvenanceType.PATIENT_REPORTED),
                ),
                MedicationFact(
                    name="Furosemide",
                    dosage="20",
                    unit="mg",
                    frequency="daily",
                    provenance=ProvenanceRecord(source_type=ProvenanceType.DOCUMENT_EXTRACTED),
                ),
            ],
            allergies=[
                AllergyFact(allergen="Sulfa", reaction="Skin rash", is_denied=False),
            ],
            lab_results=[
                LabResultFact(
                    test_name="Serum Creatinine",
                    numeric_value=1.3,
                    unit="mg/dL",
                    test_date="2024-05-01",
                ),
            ],
        ),
        timeline_result=TimelineAndConflictResult(
            dated_timeline=[
                TimelineEvent(
                    event_date="2024-05-01",
                    title="Lab: Serum Creatinine",
                    description="Result: 1.3 mg/dL",
                    provenance=ProvenanceRecord(source_type=ProvenanceType.DOCUMENT_EXTRACTED),
                )
            ],
            conflicts=[
                ClinicalConflict(
                    entity_name="Lisinopril",
                    category="medication_dosage",
                    description="Conflicting active dosages: 10mg vs 20mg.",
                    severity=ConflictSeverity.CRITICAL,
                    conflicting_sources=["discharge_2023.txt: 10mg", "patient_reported: 20mg"],
                )
            ],
            missing_information=[
                MissingInfoIndicator(
                    field_name="onset_date",
                    context="Exact onset date of Hypertension not documented.",
                )
            ],
        ),
        red_flag_triggered=False,
    )

    draft = synthesize_clinical_draft(session)

    md = draft.formatted_markdown
    # Governance & Draft status
    assert "DRAFT_PENDING_CLINICIAN_REVIEW" in md
    assert "Consent Status: Explicit patient consent recorded" in md

    # Chief complaint & HPI
    assert "Increasing shortness of breath" in md
    assert "climbing stairs" in md

    # Conflicts prominently surfaced
    assert "Identified Clinical Conflicts & Discrepancies" in md
    assert "Conflicting active dosages: 10mg vs 20mg" in md

    # Medications table
    assert "| **Lisinopril** |" in md
    assert "| **Furosemide** |" in md

    # Allergies & Labs
    assert "Sulfa" in md
    assert "Serum Creatinine" in md

    # Missing info & Checklist
    assert "Missing Information & Clinical Verification Checklist" in md
    assert "ONSET_DATE" in md

    # Provenance summary
    assert "Patient-Reported Facts:" in md
    assert "Document-Extracted Facts:" in md

    # Metrics
    assert draft.conflict_count == 1
    assert draft.missing_items_count == 1
    assert not draft.has_emergency_warning


def test_red_flag_emergency_banner_in_draft() -> None:
    """When a red flag is triggered, an emergency alert banner must be rendered in the draft."""
    session = IntakeSession(
        session_id="emergency_sess_002",
        chief_complaint="Severe chest pain and shortness of breath",
        red_flag_triggered=True,
        red_flag_details=RedFlagResult(
            is_emergency=True,
            matched_indicators=["ACUTE_CHEST_PAIN_CARDIAC: Crushing chest pain"],
            safety_message="High-risk cardiac warning signs detected.",
            suggested_action="Seek emergency medical attention immediately.",
        ),
    )

    draft = synthesize_clinical_draft(session)
    assert draft.has_emergency_warning
    assert "EMERGENCY WARNING PATTERN DETECTED" in draft.formatted_markdown
    assert "High-risk cardiac warning signs detected." in draft.formatted_markdown
