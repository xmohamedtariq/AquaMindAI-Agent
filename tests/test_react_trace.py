from src.agent.state import AgentState


def test_add_react_event_minimal_and_full() -> None:
    state = AgentState(
        task_id="react-trace",
        user_request="test",
    )

    state.add_react_event(
        phase="reason",
        decision_summary="Choose the next safe action.",
    )

    assert state.react_trace == [
        {
            "sequence": 1,
            "turn": 0,
            "phase": "reason",
            "decision_summary": "Choose the next safe action.",
        }
    ]

    state.turn_count = 1

    state.add_react_event(
        phase="act",
        decision_summary="Execute validation.",
        action="validate_sensor_data",
        status="started",
        details={"safe": True},
    )

    assert state.react_trace[1] == {
        "sequence": 2,
        "turn": 1,
        "phase": "act",
        "decision_summary": "Execute validation.",
        "action": "validate_sensor_data",
        "status": "started",
        "details": {"safe": True},
    }
