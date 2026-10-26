from enum import Enum

from pydantic import BaseModel

from src.agent.state import (
    AgentState,
    AgentStatus,
    TerminationReason,
)


class AgentAction(str, Enum):
    """Actions AquaMindAI-Agent is allowed to plan."""

    VALIDATE_DATA = "validate_sensor_data"
    CALCULATE_KPIS = "calculate_plant_kpis"
    DETECT_ANOMALIES = "detect_anomalies"
    SEARCH_KNOWLEDGE = "search_operational_knowledge"
    SEARCH_MEMORY = "search_incident_memory"
    DIAGNOSE = "diagnose_issue"
    GENERATE_REPORT = "generate_incident_report"
    FINALIZE = "final_answer"
    STOP = "stop"


class PlanDecision(BaseModel):
    """One planning decision produced by the agent."""

    action: AgentAction
    reason: str
    termination_reason: TerminationReason | None = None


class Planner:
    """
    Selects the next action from the current investigation state.

    The planner does not execute tools.
    It only decides what AquaMind should do next.
    """

    def build_initial_plan(self, state: AgentState) -> list[str]:
        """Create the initial high-level investigation plan."""

        state.plan = [
            AgentAction.VALIDATE_DATA.value,
            AgentAction.CALCULATE_KPIS.value,
            AgentAction.DETECT_ANOMALIES.value,
            AgentAction.SEARCH_KNOWLEDGE.value,
            AgentAction.SEARCH_MEMORY.value,
            AgentAction.DIAGNOSE.value,
            AgentAction.GENERATE_REPORT.value,
            AgentAction.FINALIZE.value,
        ]

        return state.plan

    @staticmethod
    def _has_observation(
        state: AgentState,
        source: str,
    ) -> bool:
        """Check whether a particular step has already produced an observation."""

        return any(
            observation.get("source") == source
            for observation in state.observations
        )

    def next_action(self, state: AgentState) -> PlanDecision:
        """
        Decide what the agent should do next.

        Hard limits are checked before any new action is planned.
        """

        state.status = AgentStatus.PLANNING

        # ----- Hard termination conditions -----

        if state.budget_exceeded():
            return PlanDecision(
                action=AgentAction.STOP,
                reason="The configured task budget has been exhausted.",
                termination_reason=TerminationReason.BUDGET_LIMIT_REACHED,
            )

        if state.max_turns_reached():
            return PlanDecision(
                action=AgentAction.STOP,
                reason="The maximum number of agent turns has been reached.",
                termination_reason=TerminationReason.MAX_TURNS_REACHED,
            )

        if state.max_tool_calls_reached():
            return PlanDecision(
                action=AgentAction.STOP,
                reason="The maximum number of tool calls has been reached.",
                termination_reason=TerminationReason.MAX_TOOL_CALLS_REACHED,
            )

        # ----- Investigation planning -----

        if not self._has_observation(state, AgentAction.VALIDATE_DATA.value):
            return PlanDecision(
                action=AgentAction.VALIDATE_DATA,
                reason=(
                    "Operational data must be validated before "
                    "performing engineering analysis."
                ),
            )

        if not self._has_observation(
            state,
            AgentAction.CALCULATE_KPIS.value,
        ):
            return PlanDecision(
                action=AgentAction.CALCULATE_KPIS,
                reason=(
                    "Validated data is available, so plant KPIs "
                    "should be calculated next."
                ),
            )

        if not self._has_observation(
            state,
            AgentAction.DETECT_ANOMALIES.value,
        ):
            return PlanDecision(
                action=AgentAction.DETECT_ANOMALIES,
                reason=(
                    "Plant KPIs are available and should now be "
                    "examined for abnormal behavior."
                ),
            )

        if not self._has_observation(
            state,
            AgentAction.SEARCH_KNOWLEDGE.value,
        ):
            return PlanDecision(
                action=AgentAction.SEARCH_KNOWLEDGE,
                reason=(
                    "Operational evidence should be compared with "
                    "approved desalination knowledge resources."
                ),
            )

        if not self._has_observation(
            state,
            AgentAction.SEARCH_MEMORY.value,
        ):
            return PlanDecision(
                action=AgentAction.SEARCH_MEMORY,
                reason=(
                    "Historical incidents may provide supporting "
                    "context for the current investigation."
                ),
            )

        if not self._has_observation(
            state,
            AgentAction.DIAGNOSE.value,
        ):
            return PlanDecision(
                action=AgentAction.DIAGNOSE,
                reason=(
                    "Sensor evidence, operational knowledge, and "
                    "historical context are available for diagnosis."
                ),
            )

        if not self._has_observation(
            state,
            AgentAction.GENERATE_REPORT.value,
        ):
            return PlanDecision(
                action=AgentAction.GENERATE_REPORT,
                reason=(
                    "The investigation has sufficient outputs to "
                    "produce a structured incident report."
                ),
            )

        return PlanDecision(
            action=AgentAction.FINALIZE,
            reason="The investigation workflow has completed successfully.",
            termination_reason=TerminationReason.FINAL_ANSWER,
        )
