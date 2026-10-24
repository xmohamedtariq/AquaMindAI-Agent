from enum import Enum
from typing import Any

from pydantic import BaseModel

from src.agent.state import (
    AgentState,
    AgentStatus,
    TerminationReason,
)


class ReflectionDecision(str, Enum):
    """Possible decisions after the reflection phase."""

    CONTINUE = "continue"
    RETRY = "retry"
    REQUEST_APPROVAL = "request_approval"
    STOP = "stop"


class ReflectionResult(BaseModel):
    """Structured result produced by the reflection phase."""

    decision: ReflectionDecision
    reason: str

    termination_reason: TerminationReason | None = None

    recoverable: bool = False


class Reflector:
    """
    Evaluate observations after every AquaMind action.

    The reflector determines whether AquaMind should:

    - continue execution
    - retry an action
    - request human approval
    - terminate safely
    """

    MAX_RECOVERY_ATTEMPTS = 2

    @staticmethod
    def _record(
        state: AgentState,
        action: str,
        result: ReflectionResult,
    ) -> ReflectionResult:
        """Store reflection output in the agent state."""

        state.add_reflection(
            action=action,
            decision=result.decision.value,
            reason=result.reason,
        )

        return result

    def _handle_failure(
        self,
        state: AgentState,
        action: str,
        recoverable: bool,
    ) -> ReflectionResult:
        """
        Process recoverable and non-recoverable failures.
        """

        if not recoverable:
            return self._record(
                state,
                action,
                ReflectionResult(
                    decision=ReflectionDecision.STOP,
                    reason=(
                        f"Action '{action}' failed and "
                        "cannot be safely recovered."
                    ),
                    termination_reason=(
                        TerminationReason.NON_RECOVERABLE_ERROR
                    ),
                ),
            )

        attempts = state.increment_recovery(
            action
        )

        if attempts <= self.MAX_RECOVERY_ATTEMPTS:
            return self._record(
                state,
                action,
                ReflectionResult(
                    decision=ReflectionDecision.RETRY,
                    reason=(
                        f"Action '{action}' encountered "
                        "a recoverable problem. "
                        f"Recovery attempt "
                        f"{attempts}/"
                        f"{self.MAX_RECOVERY_ATTEMPTS}."
                    ),
                    recoverable=True,
                ),
            )

        return self._record(
            state,
            action,
            ReflectionResult(
                decision=ReflectionDecision.STOP,
                reason=(
                    f"Action '{action}' exceeded "
                    "the maximum recovery attempts."
                ),
                termination_reason=(
                    TerminationReason.NON_RECOVERABLE_ERROR
                ),
            ),
        )

    def reflect(
        self,
        state: AgentState,
        action: str,
        observation: Any = None,
        error: str | None = None,
        permission_required: bool = False,
        safety_blocked: bool = False,
    ) -> ReflectionResult:
        """Evaluate the latest AquaMind action."""

        state.status = AgentStatus.REFLECTING

        # Safety takes highest priority.
        if safety_blocked:
            return self._record(
                state,
                action,
                ReflectionResult(
                    decision=ReflectionDecision.STOP,
                    reason=(
                        "Execution was blocked because "
                        "the requested action violates "
                        "the AquaMind safety policy."
                    ),
                    termination_reason=(
                        TerminationReason.SAFETY_BLOCK
                    ),
                ),
            )

        # Sensitive operations require human approval.
        if permission_required:
            return self._record(
                state,
                action,
                ReflectionResult(
                    decision=(
                        ReflectionDecision.REQUEST_APPROVAL
                    ),
                    reason=(
                        "The requested operation requires "
                        "explicit human authorization."
                    ),
                    termination_reason=(
                        TerminationReason
                        .HUMAN_AUTHORIZATION_REQUIRED
                    ),
                ),
            )

        # Runtime or tool failure.
        if error is not None:
            return self._handle_failure(
                state=state,
                action=action,
                recoverable=True,
            )

        # Structured observation analysis.
        if isinstance(
            observation,
            dict,
        ):

            if observation.get(
                "insufficient_evidence",
                False,
            ):
                return self._record(
                    state,
                    action,
                    ReflectionResult(
                        decision=ReflectionDecision.STOP,
                        reason=(
                            "Available evidence is "
                            "insufficient for a responsible "
                            "operational diagnosis."
                        ),
                        termination_reason=(
                            TerminationReason
                            .INSUFFICIENT_EVIDENCE
                        ),
                    ),
                )

            if observation.get(
                "success"
            ) is False:

                return self._handle_failure(
                    state=state,
                    action=action,
                    recoverable=observation.get(
                        "recoverable",
                        False,
                    ),
                )

        # Normal successful action.
        return self._record(
            state,
            action,
            ReflectionResult(
                decision=ReflectionDecision.CONTINUE,
                reason=(
                    f"Action '{action}' completed "
                    "successfully. Investigation may continue."
                ),
            ),
        )