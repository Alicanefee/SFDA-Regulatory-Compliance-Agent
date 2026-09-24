"""
SFDA Regulatory Compliance Agent — State Machine
================================================

YAML-driven state machine. The LLM does NOT pick which agent to call;
the state machine does. Agents are deterministic roles defined in YAML.

See docs/PLAN.md §2.2 for the state machine design.

Current state (v0.1 MVP):
- State machine NOT yet implemented
- The MVP main.py runs a single-step RAG + tool use flow
- TODO: Replace with YAML-driven state machine in v0.2

State flow (target):
    UPLOAD → INGEST → CLASSIFY → CONFIRM_CLASS → CHECKLIST → COLLECT → VALIDATE → REPORT → DONE

Each state has:
  - entry_condition: what triggers this state
  - agent: which agent to call
  - output: what data the agent produces
  - next: success transition
  - on_error: failure transition (typically MANUAL_REVIEW)

TODO (v0.2):
1. Define state_machine.yaml
2. Implement YAML loader + state transition logic
3. Replace inline flow in main.py with state machine dispatch
"""

from __future__ import annotations
from enum import Enum
from typing import Any


class State(str, Enum):
    """State machine states. See docs/PLAN.md §2.2."""
    UPLOAD = "UPLOAD"
    INGEST = "INGEST"
    CLASSIFY = "CLASSIFY"
    CONFIRM_CLASS = "CONFIRM_CLASS"
    CHECKLIST = "CHECKLIST"
    COLLECT = "COLLECT"
    VALIDATE = "VALIDATE"
    REPORT = "REPORT"
    DONE = "DONE"
    MANUAL_REVIEW = "MANUAL_REVIEW"  # fallback for any state failure


class StateMachine:
    """YAML-driven state machine. (TODO: implement in v0.2)

    For now, this is a placeholder. The MVP main.py runs a single
    RAG + tool use flow without state transitions.
    """

    def __init__(self, yaml_path: str | None = None) -> None:
        self.yaml_path = yaml_path
        self.current_state = State.UPLOAD
        self.transitions: dict[State, dict[str, Any]] = {}
        # TODO: load from YAML in v0.2

    def next_state(self, current: State, success: bool = True) -> State:
        """Transition to next state based on success/failure."""
        # TODO: implement YAML-driven transitions in v0.2
        if not success:
            return State.MANUAL_REVIEW
        # Linear progression for now
        order = list(State)
        idx = order.index(current)
        return order[min(idx + 1, len(order) - 1)]

    def run(self, context: dict) -> dict:
        """Run the full state machine.

        TODO (v0.2): Implement YAML-driven dispatch.
        For now, see src/main.py for the MVP single-step flow.
        """
        raise NotImplementedError(
            "State machine not yet implemented. See src/main.py for MVP flow."
        )
