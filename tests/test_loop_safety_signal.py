from src.agent.loop import AgentLoop
from src.agent.state import (
    AgentState,
    AgentStatus,
    TerminationReason,
)


def test_safety_violation_signal_stops_agent():
    state = AgentState(
        task_id="safety-signal-test",
        user_request="Analyze this plant.",
    )

    def unsafe_validation(
        current_state,
    ):
        return {
            "success": False,
            "recoverable": False,
            "_safety_violation": True,
            "message": (
                "Unsafe request blocked."
            ),
        }

    loop = AgentLoop(
        tools={
            "validate_sensor_data":
                unsafe_validation,
        }
    )

    result = loop.run(
        state
    )

    assert (
        result.termination_reason
        == TerminationReason.SAFETY_BLOCK
    )

    assert (
        result.status
        == AgentStatus.FAILED
    )

    assert (
        result.tool_call_count
        == 1
    )

    assert (
        result.turn_count
        == 1
    )

    assert (
        result.observations
        == []
    )


def test_legacy_safety_blocked_signal_still_works():
    state = AgentState(
        task_id="legacy-safety-test",
        user_request="Analyze this plant.",
    )

    def blocked_validation(
        current_state,
    ):
        return {
            "success": False,
            "recoverable": False,
            "_safety_blocked": True,
            "message": (
                "Safety boundary triggered."
            ),
        }

    loop = AgentLoop(
        tools={
            "validate_sensor_data":
                blocked_validation,
        }
    )

    result = loop.run(
        state
    )

    assert (
        result.termination_reason
        == TerminationReason.SAFETY_BLOCK
    )

    assert (
        result.status
        == AgentStatus.FAILED
    )