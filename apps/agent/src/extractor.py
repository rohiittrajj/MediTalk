"""Deterministic Clinical Fact & Document Extractor for MediTalk.

Extracts structured medical facts from patient messages or pasted medical notes:
- Conditions & diagnoses
- Medications, dosages, units, and frequencies
- Allergies & adverse reactions (including explicit denials like NKDA)
- Laboratory tests, numeric values, units, reference ranges, and dates

CRITICAL SAFETY RULES:
- Never invent missing facts, units, dosages, or dates.
- Unsupported or unstated fields remain None.
- Preserves source provenance for every extracted fact.
"""

from __future__ import annotations

import re
from typing import Any

from .models import (
    AllergyFact,
    ConditionFact,
    ExtractionResult,
    LabResultFact,
    MedicationFact,
    ProvenanceRecord,
    ProvenanceType,
)

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
