"""MediTalk Autonomous Clinical Preparation Agent.

Implements the Fetch.ai Agent Chat Protocol (ACP) for integration with Agentverse
and conversational interaction inside ASI:One.

OFFICIAL PROTOCOL SPECIFICATION:
- Protocol Spec: `uagents_core.contrib.protocols.chat.chat_protocol_spec`
- Message Models: `ChatMessage`, `ChatAcknowledgement`, `TextContent`
- Routing: Messages dispatched to `@chat_proto.on_message(ChatMessage)`
- Receipt Confirmation: Immediate return of `ChatAcknowledgement` referencing `msg.msg_id`
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Ensure agent package root is in sys.path
_agent_root = str(Path(__file__).resolve().parent.parent)
if _agent_root not in sys.path:
    sys.path.insert(0, _agent_root)

from src.session import (
    create_acknowledgement,
    create_reply_message,
    parse_incoming_text,
    process_user_turn,
)

logger = logging.getLogger("meditalk.agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Environment configuration
AGENT_NAME = os.getenv("AGENT_NAME", "meditalk_agent")
AGENT_SEED = os.getenv("AGENT_SEED", "meditalk_dev_agent_seed_default_dev_only")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8001"))
AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY")

try:
    from uagents import Agent, Context, Protocol
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement,
        ChatMessage,
        TextContent,
        chat_protocol_spec,
    )

    UAGENTS_AVAILABLE = True
except ImportError:
    from src.session import (  # type: ignore[no-redef]
        ChatAcknowledgement,
        ChatMessage,
        TextContent,
    )

    chat_protocol_spec = None  # type: ignore[assignment]
    UAGENTS_AVAILABLE = False


async def on_chat_message(ctx: Any, sender: str, msg: Any) -> None:
    """Handle incoming ACP chat message from ASI:One or peer agent."""
    msg_id = getattr(msg, "msg_id", None) or uuid4()
    logger.info("Received ACP message from sender=%s msg_id=%s", sender, msg_id)

    # 1. Acknowledge receipt immediately (<100ms mandate)
    ack = ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc),
        acknowledged_msg_id=msg_id,
    )
    await ctx.send(sender, ack)

    # 2. Extract text content
    user_text = parse_incoming_text(msg)

    # 3. Process turn through MediTalk state machine
    try:
        reply_text = process_user_turn(sender=sender, raw_text=user_text, ctx=ctx)
    except Exception as exc:
        logger.error("Error processing turn for sender=%s: %s", sender, exc, exc_info=True)
        reply_text = (
            "An unexpected error occurred while processing your message. "
            "Your intake state has been preserved. Please try rephrasing your message."
        )

    # 4. Construct and dispatch ACP ChatMessage reply
    reply_msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=reply_text)],
    )
    await ctx.send(sender, reply_msg)
    logger.info("Dispatched ACP reply to sender=%s", sender)


async def on_chat_ack(ctx: Any, sender: str, msg: Any) -> None:
    """Handle receipt confirmations from client/peer."""
    ack_id = getattr(msg, "acknowledged_msg_id", None)
    logger.info("Sender=%s acknowledged receipt of msg_id=%s", sender, ack_id)


def create_agent() -> Any:
    """Instantiate and configure the MediTalk uAgent with ACP protocol."""
    if not UAGENTS_AVAILABLE:
        raise RuntimeError(
            "uagents library is not installed in the current environment. "
            "Install with: pip install 'uagents>=0.25.5'"
        )

    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Initialize agent (configure mailbox if key is provided)
    agent_kwargs: dict[str, Any] = {
        "name": AGENT_NAME,
        "seed": AGENT_SEED,
        "port": AGENT_PORT,
        "loop": loop,
    }
    if AGENT_MAILBOX_KEY:
        agent_kwargs["mailbox"] = AGENT_MAILBOX_KEY

    agent = Agent(**agent_kwargs)

    # Instantiate the official Chat Protocol
    chat_proto = Protocol(spec=chat_protocol_spec)

    # Register handlers
    chat_proto.on_message(ChatMessage)(on_chat_message)
    chat_proto.on_message(ChatAcknowledgement)(on_chat_ack)

    # Include protocol with manifest publication for Agentverse/ASI:One discovery
    agent.include(chat_proto, publish_manifest=True)
    return agent


# Module-level agent instance for Agentverse Hosted environment
agent: Any = None
if UAGENTS_AVAILABLE and os.getenv("AGENTVERSE_HOSTED", "false").lower() in ("true", "1"):
    try:
        agent = create_agent()
    except Exception as exc:
        logger.warning("Could not auto-instantiate module-level agent: %s", exc)


if __name__ == "__main__":
    if not UAGENTS_AVAILABLE:
        print("\n" + "=" * 70)
        print("MediTalk Clinical Preparation Agent (ACP Adapter)")
        print("=" * 70)
        print("\nNotice: The 'uagents' library is required to run the live networking agent.")
        print("All clinical tools, state machine, and tests are available standalone.")
        print("\nTo run the live agent on Agentverse:")
        print("  1. pip install 'uagents>=0.25.5'")
        print("  2. python -m apps.agent.src.agent")
        print("=" * 70 + "\n")
        sys.exit(0)

    agent_instance = create_agent()
    print(f"Starting {AGENT_NAME} on port {AGENT_PORT}...")
    agent_instance.run()
