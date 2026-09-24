"""
Agent: Orchestrator
==================

Role: Manages state machine transitions, generates user-facing messages.

Input: State, Context Packet
Output: Next state, user message

Model: Strong model (optional — for complex user-facing messages)

TODO (v0.2): Implement.
"""
from __future__ import annotations
from typing import Any


class Orchestrator:
    """Manages state machine + user communication.

    Responsibilities:
    - Read current state from state machine
    - Decide next state based on agent output
    - Generate user-facing messages (confirmation prompts, status updates)
    - Handle error transitions (fall back to MANUAL_REVIEW)

    Design notes:
    - The orchestrator does NOT pick which agent to call; the state machine does.
    - The orchestrator's role is limited to communication + transition logic.
    """

    def __init__(self) -> None:
        # TODO: initialize LLM client for user-facing messages
        pass

    def generate_user_message(self, state: str, context: dict) -> str:
        """Generate a user-facing message for the current state."""
        # TODO (v0.2)
        raise NotImplementedError

    def decide_next_state(self, current: str, agent_output: dict) -> str:
        """Decide next state based on agent output."""
        # TODO (v0.2)
        raise NotImplementedError
