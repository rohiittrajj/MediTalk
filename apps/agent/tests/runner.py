"""Lightweight standalone test runner using only Python standard library.

Enables running all agent tests without requiring external test runner packages.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

# Add apps/agent to sys.path
agent_root = Path(__file__).resolve().parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

from tests import (
    test_acp_adapter,
    test_bundle,
    test_extractor,
    test_red_flags,
    test_safety_and_provenance,
    test_summary,
    test_timeline,
)

TEST_MODULES = [
    test_red_flags,
    test_extractor,
    test_timeline,
    test_summary,
    test_safety_and_provenance,
    test_acp_adapter,
    test_bundle,
]


def run_all_tests() -> int:
    total_passed = 0
    total_failed = 0
    failures: list[tuple[str, str, Exception]] = []

    print("=" * 70)
    print("MediTalk Phase 1: Clinical Tools Test Suite (Standalone Runner)")
    print("=" * 70)

    for mod in TEST_MODULES:
        mod_name = mod.__name__.split(".")[-1]
        print(f"\nRunning tests in {mod_name}...")
        test_funcs = [
            (name, func)
            for name, func in inspect.getmembers(mod, inspect.isfunction)
            if name.startswith("test_")
        ]

        for name, func in test_funcs:
            try:
                func()
                print(f"  [PASS] {name}")
                total_passed += 1
            except Exception as exc:
                print(f"  [FAIL] {name}: {exc}")
                total_failed += 1
                failures.append((mod_name, name, exc))

    print("\n" + "=" * 70)
    print(f"Summary: {total_passed} passed, {total_failed} failed.")
    print("=" * 70)

    if failures:
        print("\nFailure Details:")
        import traceback
        for mod_name, name, exc in failures:
            print(f"\n--- {mod_name}.{name} ---")
            traceback.print_exception(type(exc), exc, exc.__traceback__)
        return 1

    print("\nALL CLINICAL TOOL TESTS PASSED SUCCESSFULLY.")
    return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
