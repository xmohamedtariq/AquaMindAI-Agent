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
    Core autonomous execution loop for AquaMind AI.

    Lifecycle:

    PLAN
      ->
    ACT
      ->
    OBSERVE
      ->
    REFLECT
      ->
    CONTINUE / RETRY / TERMINATE
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
            "AquaMind AI completed the "
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
            # PLAN
            # =================================================

            decision = (
                self.planner.next_action(
                    state
                )
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

                state.terminate(
                    reason=(
                        TerminationReason
                        .FINAL_ANSWER
                    ),
                    final_answer=(
                        self._final_message(
                            state
                        )
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

            try:
                observation = tool(
                    state
                )

            except Exception as exc:

                state.last_error = str(
                    exc
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