"""Safety, conflict-preservation, and provenance-integrity regression tests.

Verifies:
1. Emergency warnings cannot be suppressed or masked by benign context.
2. Emergency state cannot be cleared by subsequent non-urgent turns.
3. Conflicting medication dosages are strictly preserved without silent resolution.
4. Extracted facts retain full provenance and source references through to the draft.
5. Missing units and dosages are never silently inferred or fabricated.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure apps/agent root is in sys.path
_agent_root = str(Path(__file__).resolve().parent.parent)
if _agent_root not in sys.path:
    sys.path.insert(0, _agent_root)

from src.extractor import extract_clinical_facts
from src.models import (
    ConflictSeverity,
    ExtractionResult,
    IntakeSession,
    MedicationFact,
    ProvenanceRecord,
    ProvenanceType,
    RedFlagResult,
    TimelineAndConflictResult,
)
from src.red_flags import screen_red_flags
from src.summary import synthesize_clinical_draft
from src.timeline import detect_conflicts_and_timeline


def test_emergency_not_masked_by_benign_intake_narrative() -> None:
    """An emergency warning embedded in a long routine intake message must still trigger."""
    mixed_text = (
        "Good morning, I am scheduling a routine consultation for my hypertension. "
        "I need a refill on my blood pressure medicine, and also my knee has been stiff. "
        "However, right now I have crushing chest pain and shortness of breath that started 15 minutes ago. "
        "I was hoping to talk about it during my appointment."
    )
    result = screen_red_flags(mixed_text)
    assert result.is_emergency is True, "Emergency warning was masked by benign intake text!"
    assert any("ACUTE_CHEST_PAIN_CARDIAC" in ind for ind in result.matched_indicators)
    assert "SEEK IMMEDIATE EMERGENCY MEDICAL CARE" in result.suggested_action


def test_emergency_state_persists_in_session() -> None:
    """A session flagged with an emergency must retain its emergency banner in the final draft."""
    session = IntakeSession(
        session_id="session_persist_test",
        chief_complaint="Chest tightness and dyspnea",
        red_flag_triggered=True,
        red_flag_details=RedFlagResult(
            is_emergency=True,
            matched_indicators=["ACUTE_CHEST_PAIN_CARDIAC: Crushing chest pain"],
            safety_message="Emergency cardiac indicators detected.",
            suggested_action="Call emergency services immediately.",
        ),
    )

    # Patient subsequently enters benign medication info
    extracted = extract_clinical_facts("Taking Metformin 500mg daily", source_type=ProvenanceType.PATIENT_REPORTED)
    session.extracted_facts = extracted
    session.timeline_result = detect_conflicts_and_timeline(extracted)

    # Draft must still prominently highlight the emergency warning
    draft = synthesize_clinical_draft(session)
    assert draft.has_emergency_warning is True
    assert "EMERGENCY WARNING PATTERN DETECTED" in draft.formatted_markdown
    assert "Call emergency services immediately" in draft.formatted_markdown


def test_conflicting_dosages_not_silently_resolved() -> None:
    """Conflicting dosages from different sources must both be preserved and surfaced."""
    doc_facts = extract_clinical_facts(
        "Discharge Order: Metformin 1000mg twice daily.",
        source_type=ProvenanceType.DOCUMENT_EXTRACTED,
        source_ref="hospital_discharge.pdf",
    )
    patient_facts = extract_clinical_facts(
        "I take Metformin 500mg twice daily because 1000mg upset my stomach.",
        source_type=ProvenanceType.PATIENT_REPORTED,
        source_ref="patient_chat_turn_3",
    )

    combined_meds = [*doc_facts.medications, *patient_facts.medications]
    assert len(combined_meds) == 2, "Failed to preserve both medication records!"

    timeline_res = detect_conflicts_and_timeline(combined_meds)
    assert len(timeline_res.conflicts) == 1
    conflict = timeline_res.conflicts[0]
    assert conflict.category == "medication_dosage"
    assert conflict.severity == ConflictSeverity.CRITICAL

    # Verify both sources are preserved in the conflict record
    assert any("1000mg" in src for src in conflict.conflicting_sources)
    assert any("500mg" in src for src in conflict.conflicting_sources)

    # Verify summary draft exposes the conflict to the clinician
    session = IntakeSession(
        session_id="conflict_test_sess",
        extracted_facts=ExtractionResult(medications=combined_meds),
        timeline_result=timeline_res,
    )
    draft = synthesize_clinical_draft(session)
    assert "Discrepancy #1: Metformin (🔴 CRITICAL)" in draft.formatted_markdown
    assert "1000mg" in draft.formatted_markdown
    assert "500mg" in draft.formatted_markdown


def test_provenance_preservation_across_pipeline() -> None:
    """Facts must preserve their distinct source types and source references end-to-end."""
    doc_text = "Lab Report: Serum Creatinine: 1.6 mg/dL. Rx: Amlodipine 5mg daily."
    extracted = extract_clinical_facts(
        doc_text,
        source_type=ProvenanceType.DOCUMENT_EXTRACTED,
        source_ref="lab_report_nov2024.pdf",
    )

    amlodipine = next(m for m in extracted.medications if m.name == "Amlodipine")
    assert amlodipine.provenance.source_type == ProvenanceType.DOCUMENT_EXTRACTED
    assert amlodipine.provenance.source_ref == "lab_report_nov2024.pdf"

    creat = next(l for l in extracted.lab_results if l.test_name == "Serum Creatinine")
    assert creat.provenance.source_type == ProvenanceType.DOCUMENT_EXTRACTED
    assert creat.provenance.source_ref == "lab_report_nov2024.pdf"

    session = IntakeSession(
        session_id="prov_test_sess",
        extracted_facts=extracted,
        timeline_result=detect_conflicts_and_timeline(extracted),
    )
    draft = synthesize_clinical_draft(session)
    assert "`document_extracted`" in draft.formatted_markdown
    assert "- **Document-Extracted Facts:** 2" in draft.formatted_markdown


def test_zero_fabrication_of_missing_units_and_dosages() -> None:
    """Missing units and dosages must remain None and be surfaced as missing information."""
    raw_text = "Patient takes Atorvastatin. Lab: Potassium 4.8. Total Cholesterol 210."
    extracted = extract_clinical_facts(raw_text, source_type=ProvenanceType.PATIENT_REPORTED)

    # Atorvastatin has no dose
    atorva = next(m for m in extracted.medications if m.name == "Atorvastatin")
    assert atorva.dosage is None
    assert atorva.unit is None

    # Potassium has no unit
    potassium = next(l for l in extracted.lab_results if l.test_name == "Potassium")
    assert potassium.numeric_value == 4.8
    assert potassium.unit is None

    # Total cholesterol has no unit
    chol = next(l for l in extracted.lab_results if l.test_name == "Total Cholesterol")
    assert chol.numeric_value == 210.0
    assert chol.unit is None

    timeline_res = detect_conflicts_and_timeline(extracted)
    missing_fields = [m.field_name for m in timeline_res.missing_information]
    assert "dosage" in missing_fields
    assert "unit" in missing_fields

    session = IntakeSession(
        session_id="missing_check_sess",
        extracted_facts=extracted,
        timeline_result=timeline_res,
    )
    draft = synthesize_clinical_draft(session)
    assert "[Missing unit]" in draft.formatted_markdown
    assert "*Not specified*" in draft.formatted_markdown
    assert "Missing Information & Clinical Verification Checklist" in draft.formatted_markdown
