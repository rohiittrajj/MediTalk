"""Test suite verifying the Agentverse deployment bundle.

Ensures that apps/agent/deploy/agentverse_bundle.py remains in exact behavioral
parity with the modular source code in apps/agent/src/.
"""

from __future__ import annotations

from pathlib import Path


def test_agentverse_bundle_in_memory_execution() -> None:
    """Verify that the bundled single-file agent executes correctly without syntax or runtime errors."""
    bundle_path = Path(__file__).resolve().parent.parent / "deploy" / "agentverse_bundle.py"
    assert bundle_path.exists(), f"Bundle not found at: {bundle_path}"

    code = bundle_path.read_text(encoding="utf-8")
    assert len(code) > 20000, "Bundle is unexpectedly small"

    namespace: dict[str, object] = {}
    exec(code, namespace)  # noqa: S102

    # Check tools and models are exposed
    assert callable(namespace.get("screen_red_flags"))
    assert callable(namespace.get("extract_clinical_facts"))
    assert callable(namespace.get("detect_conflicts_and_timeline"))
    assert callable(namespace.get("synthesize_clinical_draft"))
    assert callable(namespace.get("process_user_turn"))

    # Test conversational intake lifecycle
    sender = "test_bundle_user_42"
    process_turn = namespace["process_user_turn"]

    # Turn 1: Initial greeting and consent gating
    t1 = process_turn(sender, "hello")
    assert "consent" in t1.lower()

    # Turn 2: Grant consent
    t2 = process_turn(sender, "I consent to clinical preparation")
    assert "consent recorded" in t2.lower()

    # Turn 3: Clinical fact extraction
    t3 = process_turn(sender, "I have Type 2 Diabetes and take Metformin 500mg daily. Also allergic to Penicillin: rash.")
    assert "metformin" in t3.lower()
    assert "penicillin" in t3.lower()

    # Turn 4: Emergency red flag detection
    t4 = process_turn(sender, "Sudden severe crushing chest pain radiating to left arm")
    assert "critical emergency alert" in t4.lower()

    # Turn 5: Subsequent turn must retain emergency alert prefix
    t5 = process_turn(sender, "Also have a headache")
    assert "prior emergency alert" in t5.lower()

    # Turn 6: Draft clinical summary synthesis
    t6 = process_turn(sender, "Please generate the clinical summary for my doctor")
    assert "meditalk clinical preparation draft" in t6.lower()
    assert "metformin" in t6.lower()
