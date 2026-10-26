from pathlib import Path

from src.agent.runtime import AquaMindRuntime, RuntimeConfig
from src.agent.state import TerminationReason


class FakeKnowledgeClient:
    async def search(self, query, limit=5):
        return {"success": True, "query": query, "match_count": 0, "results": []}


def test_request_boundary_block_is_visible_in_react_trace(tmp_path: Path, monkeypatch) -> None:
    import src.agent.runtime as runtime_module

    monkeypatch.setattr(
        runtime_module,
        "guard_agent_request",
        lambda text: {
            "success": False,
            "assessment": {"unsafe": True, "reason": "physical control"},
            "message": "Blocked by safety policy.",
        },
    )

    class Memory:
        pass

    class Audit:
        def __init__(self):
            self.events = []
        def log_event(self, **kwargs):
            self.events.append(kwargs)
        def verify_integrity(self):
            return {"valid": True}

    class Cost:
        def summary(self):
            return {"total_cost_usd": 0.0}

    runtime = AquaMindRuntime.__new__(AquaMindRuntime)
    runtime.config = RuntimeConfig(dataset_path="normal_operation.csv")
    runtime.audit_logger = Audit()
    runtime.cost_tracker = Cost()
    runtime.agent_loop = None

    result = runtime.run(
        task_id="unsafe",
        user_request="unsafe request",
    )

    state = result["state"]
    assert state.termination_reason == TerminationReason.SAFETY_BLOCK
    assert state.tool_call_count == 0
    assert [event["phase"] for event in state.react_trace] == ["observe", "terminate"]
    assert state.react_trace[0]["status"] == "blocked"
    assert state.react_trace[1]["status"] == "SAFETY_BLOCK"
