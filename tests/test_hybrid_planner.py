from types import SimpleNamespace

from src.agent.hybrid_planner import HybridPlanner
from src.agent.planner import AgentAction
from src.agent.state import AgentState, TerminationReason


class FakeReasoner:
    def __init__(self, *, error=None):
        self.error = error
        self.calls = []

    def review_candidate(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            decision_summary="Model-backed concise decision.",
            usage={
                "model": "gemini-3.5-flash-lite",
                "input_tokens": 100,
                "output_tokens": 10,
                "cached_input_tokens": 0,
                "operation": "llm_reasoning",
            },
        )


def make_state():
    return AgentState(
        task_id="hybrid",
        user_request="Investigate RO data.",
    )


def test_successful_hybrid_reasoning_records_usage():
    state = make_state()
    reasoner = FakeReasoner()
    usage_calls = []
    budget_calls = []

    planner = HybridPlanner(
        reasoner=reasoner,
        usage_recorder=lambda state, usage: usage_calls.append((state, usage)),
        budget_guard=lambda state, model, input_tokens, output_tokens: (
            budget_calls.append((model, input_tokens, output_tokens)) or True
        ),
        model="gemini-3.5-flash-lite",
        preflight_input_tokens=5000,
        max_output_tokens=120,
    )

    decision = planner.next_action(state)

    assert decision.action == AgentAction.VALIDATE_DATA
    assert decision.reason == "Model-backed concise decision."
    assert reasoner.calls[0]["candidate_action"] == "validate_sensor_data"
    assert budget_calls == [("gemini-3.5-flash-lite", 5000, 120)]
    assert usage_calls[0][0] is state
    assert usage_calls[0][1]["input_tokens"] == 100


def test_budget_guard_can_stop_before_model_call():
    state = make_state()
    reasoner = FakeReasoner()
    planner = HybridPlanner(
        reasoner=reasoner,
        usage_recorder=lambda *_: None,
        budget_guard=lambda *_: False,
    )

    decision = planner.next_action(state)

    assert decision.action == AgentAction.STOP
    assert decision.termination_reason == TerminationReason.BUDGET_LIMIT_REACHED
    assert reasoner.calls == []


def test_reasoner_failure_falls_back_and_is_logged():
    state = make_state()
    error = RuntimeError("offline")
    reasoner = FakeReasoner(error=error)
    fallbacks = []

    planner = HybridPlanner(
        reasoner=reasoner,
        usage_recorder=lambda *_: None,
        fallback_logger=lambda state, exc: fallbacks.append((state, exc)),
    )

    decision = planner.next_action(state)

    assert decision.action == AgentAction.VALIDATE_DATA
    assert "validated" in decision.reason.lower()
    assert fallbacks == [(state, error)]


def test_reasoner_failure_without_logger_still_falls_back():
    state = make_state()
    planner = HybridPlanner(
        reasoner=FakeReasoner(error=RuntimeError("offline")),
        usage_recorder=lambda *_: None,
    )

    decision = planner.next_action(state)
    assert decision.action == AgentAction.VALIDATE_DATA


def test_budget_guard_is_optional():
    state = make_state()
    planner = HybridPlanner(
        reasoner=FakeReasoner(),
        usage_recorder=lambda *_: None,
        budget_guard=None,
    )

    decision = planner.next_action(state)
    assert decision.reason == "Model-backed concise decision."


def test_stop_and_finalize_skip_model_reasoner():
    reasoner = FakeReasoner()
    planner = HybridPlanner(
        reasoner=reasoner,
        usage_recorder=lambda *_: None,
    )

    stopped = make_state()
    stopped.turn_count = stopped.max_turns
    stop_decision = planner.next_action(stopped)
    assert stop_decision.action == AgentAction.STOP

    finished = make_state()
    for action in (
        AgentAction.VALIDATE_DATA,
        AgentAction.CALCULATE_KPIS,
        AgentAction.DETECT_ANOMALIES,
        AgentAction.SEARCH_KNOWLEDGE,
        AgentAction.SEARCH_MEMORY,
        AgentAction.DIAGNOSE,
        AgentAction.GENERATE_REPORT,
    ):
        finished.add_observation(action.value, {"success": True})

    final_decision = planner.next_action(finished)
    assert final_decision.action == AgentAction.FINALIZE
    assert reasoner.calls == []
