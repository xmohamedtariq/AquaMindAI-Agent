from __future__ import annotations

import src.agent.runtime as runtime_module

from src.agent.runtime import AquaMindRuntime
from src.agent.state import AgentState


def test_latest_report_skips_non_dict_content() -> None:
    """
    Cover the defensive branch where a report
    observation exists but its content is not
    a dictionary.
    """

    state = AgentState(
        task_id="coverage-latest-report",
        user_request="coverage test",
    )

    state.add_observation(
        source="generate_incident_report",
        content="invalid-report-content",
    )

    result = (
        AquaMindRuntime
        ._latest_report(
            state
        )
    )

    assert result is None


def test_report_tool_success_with_non_dict_report(
    monkeypatch,
) -> None:
    """
    Cover the branch where report generation
    succeeds but the report value itself is not
    a dictionary.

    The runtime must return the result without
    creating a final answer from invalid report
    content.
    """

    expected_result = {
        "success": True,
        "recoverable": False,
        "report": "invalid-report-value",
    }

    def fake_report_tool(
        state: AgentState,
    ) -> dict:
        return expected_result

    def fake_report_factory():
        return fake_report_tool

    monkeypatch.setattr(
        runtime_module,
        "make_generate_incident_report",
        fake_report_factory,
    )

    runtime = object.__new__(
        AquaMindRuntime
    )

    tool = runtime._make_report_tool()

    state = AgentState(
        task_id="coverage-report-wrapper",
        user_request="coverage test",
    )

    assert state.final_answer is None

    result = tool(
        state
    )

    assert result == expected_result

    assert (
        state.final_answer
        is None
    )