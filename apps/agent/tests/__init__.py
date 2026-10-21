"""Tests for MediTalk Clinical Preparation Agent."""

import sys
from pathlib import Path

# Ensure apps/agent is in sys.path for test runners executing from repository root
_agent_root = str(Path(__file__).resolve().parent.parent)
if _agent_root not in sys.path:
    sys.path.insert(0, _agent_root)

