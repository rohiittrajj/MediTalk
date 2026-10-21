"""Structured Clinical Draft Summary Synthesizer for MediTalk.

Synthesizes an organized, source-aware clinical preparation draft for clinician review.

CLINICAL SAFETY MANDATES:
1. Every summary is an unverified draft pending qualified clinician review.
2. MediTalk does NOT diagnose, prescribe, or provide emergency treatment.
3. Provenance and conflicts must be explicitly visible to the reviewing clinician.
4. Missing facts must be clearly designated, never fabricated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import (
    ClinicalDraft,
    ConflictSeverity,
    IntakeSession,
    ProvenanceType,
)


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
