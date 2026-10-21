"""Timeline sequencing and Clinical Conflict Detection for MediTalk.

Builds chronological event sequences and flags discrepancies across sources:
- Conflicting medication dosages
- Contradictory allergy statements
- Missing laboratory units
- Missing medication dosages and dates

CRITICAL SAFETY RULES:
- Never silently resolve or overwrite conflicting data.
- Surface all discrepancies prominently with severity ratings.
- Clearly identify missing units and dates rather than guessing them.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import (
    AllergyFact,
    ClinicalConflict,
    ConditionFact,
    ConflictSeverity,
    ExtractionResult,
    LabResultFact,
    MedicationFact,
    MissingInfoIndicator,
    ProvenanceRecord,
    ProvenanceType,
    TimelineAndConflictResult,
    TimelineEvent,
)


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
