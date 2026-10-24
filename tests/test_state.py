from src.agent.state import (
    AgentState,
    AgentStatus,
    TerminationReason,
)


def make_state() -> AgentState:
    return AgentState(
        task_id="state-test-001",
        user_request=(
            "Investigate desalination plant performance"
        ),
    )


def test_default_state():
    state = make_state()

    assert state.status == AgentStatus.READY

    assert state.turn_count == 0
    assert state.tool_call_count == 0

    assert state.max_turns == 12
    assert state.max_tool_calls == 20

    assert state.budget_cap_usd == 0.10

    assert state.cumulative_cost_usd == 0.0

    assert state.input_tokens == 0
    assert state.output_tokens == 0

    assert state.plan == []
    assert state.observations == []
    assert state.evidence == []
    assert state.hypotheses == []
    assert state.recommendations == []

    assert state.reflection_notes == []
    assert state.recovery_attempts == {}

    assert state.current_action is None
    assert state.last_tool is None
    assert state.last_error is None

    assert state.final_answer is None
    assert state.termination_reason is None


def test_add_observation():
    state = make_state()

    state.add_observation(
        source="validate_sensor_data",
        content={
            "success": True,
        },
    )

    assert len(
        state.observations
    ) == 1

    observation = state.observations[0]

    assert (
        observation["source"]
        == "validate_sensor_data"
    )

    assert (
        observation["content"]["success"]
        is True
    )


def test_add_evidence():
    state = make_state()

    state.add_evidence(
        evidence_type="sensor",
        description=(
            "Differential pressure increased."
        ),
        value=18.5,
    )

    assert len(
        state.evidence
    ) == 1

    evidence = state.evidence[0]

    assert evidence["type"] == "sensor"

    assert (
        evidence["description"]
        == "Differential pressure increased."
    )

    assert evidence["value"] == 18.5


def test_add_cost():
    state = make_state()

    state.add_cost(
        cost_usd=0.012,
        input_tokens=1000,
        output_tokens=300,
    )

    state.add_cost(
        cost_usd=0.008,
        input_tokens=500,
        output_tokens=200,
    )

    assert (
        state.cumulative_cost_usd
        == 0.02
    )

    assert state.input_tokens == 1500
    assert state.output_tokens == 500


def test_reflection_storage():
    state = make_state()

    state.add_reflection(
        action="detect_anomalies",
        decision="continue",
        reason=(
            "Anomaly analysis completed."
        ),
    )

    assert len(
        state.reflection_notes
    ) == 1

    assert state.reflection_notes[0] == {
        "action": "detect_anomalies",
        "decision": "continue",
        "reason": "Anomaly analysis completed.",
    }


def test_recovery_count_defaults_to_zero():
    state = make_state()

    assert (
        state.recovery_count(
            "validate_sensor_data"
        )
        == 0
    )


def test_increment_recovery():
    state = make_state()

    first = state.increment_recovery(
        "validate_sensor_data"
    )

    second = state.increment_recovery(
        "validate_sensor_data"
    )

    assert first == 1
    assert second == 2

    assert (
        state.recovery_count(
            "validate_sensor_data"
        )
        == 2
    )


def test_budget_limit_helpers():
    state = make_state()

    assert (
        state.budget_exceeded()
        is False
    )

    state.cumulative_cost_usd = 0.10

    assert (
        state.budget_exceeded()
        is True
    )


def test_turn_limit_helpers():
    state = make_state()

    assert (
        state.max_turns_reached()
        is False
    )

    state.turn_count = 12

    assert (
        state.max_turns_reached()
        is True
    )


def test_tool_call_limit_helpers():
    state = make_state()

    assert (
        state.max_tool_calls_reached()
        is False
    )

    state.tool_call_count = 20

    assert (
        state.max_tool_calls_reached()
        is True
    )


def test_successful_termination():
    state = make_state()

    state.terminate(
        reason=TerminationReason.FINAL_ANSWER,
        final_answer=(
            "Plant investigation completed."
        ),
    )

    assert (
        state.status
        == AgentStatus.COMPLETED
    )

    assert (
        state.termination_reason
        == TerminationReason.FINAL_ANSWER
    )

    assert (
        state.final_answer
        == "Plant investigation completed."
    )


def test_human_authorization_termination():
    state = make_state()

    state.terminate(
        reason=(
            TerminationReason
            .HUMAN_AUTHORIZATION_REQUIRED
        ),
        final_answer=(
            "Operator approval required."
        ),
    )

    assert (
        state.status
        == AgentStatus.WAITING_FOR_APPROVAL
    )

    assert (
        state.termination_reason
        == TerminationReason
        .HUMAN_AUTHORIZATION_REQUIRED
    )


def test_failure_termination():
    state = make_state()

    state.terminate(
        reason=TerminationReason.SAFETY_BLOCK,
        final_answer=(
            "Unsafe operation blocked."
        ),
    )

    assert (
        state.status
        == AgentStatus.FAILED
    )

    assert (
        state.termination_reason
        == TerminationReason.SAFETY_BLOCK
    )