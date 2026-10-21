"""Conversational Intake State Machine and ACP Turn Processor for MediTalk.

Manages per-sender session state, consent verification, continuous emergency
red-flag screening, fact extraction, conflict tracking, and draft synthesis.

CLINICAL & ETHICAL BOUNDARIES:
1. Consent is strictly required before clinical intake begins.
2. Emergency warnings persist across the entire session; benign turns never clear an alert.
3. Every sender's state is completely isolated; sessions are never mixed.
4. No clinical facts are fabricated. No diagnoses or prescriptions are generated.
5. No raw patient narratives or secrets are logged.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from .models import (
    ClinicalDraft,
    ConflictSeverity,
    ExtractionResult,
    IntakeSession,
    ProvenanceRecord,
    ProvenanceType,
    RedFlagResult,
    TimelineAndConflictResult,
)
from .red_flags import screen_red_flags
from .tools import (
    detect_conflicts_and_timeline,
    extract_clinical_facts,
    synthesize_clinical_draft,
)

logger = logging.getLogger("meditalk.agent.session")


# Try importing official uagents-core ACP models; fallback to identical pure-python schemas
try:
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement as OfficialChatAcknowledgement,
        ChatMessage as OfficialChatMessage,
        TextContent as OfficialTextContent,
    )
    HAS_UAGENTS_CORE = True
except ImportError:
    HAS_UAGENTS_CORE = False


@dataclass
class TextContent:
    """Standardized text content block matching ACP specification."""
    text: str
    type: str = "text"


@dataclass
class ChatMessage:
    """Standardized message model matching ACP specification."""
    msg_id: UUID | str
    timestamp: datetime
    content: list[Any]


@dataclass
class ChatAcknowledgement:
    """Receipt acknowledgement matching ACP specification."""
    timestamp: datetime
    acknowledged_msg_id: UUID | str


class ConversationState(str, Enum):
    """Lifecycle states of a patient intake session."""
    AWAITING_CONSENT = "awaiting_consent"
    INTAKE_ACTIVE = "intake_active"
    DRAFT_SYNTHESIZED = "draft_synthesized"


@dataclass
class AgentSession:
    """Per-sender isolated intake session state."""
    sender_id: str
    state: ConversationState = ConversationState.AWAITING_CONSENT
    consent_granted: bool = False
    consent_timestamp: str | None = None
    chief_complaint: str = ""
    hpi_narrative: str = ""
    red_flag_triggered: bool = False
    red_flag_details: RedFlagResult | None = None
    extracted_facts: ExtractionResult = field(default_factory=ExtractionResult)
    timeline_result: TimelineAndConflictResult = field(default_factory=TimelineAndConflictResult)
    last_interaction: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "state": self.state.value if isinstance(self.state, ConversationState) else str(self.state),
            "consent_granted": self.consent_granted,
            "consent_timestamp": self.consent_timestamp,
            "chief_complaint": self.chief_complaint,
            "hpi_narrative": self.hpi_narrative,
            "red_flag_triggered": self.red_flag_triggered,
            "red_flag_details": self.red_flag_details.to_dict() if self.red_flag_details else None,
            "extracted_facts": self.extracted_facts.to_dict(),
            "timeline_result": self.timeline_result.to_dict(),
            "last_interaction": self.last_interaction,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentSession:
        session = cls(sender_id=data.get("sender_id", ""))
        try:
            session.state = ConversationState(data.get("state", ConversationState.AWAITING_CONSENT.value))
        except ValueError:
            session.state = ConversationState.AWAITING_CONSENT
        session.consent_granted = data.get("consent_granted", False)
        session.consent_timestamp = data.get("consent_timestamp")
        session.chief_complaint = data.get("chief_complaint", "")
        session.hpi_narrative = data.get("hpi_narrative", "")
        session.red_flag_triggered = data.get("red_flag_triggered", False)
        if data.get("red_flag_details"):
            rf = data["red_flag_details"]
            session.red_flag_details = RedFlagResult(
                is_emergency=rf.get("is_emergency", False),
                matched_indicators=rf.get("matched_indicators", []),
                safety_message=rf.get("safety_message", ""),
                suggested_action=rf.get("suggested_action", ""),
                disclaimer=rf.get("disclaimer", ""),
            )
        session.last_interaction = data.get("last_interaction", "")
        return session


class SessionManager:
    """In-memory session registry with per-sender isolation."""

    def __init__(self) -> None:
        self._sessions: dict[str, AgentSession] = {}

    def get_or_create(self, sender: str) -> AgentSession:
        if sender not in self._sessions:
            self._sessions[sender] = AgentSession(sender_id=sender)
        return self._sessions[sender]

    def reset_session(self, sender: str) -> AgentSession:
        self._sessions[sender] = AgentSession(sender_id=sender)
        return self._sessions[sender]

    def session_count(self) -> int:
        return len(self._sessions)


# Global session manager instance
session_manager = SessionManager()

_CONSENT_POSITIVE_KEYWORDS = {
    "consent", "i consent", "yes", "i agree", "agree", "accept",
    "i accept", "proceed", "sure", "ok", "okay", "start",
}

_SUMMARY_TRIGGER_KEYWORDS = {
    "summary", "draft", "prepare draft", "clinical summary", "prepare my history",
    "ready", "doctor visit", "done", "finished", "generate report",
}


def process_user_turn(sender: str, raw_text: str | None, ctx: Any = None) -> str:
    """Process a single turn from a sender and return the agent's textual response.

    Args:
        sender: Unique sender address or user identifier.
        raw_text: Text extracted from incoming ACP ChatMessage.
        ctx: Optional uAgents Context providing persistent ctx.storage.

    Returns:
        Structured response string adhering to MediTalk clinical guidelines.
    """
    # 0. Load session from ctx.storage if available, else in-memory manager
    if ctx and hasattr(ctx, "storage") and ctx.storage:
        stored = ctx.storage.get(f"session_{sender}")
        if stored and isinstance(stored, dict):
            session = AgentSession.from_dict(stored)
        else:
            session = session_manager.get_or_create(sender)
    else:
        session = session_manager.get_or_create(sender)

    session.last_interaction = datetime.now(timezone.utc).isoformat()

    def _persist_and_return(text: str) -> str:
        if ctx and hasattr(ctx, "storage") and ctx.storage:
            ctx.storage.set(f"session_{sender}", session.to_dict())
        return text

    # 1. Handle empty / whitespace inputs
    if not raw_text or not raw_text.strip():
        logger.info("Empty turn received for sender=%s", sender)
        return _persist_and_return(
            "Hello! I am MediTalk, your clinical history preparation assistant. "
            "I didn't receive any text. Please type your message, symptoms, or "
            "paste your medical notes to begin."
        )

    clean_text = raw_text.strip()
    lower_text = clean_text.lower()

    # 2. EMERGENCY RED-FLAG SCREENING (Evaluated on every incoming turn)
    red_flag_check = screen_red_flags(clean_text)
    if red_flag_check.is_emergency:
        session.red_flag_triggered = True
        session.red_flag_details = red_flag_check
        logger.warning(
            "Emergency warning triggered for sender=%s: %s",
            sender,
            "; ".join(red_flag_check.matched_indicators),
        )
        return _persist_and_return(
            f"🚨 **{red_flag_check.safety_message}**\n\n"
            f"👉 **Action Required:** {red_flag_check.suggested_action}\n\n"
            f"> *{red_flag_check.disclaimer}*"
        )

    # 3. CONSENT VERIFICATION
    if not session.consent_granted:
        # Check if the user is granting consent
        if any(kw in lower_text for kw in _CONSENT_POSITIVE_KEYWORDS):
            session.consent_granted = True
            session.consent_timestamp = datetime.now(timezone.utc).isoformat()
            session.state = ConversationState.INTAKE_ACTIVE
            logger.info("Consent recorded for sender=%s", sender)
            return _persist_and_return(
                "✅ **Consent Recorded.** Thank you.\n\n"
                "Please tell me what brings you in today — what is your **main symptom or chief complaint**? "
                "You can also paste any prescriptions, discharge summaries, or laboratory test reports."
            )
        else:
            # Inform user of purpose and boundaries and request explicit consent
            return _persist_and_return(
                "👋 **Welcome to MediTalk.**\n\n"
                "I am a clinical preparation assistant designed to help you organize your medical "
                "history, medications, and records into a structured draft for your healthcare provider.\n\n"
                "**Clinical Safety Notice & Limitations:**\n"
                "- MediTalk does not autonomously diagnose conditions or prescribe medications.\n"
                "- MediTalk does not provide emergency intervention. If you are experiencing an acute medical emergency, call emergency services immediately.\n"
                "- All summaries are drafts that require review and verification by your clinician.\n\n"
                "To begin, **do you consent** to sharing your health information for clinical preparation? "
                "(Reply **'Yes'** or **'I consent'** to proceed)."
            )

    # 4. ACTIVE INTAKE FLOW (Consent is confirmed)
    # Prefix response with emergency reminder if session previously triggered an alert
    emergency_prefix = ""
    if session.red_flag_triggered and session.red_flag_details:
        emergency_prefix = (
            "⚠️ **PRIOR EMERGENCY ALERT:** Critical symptoms were previously detected during this intake. "
            "If you are experiencing acute distress, seek emergency medical care immediately.\n\n---\n\n"
        )

    # A. Check if the user is requesting draft synthesis
    if any(kw in lower_text for kw in _SUMMARY_TRIGGER_KEYWORDS) and (
        session.chief_complaint or session.extracted_facts.medications or session.extracted_facts.lab_results
    ):
        session.state = ConversationState.DRAFT_SYNTHESIZED
        # Build IntakeSession domain model
        intake_domain_session = IntakeSession(
            session_id=f"sess_{sender[:12]}",
            consent_granted=session.consent_granted,
            consent_timestamp=session.consent_timestamp,
            chief_complaint=session.chief_complaint,
            hpi_narrative=session.hpi_narrative,
            extracted_facts=session.extracted_facts,
            timeline_result=session.timeline_result,
            red_flag_triggered=session.red_flag_triggered,
            red_flag_details=session.red_flag_details,
        )
        draft = synthesize_clinical_draft(intake_domain_session)
        logger.info(
            "Clinical draft synthesized for sender=%s (facts=%d, conflicts=%d)",
            sender,
            draft.fact_count,
            draft.conflict_count,
        )
        return _persist_and_return(
            f"{emergency_prefix}Here is your structured clinical preparation draft for your doctor:\n\n{draft.formatted_markdown}"
        )

    # B. Extract facts from user message
    # Classify source: if text looks like a report or prescription, classify as document_extracted
    source_type = ProvenanceType.PATIENT_REPORTED
    source_ref = "chat_message"
    if any(header in lower_text for header in ["rx:", "prescription:", "discharge summary:", "lab report:", "test results:"]):
        source_type = ProvenanceType.DOCUMENT_EXTRACTED
        source_ref = "pasted_document"

    new_facts = extract_clinical_facts(clean_text, source_type=source_type, source_ref=source_ref)

    # Merge facts into session
    session.extracted_facts.medications.extend(new_facts.medications)
    session.extracted_facts.conditions.extend(new_facts.conditions)
    session.extracted_facts.allergies.extend(new_facts.allergies)
    session.extracted_facts.lab_results.extend(new_facts.lab_results)

    # If chief complaint is not yet recorded and user describes a symptom/complaint
    if not session.chief_complaint:
        session.chief_complaint = clean_text[:200]
    else:
        session.hpi_narrative += ("\n" if session.hpi_narrative else "") + clean_text

    # Run timeline and conflict detection over all accumulated facts
    session.timeline_result = detect_conflicts_and_timeline(session.extracted_facts)

    # Build constructive conversational reply
    reply_lines: list[str] = []

    # Report acknowledged extractions
    items_found: list[str] = []
    if new_facts.medications:
        med_names = [f"{m.name} ({m.dosage or 'dose unstated'}{m.unit or ''})" for m in new_facts.medications]
        items_found.append(f"Medications: {', '.join(med_names)}")
    if new_facts.conditions:
        items_found.append(f"Conditions: {', '.join(c.name for c in new_facts.conditions)}")
    if new_facts.allergies:
        allergy_names = [a.allergen for a in new_facts.allergies]
        items_found.append(f"Allergies: {', '.join(allergy_names)}")
    if new_facts.lab_results:
        lab_names = [f"{l.test_name} ({l.numeric_value or l.string_value} {l.unit or 'no unit'})" for l in new_facts.lab_results]
        items_found.append(f"Investigations: {', '.join(lab_names)}")

    if items_found:
        reply_lines.append("📋 **Noted:** " + "; ".join(items_found) + ".")
    else:
        reply_lines.append("Got it. I have added that to your history.")

    # Prominently surface any critical discrepancies detected
    critical_conflicts = [c for c in session.timeline_result.conflicts if c.severity == ConflictSeverity.CRITICAL]
    if critical_conflicts:
        reply_lines.append("\n⚠️ **Discrepancy Detected:**")
        for conf in critical_conflicts:
            reply_lines.append(f"- {conf.description}")
        reply_lines.append("*I have flagged this discrepancy for your doctor to clarify.*")

    # Missing information prompt
    if session.timeline_result.missing_information:
        missing_sample = session.timeline_result.missing_information[0]
        reply_lines.append(f"\n💡 *Note:* {missing_sample.context}")

    reply_lines.append(
        "\nDo you have any other symptoms, previous lab reports, or allergies to add? "
        "Or type **'summary'** when you are ready to generate your doctor's draft."
    )

    return _persist_and_return(emergency_prefix + "\n".join(reply_lines))


def parse_incoming_text(msg: Any) -> str:
    """Extract plain text payload from an ACP ChatMessage or dict."""
    if hasattr(msg, "content"):
        contents = msg.content
    elif isinstance(msg, dict):
        contents = msg.get("content", [])
    else:
        return ""

    if not isinstance(contents, list):
        return str(contents)

    text_parts: list[str] = []
    for item in contents:
        if isinstance(item, TextContent) or (HAS_UAGENTS_CORE and isinstance(item, OfficialTextContent)):
            text_parts.append(item.text)
        elif hasattr(item, "text"):
            text_parts.append(str(item.text))
        elif isinstance(item, dict) and item.get("type") == "text":
            text_parts.append(str(item.get("text", "")))
        elif isinstance(item, str):
            text_parts.append(item)

    return "\n".join(text_parts).strip()


def create_acknowledgement(msg_id: UUID | str) -> ChatAcknowledgement:
    """Construct an ACP receipt acknowledgement referencing msg_id."""
    return ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc),
        acknowledged_msg_id=msg_id,
    )


def create_reply_message(reply_text: str) -> ChatMessage:
    """Construct an ACP ChatMessage payload containing TextContent."""
    return ChatMessage(
        msg_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        content=[TextContent(type="text", text=reply_text)],
    )
