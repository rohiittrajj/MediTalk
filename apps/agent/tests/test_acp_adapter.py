"""Tests for MediTalk Agent Chat Protocol (ACP) Adapter and Session State Machine.

Verifies:
1. ACP protocol message parsing and receipt acknowledgement generation.
2. Purpose-specific consent verification flow and clinical boundary explanations.
3. Strict multi-turn session state isolation between distinct senders.
4. Permanent emergency red-flag persistence across subsequent turns.
5. Malformed, empty, and unsupported input handling without crashing or state corruption.
6. Graceful error recovery without exposing raw stack traces or patient PII.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Ensure apps/agent root is in sys.path
_agent_root = str(Path(__file__).resolve().parent.parent)
if _agent_root not in sys.path:
    sys.path.insert(0, _agent_root)

from src.session import (
    AgentSession,
    ChatAcknowledgement,
    ChatMessage,
    ConversationState,
    SessionManager,
    TextContent,
    create_acknowledgement,
    create_reply_message,
    parse_incoming_text,
    process_user_turn,
    session_manager,
)


def test_acp_message_parsing() -> None:
    """Extract plain text payload accurately from ACP structures and dicts."""
    # Official dataclass model with TextContent
    msg = ChatMessage(
        msg_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        content=[TextContent(type="text", text="Patient has severe headache.")],
    )
    assert parse_incoming_text(msg) == "Patient has severe headache."

    # Multiple text blocks
    multi_msg = ChatMessage(
        msg_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        content=[
            TextContent(type="text", text="Turn 1 notes."),
            TextContent(type="text", text="Rx: Metformin 500mg daily."),
        ],
    )
    assert parse_incoming_text(multi_msg) == "Turn 1 notes.\nRx: Metformin 500mg daily."

    # Raw dict payload (simulating JSON-RPC / REST webhook)
    dict_msg = {
        "msg_id": str(uuid4()),
        "content": [{"type": "text", "text": "Dict formatted message."}],
    }
    assert parse_incoming_text(dict_msg) == "Dict formatted message."

    # Empty and malformed contents
    empty_msg = ChatMessage(msg_id=uuid4(), timestamp=datetime.now(timezone.utc), content=[])
    assert parse_incoming_text(empty_msg) == ""


def test_acknowledgement_generation() -> None:
    """Generate compliant receipt acknowledgement referencing msg_id."""
    test_id = uuid4()
    ack = create_acknowledgement(test_id)
    assert ack.acknowledged_msg_id == test_id
    assert isinstance(ack.timestamp, datetime)

    reply = create_reply_message("Testing reply message")
    assert reply.msg_id is not None
    assert len(reply.content) == 1
    assert reply.content[0].text == "Testing reply message"


def test_consent_flow() -> None:
    """Verify that consent is mandatory before intake commences."""
    sender_id = f"test_sender_{uuid4().hex[:8]}"
    session = session_manager.get_or_create(sender_id)
    assert not session.consent_granted
    assert session.state == ConversationState.AWAITING_CONSENT

    # Turn 1: User sends greeting without consent
    res1 = process_user_turn(sender_id, "Hello, can you help me?")
    assert "Welcome to MediTalk" in res1
    assert "do you consent" in res1.lower()
    assert "not autonomously diagnose" in res1.lower()
    assert not session.consent_granted
    assert session.state == ConversationState.AWAITING_CONSENT

    # Turn 2: User provides positive consent
    res2 = process_user_turn(sender_id, "Yes, I consent to proceed.")
    assert "Consent Recorded" in res2
    assert "chief complaint" in res2.lower()
    assert session.consent_granted is True
    assert session.consent_timestamp is not None
    assert session.state == ConversationState.INTAKE_ACTIVE


def test_multi_turn_state_isolation() -> None:
    """Ensure two distinct senders have strictly isolated intake sessions."""
    alice_id = f"sender_alice_{uuid4().hex[:8]}"
    bob_id = f"sender_bob_{uuid4().hex[:8]}"

    # Alice gives consent and enters diabetic history
    process_user_turn(alice_id, "I consent")
    process_user_turn(alice_id, "Rx: Metformin 1000mg twice daily for Type 2 Diabetes.")

    # Bob gives consent and enters asthma history
    process_user_turn(bob_id, "Yes I consent")
    process_user_turn(bob_id, "Rx: Albuterol inhaler 2 puffs as needed for Asthma.")

    alice_session = session_manager.get_or_create(alice_id)
    bob_session = session_manager.get_or_create(bob_id)

    # Alice must have Metformin and Type 2 Diabetes, but NO Albuterol or Asthma
    alice_meds = [m.name for m in alice_session.extracted_facts.medications]
    alice_conds = [c.name for c in alice_session.extracted_facts.conditions]
    assert "Metformin" in alice_meds
    assert "Type 2 Diabetes" in alice_conds
    assert "Albuterol" not in alice_meds
    assert "Asthma" not in alice_conds

    # Bob must have Albuterol and Asthma, but NO Metformin or Diabetes
    bob_meds = [m.name for m in bob_session.extracted_facts.medications]
    bob_conds = [c.name for c in bob_session.extracted_facts.conditions]
    assert "Albuterol" in bob_meds
    assert "Asthma" in bob_conds
    assert "Metformin" not in bob_meds
    assert "Type 2 Diabetes" not in bob_conds


def test_emergency_persistence_in_conversation() -> None:
    """A detected emergency must alert immediately and persist across subsequent turns."""
    sender_id = f"sender_emergency_{uuid4().hex[:8]}"
    process_user_turn(sender_id, "I consent")

    # Turn 1: Patient reports crushing chest pain and shortness of breath
    emergency_msg = "I have sudden crushing chest pain and shortness of breath."
    res1 = process_user_turn(sender_id, emergency_msg)
    assert "CRITICAL EMERGENCY ALERT" in res1
    assert "SEEK IMMEDIATE EMERGENCY MEDICAL CARE" in res1

    session = session_manager.get_or_create(sender_id)
    assert session.red_flag_triggered is True

    # Turn 2: Patient subsequently sends a benign message
    res2 = process_user_turn(sender_id, "I also take Omeprazole 20mg daily for acid reflux.")
    # The response must still prominently carry the prior emergency alert!
    assert "PRIOR EMERGENCY ALERT" in res2
    assert "Omeprazole" in res2

    # Turn 3: Patient asks for summary
    res3 = process_user_turn(sender_id, "Please generate my summary draft.")
    assert "EMERGENCY WARNING PATTERN DETECTED" in res3
    assert "MEDITALK CLINICAL PREPARATION DRAFT" in res3


def test_malformed_and_empty_input_handling() -> None:
    """Empty strings, whitespace, and None must return helpful guidance without crashing."""
    sender_id = f"sender_empty_{uuid4().hex[:8]}"

    res_empty = process_user_turn(sender_id, "")
    assert "didn't receive any text" in res_empty

    res_spaces = process_user_turn(sender_id, "     \n\t  ")
    assert "didn't receive any text" in res_spaces

    res_none = process_user_turn(sender_id, None)
    assert "didn't receive any text" in res_none


def test_conflict_detection_surfaced_in_conversation() -> None:
    """When contradictory medication doses are entered across turns, the agent flags it in dialogue."""
    sender_id = f"sender_conflict_{uuid4().hex[:8]}"
    process_user_turn(sender_id, "I consent")

    # Turn 1: Document says Lisinopril 10mg
    process_user_turn(sender_id, "Prescription: Lisinopril 10mg daily.")

    # Turn 2: Patient says taking Lisinopril 20mg
    res2 = process_user_turn(sender_id, "Actually my pill bottle says Lisinopril 20mg daily.")
    assert "Discrepancy Detected" in res2
    assert "Lisinopril" in res2
    assert "flagged this discrepancy for your doctor" in res2.lower()


class MockContext:
    """Mock uAgents Context recording outbound messages."""

    def __init__(self) -> None:
        self.sent_messages: list[tuple[str, Any]] = []

    async def send(self, sender: str, msg: Any) -> None:
        self.sent_messages.append((sender, msg))


def test_live_handler_acknowledgement_and_reply() -> None:
    """Verify live ACP handler acknowledges receipt and dispatches a valid ChatMessage reply."""
    import asyncio
    from src.agent import on_chat_message

    mock_ctx = MockContext()
    sender = f"sender_live_{uuid4().hex[:8]}"
    msg_id = uuid4()
    msg = ChatMessage(
        msg_id=msg_id,
        timestamp=datetime.now(timezone.utc),
        content=[TextContent(type="text", text="Hello")],
    )

    asyncio.run(on_chat_message(mock_ctx, sender, msg))

    assert len(mock_ctx.sent_messages) == 2
    # 1. Receipt acknowledgement
    ack_sender, ack_msg = mock_ctx.sent_messages[0]
    assert ack_sender == sender
    assert ack_msg.acknowledged_msg_id == msg_id

    # 2. Outbound reply
    reply_sender, reply_msg = mock_ctx.sent_messages[1]
    assert reply_sender == sender
    assert len(reply_msg.content) >= 1
    assert "Welcome to MediTalk" in reply_msg.content[0].text


def test_live_handler_multi_text_blocks() -> None:
    """Verify handling of messages with multiple text content blocks."""
    import asyncio
    from src.agent import on_chat_message

    mock_ctx = MockContext()
    sender = f"sender_live_multi_{uuid4().hex[:8]}"
    msg_id = uuid4()
    msg = ChatMessage(
        msg_id=msg_id,
        timestamp=datetime.now(timezone.utc),
        content=[
            TextContent(type="text", text="I consent."),
            TextContent(type="text", text="Rx: Metformin 500mg twice daily."),
        ],
    )

    asyncio.run(on_chat_message(mock_ctx, sender, msg))
    assert len(mock_ctx.sent_messages) == 2
    ack = mock_ctx.sent_messages[0][1]
    assert ack.acknowledged_msg_id == msg_id

    reply = mock_ctx.sent_messages[1][1]
    assert "Consent Recorded" in reply.content[0].text or "Metformin" in reply.content[0].text


def test_live_handler_unsupported_content_safety() -> None:
    """Verify handler safely processes unsupported/empty payloads without throwing exceptions."""
    import asyncio
    from src.agent import on_chat_message

    mock_ctx = MockContext()
    sender = f"sender_unsupported_{uuid4().hex[:8]}"
    msg_id = uuid4()
    msg = ChatMessage(
        msg_id=msg_id,
        timestamp=datetime.now(timezone.utc),
        content=[{"unexpected_key": 12345}, 42, None],
    )

    asyncio.run(on_chat_message(mock_ctx, sender, msg))
    assert len(mock_ctx.sent_messages) == 2
    ack = mock_ctx.sent_messages[0][1]
    assert ack.acknowledged_msg_id == msg_id
    reply = mock_ctx.sent_messages[1][1]
    assert "didn't receive any text" in reply.content[0].text


def test_storage_persistence_across_process_restart() -> None:
    """Verify that when ctx.storage is provided, session and emergency state survive an in-memory reset."""
    class MockStorageStore:
        def __init__(self) -> None:
            self._data: dict[str, Any] = {}

        def get(self, key: str, default: Any = None) -> Any:
            return self._data.get(key, default)

        def set(self, key: str, value: Any) -> None:
            self._data[key] = value

        def __contains__(self, key: str) -> bool:
            return key in self._data

        def __getitem__(self, key: str) -> Any:
            return self._data[key]

    class MockStorageContext:
        def __init__(self) -> None:
            self.storage = MockStorageStore()

    mock_ctx = MockStorageContext()
    sender_id = f"sender_storage_{uuid4().hex[:8]}"

    # Turn 1: Grant consent
    process_user_turn(sender_id, "I consent", ctx=mock_ctx)
    assert f"session_{sender_id}" in mock_ctx.storage

    # Turn 2: Emergency trigger
    process_user_turn(sender_id, "Crushing chest pain and gasping for air", ctx=mock_ctx)
    saved_state = mock_ctx.storage[f"session_{sender_id}"]
    assert saved_state["red_flag_triggered"] is True

    # Simulate process restart by resetting in-memory session manager
    session_manager.reset_session(sender_id)
    assert not session_manager.get_or_create(sender_id).red_flag_triggered

    # Turn 3: Subsequent turn restoring from storage
    res3 = process_user_turn(sender_id, "Also take Lisinopril 10mg", ctx=mock_ctx)
    assert "PRIOR EMERGENCY ALERT" in res3
    assert "Lisinopril" in res3
    assert mock_ctx.storage[f"session_{sender_id}"]["red_flag_triggered"] is True


def test_live_agent_initialization() -> None:
    """Verify live uAgent instance initializes with ACP protocol when uagents is available."""
    import asyncio
    from src.agent import UAGENTS_AVAILABLE, create_agent

    if UAGENTS_AVAILABLE:
        agent = create_agent()
        assert agent is not None
        assert agent.name == "meditalk_agent"
        assert agent.address.startswith("agent1")
        if hasattr(agent, "_loop") and agent._loop:
            tasks = [t for t in asyncio.all_tasks(agent._loop) if not t.done()]
            for t in tasks:
                t.cancel()
            if tasks:
                agent._loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

