from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Current execution status of the AquaMind agent."""

    READY = "ready"
    PLANNING = "planning"
    ACTING = "acting"
    OBSERVING = "observing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_APPROVAL = "waiting_for_approval"


class TerminationReason(str, Enum):
    """Supported reasons for terminating an AquaMind investigation."""

    FINAL_ANSWER = "FINAL_ANSWER"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    HUMAN_AUTHORIZATION_REQUIRED = "HUMAN_AUTHORIZATION_REQUIRED"
    MAX_TURNS_REACHED = "MAX_TURNS_REACHED"
    MAX_TOOL_CALLS_REACHED = "MAX_TOOL_CALLS_REACHED"
    BUDGET_LIMIT_REACHED = "BUDGET_LIMIT_REACHED"
    NON_RECOVERABLE_ERROR = "NON_RECOVERABLE_ERROR"
    SAFETY_BLOCK = "SAFETY_BLOCK"


class AgentState(BaseModel):
    """
    Runtime state for one AquaMindAI-Agent investigation.

    Execution lifecycle:

    REASON -> ACT -> OBSERVE -> REFLECT

    ``react_trace`` contains concise, audit-safe decision summaries.
    It is intentionally not a private chain-of-thought transcript.
    """

    task_id: str
    user_request: str

    plant_id: str = "demo-plant"

    status: AgentStatus = AgentStatus.READY

    # Execution counters
    turn_count: int = 0
    tool_call_count: int = 0

    # Hard execution limits
    max_turns: int = 12
    max_tool_calls: int = 20
    budget_cap_usd: float = 0.10

    # Cost tracking
    cumulative_cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0

    # Agent investigation artifacts
    plan: list[str] = Field(default_factory=list)

    observations: list[dict[str, Any]] = Field(
        default_factory=list
    )

    evidence: list[dict[str, Any]] = Field(
        default_factory=list
    )

    hypotheses: list[dict[str, Any]] = Field(
        default_factory=list
    )

    recommendations: list[str] = Field(
        default_factory=list
    )

    # Optional plant/operator context supplied as structured evidence.
    # Runtime validation prevents unknown fields from entering the
    # source-grounded diagnostic engine.
    diagnostic_context: dict[str, Any] = Field(
        default_factory=dict
    )

    # Audit-safe ReAct trace. These are decision summaries, not hidden
    # chain-of-thought content.
    react_trace: list[dict[str, Any]] = Field(
        default_factory=list
    )

    # Reflection and recovery
    reflection_notes: list[dict[str, Any]] = Field(
        default_factory=list
    )

    recovery_attempts: dict[str, int] = Field(
        default_factory=dict
    )

    # Runtime information
    current_action: str | None = None
    last_tool: str | None = None
    last_error: str | None = None

    # Final result
    final_answer: str | None = None

    termination_reason: TerminationReason | None = None

    def add_observation(
        self,
        source: str,
        content: Any,
    ) -> None:
        """Store an observation produced during execution."""

        self.observations.append(
            {
                "source": source,
                "content": content,
            }
        )

    def add_evidence(
        self,
        evidence_type: str,
        description: str,
        value: Any = None,
    ) -> None:
        """Store evidence used during investigation."""

        self.evidence.append(
            {
                "type": evidence_type,
                "description": description,
                "value": value,
            }
        )

    def add_react_event(
        self,
        *,
        phase: str,
        decision_summary: str,
        action: str | None = None,
        status: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Append one audit-safe ReAct event.

        The event records only the operational decision summary needed
        to understand agent behavior. It deliberately excludes private
        chain-of-thought reasoning.
        """

        event: dict[str, Any] = {
            "sequence": len(self.react_trace) + 1,
            "turn": self.turn_count,
            "phase": phase,
            "decision_summary": decision_summary,
        }

        if action is not None:
            event["action"] = action

        if status is not None:
            event["status"] = status

        if details:
            event["details"] = details

        self.react_trace.append(event)

    def add_cost(
        self,
        cost_usd: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Update task-level model cost and token usage."""

        self.cumulative_cost_usd += cost_usd
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def add_reflection(
        self,
        action: str,
        decision: str,
        reason: str,
    ) -> None:
        """Store a reflection decision for auditability."""

        self.reflection_notes.append(
            {
                "action": action,
                "decision": decision,
                "reason": reason,
            }
        )

    def recovery_count(
        self,
        action: str,
    ) -> int:
        """Return recovery attempts for an action."""

        return self.recovery_attempts.get(
            action,
            0,
        )

    def increment_recovery(
        self,
        action: str,
    ) -> int:
        """Increment recovery attempts for an action."""

        self.recovery_attempts[action] = (
            self.recovery_attempts.get(
                action,
                0,
            )
            + 1
        )

        return self.recovery_attempts[action]

    def budget_exceeded(self) -> bool:
        """Check whether the task budget has been exhausted."""

        return (
            self.cumulative_cost_usd
            >= self.budget_cap_usd
        )

    def max_turns_reached(self) -> bool:
        """Check whether maximum agent turns were reached."""

        return (
            self.turn_count
            >= self.max_turns
        )

    def max_tool_calls_reached(self) -> bool:
        """Check whether maximum tool calls were reached."""

        return (
            self.tool_call_count
            >= self.max_tool_calls
        )

    def terminate(
        self,
        reason: TerminationReason,
        final_answer: str | None = None,
    ) -> None:
        """Terminate the current AquaMind investigation."""

        self.termination_reason = reason
        self.final_answer = final_answer

        if reason == TerminationReason.FINAL_ANSWER:
            self.status = AgentStatus.COMPLETED

        elif (
            reason
            == TerminationReason.HUMAN_AUTHORIZATION_REQUIRED
        ):
            self.status = AgentStatus.WAITING_FOR_APPROVAL

        else:
            self.status = AgentStatus.FAILED
