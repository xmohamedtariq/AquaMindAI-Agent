from src.agent.loop import AgentLoop
from src.agent.planner import (
    AgentAction,
    PlanDecision,
    Planner,
)
from src.agent.reflector import Reflector
from src.agent.state import (
    AgentState,
    AgentStatus,
    TerminationReason,
)


def make_state() -> AgentState:
    return AgentState(
        task_id="loop-test-001",
        user_request=(
            "Investigate desalination plant performance"
        ),
    )


def make_success_tools(
    set_final_answer: bool = True,
):
    """Create deterministic tools for loop tests."""

    def validate_sensor_data(
        state: AgentState,
    ):
        return {
            "success": True,
            "valid": True,
        }

    def calculate_plant_kpis(
        state: AgentState,
    ):
        return {
            "success": True,
            "recovery_rate": 42.0,
        }

    def detect_anomalies(
        state: AgentState,
    ):
        return {
            "success": True,
            "anomalies": [],
        }

    def search_operational_knowledge(
        state: AgentState,
    ):
        return {
            "success": True,
            "documents_found": 1,
        }

    def search_incident_memory(
        state: AgentState,
    ):
        return {
            "success": True,
            "similar_incidents": [],
        }

    def diagnose_issue(
        state: AgentState,
    ):
        return {
            "success": True,
            "diagnosis": (
                "No critical issue detected."
            ),
        }

    def generate_incident_report(
        state: AgentState,
    ):
        if set_final_answer:
            state.final_answer = (
                "Plant investigation "
                "completed successfully."
            )

        return {
            "success": True,
            "report_generated": True,
        }

    return {
        AgentAction.VALIDATE_DATA.value:
            validate_sensor_data,

        AgentAction.CALCULATE_KPIS.value:
            calculate_plant_kpis,

        AgentAction.DETECT_ANOMALIES.value:
            detect_anomalies,

        AgentAction.SEARCH_KNOWLEDGE.value:
            search_operational_knowledge,

        AgentAction.SEARCH_MEMORY.value:
            search_incident_memory,

        AgentAction.DIAGNOSE.value:
            diagnose_issue,

        AgentAction.GENERATE_REPORT.value:
            generate_incident_report,
    }


def test_complete_autonomous_loop():
    state = make_state()

    result = AgentLoop(
        tools=make_success_tools()
    ).run(
        state
    )

    assert (
        result.status
        == AgentStatus.COMPLETED
    )

    assert (
        result.termination_reason
        == TerminationReason.FINAL_ANSWER
    )

    assert (
        result.final_answer
        == (
            "Plant investigation "
            "completed successfully."
        )
    )

    assert result.turn_count == 7
    assert result.tool_call_count == 7

    assert len(
        result.observations
    ) == 7

    assert (
        result.current_action
        == AgentAction.GENERATE_REPORT.value
    )


def test_default_final_message():
    state = make_state()

    result = AgentLoop(
        tools=make_success_tools(
            set_final_answer=False
        )
    ).run(
        state
    )

    assert (
        result.status
        == AgentStatus.COMPLETED
    )

    assert (
        result.final_answer
        == (
            "AquaMindAI-Agent completed the "
            "desalination plant investigation."
        )
    )


def test_existing_plan_is_preserved():
    state = make_state()

    state.plan = [
        "existing-plan"
    ]

    result = AgentLoop(
        tools=make_success_tools()
    ).run(
        state
    )

    assert result.plan == [
        "existing-plan"
    ]

    assert (
        result.termination_reason
        == TerminationReason.FINAL_ANSWER
    )


def test_custom_planner_and_reflector():
    state = make_state()

    planner = Planner()
    reflector = Reflector()

    result = AgentLoop(
        tools=make_success_tools(),
        planner=planner,
        reflector=reflector,
    ).run(
        state
    )

    assert (
        result.termination_reason
        == TerminationReason.FINAL_ANSWER
    )


def test_missing_tool_stops_safely():
    state = make_state()

    def validate_sensor_data(
        state: AgentState,
    ):
        return {
            "success": True,
        }

    tools = {
        AgentAction.VALIDATE_DATA.value:
            validate_sensor_data,
    }

    result = AgentLoop(
        tools=tools
    ).run(
        state
    )

    assert (
        result.status
        == AgentStatus.FAILED
    )

    assert (
        result.termination_reason
        == TerminationReason.NON_RECOVERABLE_ERROR
    )

    assert (
        "No tool registered"
        in result.final_answer
    )


def test_exception_is_retried_then_recovers():
    state = make_state()

    tools = make_success_tools()

    attempts = {
        "count": 0,
    }

    def unstable_validation(
        state: AgentState,
    ):
        attempts["count"] += 1

        if attempts["count"] <= 2:
            raise ValueError(
                "Temporary CSV parsing error"
            )

        return {
            "success": True,
            "valid": True,
        }

    tools[
        AgentAction.VALIDATE_DATA.value
    ] = unstable_validation

    result = AgentLoop(
        tools=tools
    ).run(
        state
    )

    assert attempts["count"] == 3

    assert (
        state.recovery_count(
            AgentAction.VALIDATE_DATA.value
        )
        == 2
    )

    assert (
        result.termination_reason
        == TerminationReason.FINAL_ANSWER
    )


def test_exception_stops_after_retry_limit():
    state = make_state()

    tools = make_success_tools()

    def broken_validation(
        state: AgentState,
    ):
        raise ValueError(
            "Persistent parsing failure"
        )

    tools[
        AgentAction.VALIDATE_DATA.value
    ] = broken_validation

    result = AgentLoop(
        tools=tools
    ).run(
        state
    )

    assert (
        result.status
        == AgentStatus.FAILED
    )

    assert (
        result.termination_reason
        == TerminationReason.NON_RECOVERABLE_ERROR
    )

    assert (
        state.recovery_count(
            AgentAction.VALIDATE_DATA.value
        )
        == 3
    )


def test_recoverable_observation_retries():
    state = make_state()

    tools = make_success_tools()

    attempts = {
        "count": 0,
    }

    def recoverable_validation(
        state: AgentState,
    ):
        attempts["count"] += 1

        if attempts["count"] == 1:
            return {
                "success": False,
                "recoverable": True,
            }

        return {
            "success": True,
            "valid": True,
        }

    tools[
        AgentAction.VALIDATE_DATA.value
    ] = recoverable_validation

    result = AgentLoop(
        tools=tools
    ).run(
        state
    )

    assert attempts["count"] == 2

    assert (
        result.termination_reason
        == TerminationReason.FINAL_ANSWER
    )


def test_permission_request_stops_for_human():
    state = make_state()

    tools = make_success_tools()

    def protected_validation(
        state: AgentState,
    ):
        return {
            "success": True,
            "_permission_required": True,
        }

    tools[
        AgentAction.VALIDATE_DATA.value
    ] = protected_validation

    result = AgentLoop(
        tools=tools
    ).run(
        state
    )

    assert (
        result.status
        == AgentStatus.WAITING_FOR_APPROVAL
    )

    assert (
        result.termination_reason
        == TerminationReason
        .HUMAN_AUTHORIZATION_REQUIRED
    )


def test_safety_block_terminates():
    state = make_state()

    tools = make_success_tools()

    def unsafe_validation(
        state: AgentState,
    ):
        return {
            "success": True,
            "_safety_blocked": True,
        }

    tools[
        AgentAction.VALIDATE_DATA.value
    ] = unsafe_validation

    result = AgentLoop(
        tools=tools
    ).run(
        state
    )

    assert (
        result.status
        == AgentStatus.FAILED
    )

    assert (
        result.termination_reason
        == TerminationReason.SAFETY_BLOCK
    )


def test_insufficient_evidence_stops():
    state = make_state()

    tools = make_success_tools()

    def insufficient_validation(
        state: AgentState,
    ):
        return {
            "success": True,
            "insufficient_evidence": True,
        }

    tools[
        AgentAction.VALIDATE_DATA.value
    ] = insufficient_validation

    result = AgentLoop(
        tools=tools
    ).run(
        state
    )

    assert (
        result.status
        == AgentStatus.FAILED
    )

    assert (
        result.termination_reason
        == TerminationReason
        .INSUFFICIENT_EVIDENCE
    )


def test_non_dict_observation_is_supported():
    state = make_state()

    tools = make_success_tools()

    def text_validation(
        state: AgentState,
    ):
        return "Validation completed"

    tools[
        AgentAction.VALIDATE_DATA.value
    ] = text_validation

    result = AgentLoop(
        tools=tools
    ).run(
        state
    )

    assert (
        result.termination_reason
        == TerminationReason.FINAL_ANSWER
    )


def test_budget_limit_stops_before_tool_execution():
    state = make_state()

    state.cumulative_cost_usd = 0.10

    result = AgentLoop(
        tools=make_success_tools()
    ).run(
        state
    )

    assert result.tool_call_count == 0

    assert (
        result.termination_reason
        == TerminationReason.BUDGET_LIMIT_REACHED
    )


def test_missing_termination_reason_falls_back_safely():
    class StopPlanner(Planner):

        def next_action(
            self,
            state: AgentState,
        ) -> PlanDecision:

            return PlanDecision(
                action=AgentAction.STOP,
                reason="Forced test stop.",
                termination_reason=None,
            )

    state = make_state()

    result = AgentLoop(
        tools=make_success_tools(),
        planner=StopPlanner(),
    ).run(
        state
    )

    assert (
        result.termination_reason
        == TerminationReason.NON_RECOVERABLE_ERROR
    )
