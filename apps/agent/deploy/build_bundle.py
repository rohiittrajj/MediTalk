"""MediTalk Build Script: Generates a self-contained Agentverse Hosted Agent bundle.

This script compiles the modular source code from `apps/agent/src/` into a single,
self-contained Python script `apps/agent/deploy/agentverse_bundle.py` suitable for
direct deployment in the Agentverse Hosted Agent browser editor.

Single Source of Truth Mandate:
- DO NOT manually edit `apps/agent/deploy/agentverse_bundle.py`.
- Always edit `apps/agent/src/` and re-run this builder script:
    python apps/agent/deploy/build_bundle.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def clean_source_lines(content: str) -> list[str]:
    """Strip __future__ annotations, docstring-only headers, and local intra-package imports."""
    cleaned = []
    lines = content.splitlines()
    in_initial_docstring = False
    in_skipped_import = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track and keep module docstrings if desired, or skip initial module header
        if i == 0 and (stripped.startswith('"""') or stripped.startswith("'''")):
            in_initial_docstring = True
            if (stripped.endswith('"""') or stripped.endswith("'''")) and len(stripped) > 3:
                in_initial_docstring = False
            continue

        if in_initial_docstring:
            if stripped.endswith('"""') or stripped.endswith("'''"):
                in_initial_docstring = False
            continue

        # If we are inside a multi-line relative import, skip lines until closing paren
        if in_skipped_import:
            if ")" in stripped:
                in_skipped_import = False
            continue

        # Skip future annotations (we put one at the top of the bundle)
        if stripped == "from __future__ import annotations":
            continue

        # Skip local intra-package imports (single or multi-line)
        if re.match(r"^from\s+(\.|src\.)\w+\s+import", stripped):
            if "(" in stripped and ")" not in stripped:
                in_skipped_import = True
            continue

        if re.match(r"^import\s+src\.", stripped):
            continue
        if "_agent_root" in stripped:
            continue
        if "sys.path.insert(0, _agent_root)" in stripped:
            continue

        cleaned.append(line)

    return cleaned


def build_agentverse_bundle(src_dir: Path, output_file: Path) -> None:
    """Read source files in dependency order and write single-file bundle."""
    files_in_order = [
        "models.py",
        "red_flags.py",
        "extractor.py",
        "timeline.py",
        "summary.py",
        "tools.py",
        "session.py",
        "agent.py",
    ]

    bundle_parts: list[str] = [
        '"""MediTalk Autonomous Clinical Preparation Agent — Agentverse Hosted Bundle.',
        '',
        'Decentralized Clinical Intake and History Preparation',
        'Repository: https://github.com/rohiittrajj/MediTalk',
        '',
        'CLINICAL SAFETY MANDATES:',
        '1. MediTalk does NOT autonomously diagnose, treat, or prescribe.',
        '2. All generated summaries remain unverified drafts until reviewed and accepted by a clinician.',
        '3. Emergency warning screening is rule-based and non-exhaustive; absence of an alert never rules out an emergency.',
        '4. Never invent missing facts, dosages, units, or dates.',
        '5. Preserves provenance across patient-reported, document-extracted, and clinician-entered data.',
        '6. Explicit informed consent is mandatory prior to clinical intake.',
        '7. Emergency state persists permanently across the entire conversation.',
        '"""',
        '',
        'from __future__ import annotations',
        '',
        'import asyncio',
        'from dataclasses import asdict, dataclass, field',
        'from datetime import datetime, timezone',
        'from enum import Enum',
        'import logging',
        'import os',
        'import re',
        'import sys',
        'from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union',
        'from uuid import UUID, uuid4',
        '',
        '# uAgents and Agent Chat Protocol (ACP) dependencies',
        'try:',
        '    from uagents import Agent, Context, Protocol',
        '    from uagents_core.contrib.protocols.chat import (',
        '        ChatAcknowledgement,',
        '        ChatMessage,',
        '        TextContent,',
        '        chat_protocol_spec,',
        '    )',
        '    UAGENTS_AVAILABLE = True',
        'except ImportError:',
        '    UAGENTS_AVAILABLE = False',
        '',
        'logger = logging.getLogger("meditalk.agent")',
        'logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")',
        '',
        '# Default to hosted mode when running bundle on Agentverse',
        'os.environ.setdefault("AGENTVERSE_HOSTED", "true")',
        '',
    ]

    for fname in files_in_order:
        fpath = src_dir / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Required source file not found: {fpath}")

        raw_content = fpath.read_text(encoding="utf-8")
        cleaned_lines = clean_source_lines(raw_content)

        bundle_parts.append(f"# {'=' * 75}")
        bundle_parts.append(f"# SECTION: {fname}")
        bundle_parts.append(f"# {'=' * 75}\n")
        bundle_parts.extend(cleaned_lines)
        bundle_parts.append("\n")

    final_content = "\n".join(bundle_parts)
    output_file.write_text(final_content, encoding="utf-8")
    print(f"Successfully generated Agentverse bundle at: {output_file} ({len(final_content)} bytes)")


if __name__ == "__main__":
    deploy_dir = Path(__file__).resolve().parent
    src_path = deploy_dir.parent / "src"
    output_bundle = deploy_dir / "agentverse_bundle.py"
    build_agentverse_bundle(src_path, output_bundle)
    print("Bundle generated at:", output_bundle)
