from src.agent.loop import AgentLoop
from src.agent.state import (
    AgentState,
    AgentStatus,
    TerminationReason,
)


def test_preterminated_state_returns_without_execution():
    """
    A state that is already terminated must not
    execute any additional agent turns or tools.
    """

    state = AgentState(
        task_id="preterminated-test",
        user_request="Investigate plant performance",
    )

    state.terminate(
        reason=TerminationReason.SAFETY_BLOCK,
        final_answer="Execution was already terminated.",
    )

    loop = AgentLoop(
        tools={}
    )

    result = loop.run(
        state
    )

    assert result is state

    assert (
        result.status
        == AgentStatus.FAILED
    )

    assert (
        result.termination_reason
        == TerminationReason.SAFETY_BLOCK
    )

    assert (
        result.final_answer
        == "Execution was already terminated."
    )

    assert result.turn_count == 0
    assert result.tool_call_count == 0
    assert result.observations == []