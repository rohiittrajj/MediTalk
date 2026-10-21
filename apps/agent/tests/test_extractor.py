"""Tests for extract_clinical_facts.

Verifies accurate extraction of medications, conditions, allergies, and lab values,
preserving provenance and ensuring no missing values (units, dosages) are fabricated.
All scenarios use synthetic clinical data.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure apps/agent root is in sys.path
_agent_root = str(Path(__file__).resolve().parent.parent)
if _agent_root not in sys.path:
    sys.path.insert(0, _agent_root)

from src.extractor import extract_clinical_facts
from src.models import ProvenanceType


def test_empty_and_whitespace_input() -> None:
    """Empty inputs should yield empty extraction results without errors."""
    res_empty = extract_clinical_facts("")
    assert res_empty.medications == []
    assert res_empty.conditions == []
    assert res_empty.allergies == []
    assert res_empty.lab_results == []

    res_none = extract_clinical_facts(None)
    assert res_none.medications == []


def test_medication_extraction_with_dosage_and_frequency() -> None:
    """Extract medication name, dose, unit, and frequency accurately."""
    note = "Patient is currently taking Metformin 500mg twice daily and Lisinopril 10 mg once daily."
    res = extract_clinical_facts(note, source_type=ProvenanceType.PATIENT_REPORTED)

    assert len(res.medications) >= 2
    metformin = next((m for m in res.medications if m.name == "Metformin"), None)
    assert metformin is not None
    assert metformin.dosage == "500"
    assert metformin.unit.lower() == "mg"
    assert metformin.frequency.lower() == "twice daily"
    assert metformin.status == "active"
    assert metformin.provenance.source_type == ProvenanceType.PATIENT_REPORTED

    lisinopril = next((m for m in res.medications if m.name == "Lisinopril"), None)
    assert lisinopril is not None
    assert lisinopril.dosage == "10"
    assert lisinopril.unit.lower() == "mg"
    assert lisinopril.frequency.lower() == "once daily"


def test_medication_with_missing_dosage_is_not_fabricated() -> None:
    """If a patient mentions a drug without dose, dosage must remain None."""
    note = "I take Aspirin for heart health and Atorvastatin at bedtime."
    res = extract_clinical_facts(note)

    aspirin = next((m for m in res.medications if m.name == "Aspirin"), None)
    assert aspirin is not None
    assert aspirin.dosage is None
    assert aspirin.unit is None


def test_allergy_denial_nkda() -> None:
    """Explicit statement of no known allergies must be recorded as a denial."""
    note = "Patient has No Known Drug Allergies (NKDA). Regular diet."
    res = extract_clinical_facts(note)

    assert len(res.allergies) == 1
    assert res.allergies[0].is_denied
    assert "No Known Drug Allergies" in res.allergies[0].allergen


def test_specific_allergy_extraction() -> None:
    """Extract specific allergens and associated reactions."""
    note = "Allergic to Penicillin: causes severe hives and swelling."
    res = extract_clinical_facts(note)

    assert len(res.allergies) >= 1
    penicillin_allergy = next((a for a in res.allergies if "Penicillin" in a.allergen), None)
    assert penicillin_allergy is not None
    assert not penicillin_allergy.is_denied
    assert "hives" in (penicillin_allergy.reaction or "").lower()


def test_conditions_active_and_historical() -> None:
    """Extract active conditions and distinguish historical/resolved conditions."""
    note = "Assessment: Type 2 Diabetes, Hypertension. History of Asthma resolved in childhood."
    res = extract_clinical_facts(note)

    names = [c.name for c in res.conditions]
    assert "Type 2 Diabetes" in names
    assert "Hypertension" in names
    assert "Asthma" in names

    asthma = next(c for c in res.conditions if c.name == "Asthma")
    assert asthma.status == "historical"


def test_laboratory_extraction_with_units_and_missing_units() -> None:
    """Extract laboratory test names, values, units, reference ranges without inventing missing units."""
    note = (
        "Lab Report 2024-05-10: HbA1c: 7.2% (ref 4.0 - 5.6). "
        "Serum Creatinine: 1.8 mg/dL (ref 0.6 - 1.2). "
        "Potassium: 4.5 mmol/L. "
        "Blood Pressure: 130/80 mmHg. "
        "Fasting Glucose: 140"
    )
    res = extract_clinical_facts(note, source_type=ProvenanceType.DOCUMENT_EXTRACTED, source_ref="synthetic_lab.pdf")

    # HbA1c
    hba1c = next((l for l in res.lab_results if l.test_name == "HbA1c"), None)
    assert hba1c is not None
    assert hba1c.numeric_value == 7.2
    assert hba1c.unit == "%"
    assert hba1c.reference_range == "4.0 - 5.6"
    assert hba1c.provenance.source_ref == "synthetic_lab.pdf"

    # Creatinine
    creat = next((l for l in res.lab_results if l.test_name == "Serum Creatinine"), None)
    assert creat is not None
    assert creat.numeric_value == 1.8
    assert creat.unit == "mg/dL"

    # Blood Pressure (string value format)
    bp = next((l for l in res.lab_results if l.test_name in {"Blood Pressure", "BP"}), None)
    assert bp is not None
    assert bp.string_value == "130/80"
    assert bp.unit == "mmHg"

    # Fasting Glucose without unit: unit must be None, NOT guessed as mg/dL!
    glucose = next((l for l in res.lab_results if l.test_name == "Fasting Glucose"), None)
    assert glucose is not None
    assert glucose.numeric_value == 140.0
    assert glucose.unit is None, "Missing unit must remain None; never fabricate units!"
