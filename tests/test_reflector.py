from src.agent.reflector import (
    ReflectionDecision,
    Reflector,
)
from src.agent.state import (
    AgentState,
    AgentStatus,
    TerminationReason,
)


def make_state() -> AgentState:
    return AgentState(
        task_id="reflection-test",
        user_request=(
            "Investigate plant performance"
        ),
    )


def test_successful_action_continues():
    state = make_state()

    result = Reflector().reflect(
        state=state,
        action="calculate_plant_kpis",
        observation={
            "success": True,
        },
    )

    assert (
        result.decision
        == ReflectionDecision.CONTINUE
    )

    assert (
        result.termination_reason
        is None
    )

    assert (
        state.status
        == AgentStatus.REFLECTING
    )

    assert len(
        state.reflection_notes
    ) == 1


def test_success_without_structured_observation():
    state = make_state()

    result = Reflector().reflect(
        state=state,
        action="search_operational_knowledge",
        observation="Knowledge retrieved",
    )

    assert (
        result.decision
        == ReflectionDecision.CONTINUE
    )


def test_runtime_error_retries():
    state = make_state()

    reflector = Reflector()

    result = reflector.reflect(
        state=state,
        action="validate_sensor_data",
        error="Temporary parsing error",
    )

    assert (
        result.decision
        == ReflectionDecision.RETRY
    )

    assert (
        result.recoverable
        is True
    )

    assert (
        state.recovery_count(
            "validate_sensor_data"
        )
        == 1
    )


def test_runtime_error_stops_after_recovery_limit():
    state = make_state()

    reflector = Reflector()

    for _ in range(2):

        result = reflector.reflect(
            state=state,
            action="validate_sensor_data",
            error="Temporary parsing error",
        )

        assert (
            result.decision
            == ReflectionDecision.RETRY
        )

    result = reflector.reflect(
        state=state,
        action="validate_sensor_data",
        error="Temporary parsing error",
    )

    assert (
        result.decision
        == ReflectionDecision.STOP
    )

    assert (
        result.termination_reason
        == TerminationReason
        .NON_RECOVERABLE_ERROR
    )


def test_unrecoverable_observation_stops():
    state = make_state()

    result = Reflector().reflect(
        state=state,
        action="load_operational_data",
        observation={
            "success": False,
            "recoverable": False,
        },
    )

    assert (
        result.decision
        == ReflectionDecision.STOP
    )

    assert (
        result.termination_reason
        == TerminationReason
        .NON_RECOVERABLE_ERROR
    )


def test_recoverable_observation_retries():
    state = make_state()

    result = Reflector().reflect(
        state=state,
        action="validate_sensor_data",
        observation={
            "success": False,
            "recoverable": True,
        },
    )

    assert (
        result.decision
        == ReflectionDecision.RETRY
    )

    assert (
        result.recoverable
        is True
    )


def test_insufficient_evidence_stops():
    state = make_state()

    result = Reflector().reflect(
        state=state,
        action="diagnose_issue",
        observation={
            "success": True,
            "insufficient_evidence": True,
        },
    )

    assert (
        result.decision
        == ReflectionDecision.STOP
    )

    assert (
        result.termination_reason
        == TerminationReason
        .INSUFFICIENT_EVIDENCE
    )


def test_safety_violation_is_blocked():
    state = make_state()

    result = Reflector().reflect(
        state=state,
        action="increase_feed_pressure",
        safety_blocked=True,
    )

    assert (
        result.decision
        == ReflectionDecision.STOP
    )

    assert (
        result.termination_reason
        == TerminationReason.SAFETY_BLOCK
    )


def test_human_authorization_is_requested():
    state = make_state()

    result = Reflector().reflect(
        state=state,
        action="change_pump_settings",
        permission_required=True,
    )

    assert (
        result.decision
        == ReflectionDecision.REQUEST_APPROVAL
    )

    assert (
        result.termination_reason
        == TerminationReason
        .HUMAN_AUTHORIZATION_REQUIRED
    )