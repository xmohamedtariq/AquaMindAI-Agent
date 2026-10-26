from collections.abc import Callable
from typing import Any

from src.agent.planner import (
    AgentAction,
    Planner,
)
from src.agent.reflector import (
    ReflectionDecision,
    ReflectionResult,
    Reflector,
)
from src.agent.state import (
    AgentState,
    AgentStatus,
    TerminationReason,
)


ToolFunction = Callable[
    [AgentState],
    Any,
]


class AgentLoop:
    """
    Core autonomous execution loop for AquaMindAI-Agent.

    Lifecycle:

    REASON
      ->
    ACT
      ->
    OBSERVE
      ->
    REFLECT
      ->
    CONTINUE / RETRY / TERMINATE

    The trace stores concise decision summaries only. It does not
    expose private chain-of-thought reasoning.
    """

    def __init__(
        self,
        tools: dict[
            str,
            ToolFunction,
        ],
        planner: Planner | None = None,
        reflector: Reflector | None = None,
    ) -> None:
        """Initialize the AquaMind autonomous loop."""

        self.tools = tools

        if planner is None:
            self.planner = Planner()
        else:
            self.planner = planner

        if reflector is None:
            self.reflector = Reflector()
        else:
            self.reflector = reflector

    @staticmethod
    def _final_message(
        state: AgentState,
    ) -> str:
        """Return the final investigation message."""

        if (
            state.final_answer
            is not None
        ):
            return state.final_answer

        return (
            "AquaMindAI-Agent completed the "
            "desalination plant investigation."
        )

    @staticmethod
    def _termination_reason(
        reason: TerminationReason | None,
    ) -> TerminationReason:
        """Guarantee that termination always has a reason."""

        if reason is not None:
            return reason

        return (
            TerminationReason
            .NON_RECOVERABLE_ERROR
        )

    @staticmethod
    def _observation_details(
        observation: Any,
    ) -> dict[str, Any]:
        """
        Build an audit-safe observation summary for the ReAct trace.

        Raw sensor rows and full documents are intentionally omitted.
        """

        if not isinstance(
            observation,
            dict,
        ):
            return {
                "result_type":
                    type(
                        observation
                    ).__name__,
            }

        details: dict[str, Any] = {
            "keys": sorted(
                str(key)
                for key
                in observation
            )
        }

        for key in (
            "success",
            "recoverable",
            "diagnosis_status",
            "anomaly_detected",
            "overall_severity",
            "match_count",
            "_permission_required",
            "_safety_blocked",
            "_safety_violation",
        ):
            if key in observation:
                details[key] = (
                    observation[
                        key
                    ]
                )

        return details

    @staticmethod
    def _trace_termination(
        state: AgentState,
        *,
        reason: TerminationReason,
        summary: str,
        action: str | None = None,
    ) -> None:
        """Record one audit-safe termination event."""

        state.add_react_event(
            phase="terminate",
            decision_summary=summary,
            action=action,
            status=reason.value,
        )

    def _terminate_from_reflection(
        self,
        state: AgentState,
        reflection: ReflectionResult,
    ) -> AgentState:
        """Terminate execution using a reflection decision."""

        reason = (
            self._termination_reason(
                reflection
                .termination_reason
            )
        )

        self._trace_termination(
            state,
            reason=reason,
            summary=reflection.reason,
            action=state.current_action,
        )

        state.terminate(
            reason=reason,
            final_answer=(
                reflection.reason
            ),
        )

        return state

    def run(
        self,
        state: AgentState,
    ) -> AgentState:
        """
        Execute the autonomous AquaMind investigation.

        The loop continues until a valid termination
        condition is reached.
        """

        # Build initial plan once.
        if not state.plan:
            self.planner.build_initial_plan(
                state
            )

        while (
            state.termination_reason
            is None
        ):

            # =================================================
            # REASON
            # =================================================

            decision = (
                self.planner.next_action(
                    state
                )
            )

            state.add_react_event(
                phase="reason",
                decision_summary=(
                    decision.reason
                ),
                action=(
                    decision.action.value
                ),
                status="planned",
            )

            # Planner requested termination.
            if (
                decision.action
                == AgentAction.STOP
            ):

                reason = (
                    self._termination_reason(
                        decision
                        .termination_reason
                    )
                )

                self._trace_termination(
                    state,
                    reason=reason,
                    summary=(
                        decision.reason
                    ),
                    action=(
                        decision.action.value
                    ),
                )

                state.terminate(
                    reason=reason,
                    final_answer=(
                        decision.reason
                    ),
                )

                break

            # Investigation completed.
            if (
                decision.action
                == AgentAction.FINALIZE
            ):

                final_message = (
                    self._final_message(
                        state
                    )
                )

                self._trace_termination(
                    state,
                    reason=(
                        TerminationReason
                        .FINAL_ANSWER
                    ),
                    summary=final_message,
                    action=(
                        decision.action.value
                    ),
                )

                state.terminate(
                    reason=(
                        TerminationReason
                        .FINAL_ANSWER
                    ),
                    final_answer=(
                        final_message
                    ),
                )

                break

            action = (
                decision.action.value
            )

            state.current_action = (
                action
            )

            # =================================================
            # TOOL LOOKUP
            # =================================================

            tool = self.tools.get(
                action
            )

            if tool is None:

                state.last_error = (
                    "No tool registered for "
                    f"action '{action}'."
                )

                self._trace_termination(
                    state,
                    reason=(
                        TerminationReason
                        .NON_RECOVERABLE_ERROR
                    ),
                    summary=(
                        state.last_error
                    ),
                    action=action,
                )

                state.terminate(
                    reason=(
                        TerminationReason
                        .NON_RECOVERABLE_ERROR
                    ),
                    final_answer=(
                        state.last_error
                    ),
                )

                break

            # =================================================
            # ACT
            # =================================================

            state.status = (
                AgentStatus.ACTING
            )

            state.turn_count += 1
            state.tool_call_count += 1

            state.last_tool = action
            state.last_error = None

            state.add_react_event(
                phase="act",
                decision_summary=(
                    f"Execute the approved tool '{action}'."
                ),
                action=action,
                status="started",
            )

            try:
                observation = tool(
                    state
                )

            except Exception as exc:

                state.last_error = str(
                    exc
                )

                state.add_react_event(
                    phase="observe",
                    decision_summary=(
                        f"Tool '{action}' raised an execution error."
                    ),
                    action=action,
                    status="error",
                    details={
                        "error_type":
                            type(exc).__name__,
                    },
                )

                reflection = (
                    self.reflector.reflect(
                        state=state,
                        action=action,
                        error=(
                            state.last_error
                        ),
                    )
                )

                state.add_react_event(
                    phase="reflect",
                    decision_summary=(
                        reflection.reason
                    ),
                    action=action,
                    status=(
                        reflection
                        .decision.value
                    ),
                )

                if (
                    reflection.decision
                    == ReflectionDecision.RETRY
                ):
                    continue

                return (
                    self
                    ._terminate_from_reflection(
                        state=state,
                        reflection=reflection,
                    )
                )

            # =================================================
            # OBSERVE
            # =================================================

            state.status = (
                AgentStatus.OBSERVING
            )

            permission_required = False
            safety_blocked = False

            if isinstance(
                observation,
                dict,
            ):

                permission_required = bool(
                    observation.get(
                        "_permission_required",
                        False,
                    )
                )

                safety_blocked = bool(
                    observation.get(
                        "_safety_blocked",
                        False,
                    )
                    or observation.get(
                        "_safety_violation",
                        False,
                    )
                )

            state.add_react_event(
                phase="observe",
                decision_summary=(
                    f"Observe the structured result returned by '{action}'."
                ),
                action=action,
                status="observed",
                details=(
                    self._observation_details(
                        observation
                    )
                ),
            )

            # =================================================
            # REFLECT
            # =================================================

            reflection = (
                self.reflector.reflect(
                    state=state,
                    action=action,
                    observation=observation,
                    permission_required=(
                        permission_required
                    ),
                    safety_blocked=(
                        safety_blocked
                    ),
                )
            )

            state.add_react_event(
                phase="reflect",
                decision_summary=(
                    reflection.reason
                ),
                action=action,
                status=(
                    reflection
                    .decision.value
                ),
            )

            # Successful action.
            if (
                reflection.decision
                == ReflectionDecision.CONTINUE
            ):

                state.add_observation(
                    source=action,
                    content=observation,
                )

                continue

            # Recoverable failure.
            if (
                reflection.decision
                == ReflectionDecision.RETRY
            ):
                continue

            # STOP or REQUEST_APPROVAL.
            return (
                self
                ._terminate_from_reflection(
                    state=state,
                    reflection=reflection,
                )
            )

        return state
