import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from src.agent.state import AgentState
from src.llm.gemini_reasoner import GeminiReasoner


class FakeModels:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.models = FakeModels(response)


def make_state():
    state = AgentState(
        task_id="llm-test",
        user_request="Investigate RO performance.",
    )
    state.add_observation(
        "validate_sensor_data",
        {
            "success": True,
            "recoverable": True,
            "quality_score": 98.0,
            "records": [{"raw": "not forwarded"}],
        },
    )
    state.add_observation("non-dict", "ok")
    return state


def make_response(*, cached=5, thinking=3):
    return SimpleNamespace(
        text=json.dumps(
            {"decision_summary": "Validate evidence before continuing."}
        ),
        usage_metadata=SimpleNamespace(
            prompt_token_count=100,
            candidates_token_count=20,
            thoughts_token_count=thinking,
            cached_content_token_count=cached,
        ),
    )


def test_constructor_and_review_success():
    client = FakeClient(make_response())
    reasoner = GeminiReasoner(
        model="  gemini-3.5-flash-lite  ",
        max_output_tokens=80,
        client=client,
    )

    result = reasoner.review_candidate(
        state=make_state(),
        candidate_action="calculate_plant_kpis",
        fallback_reason="Validated data is available.",
    )

    assert reasoner.model == "gemini-3.5-flash-lite"
    assert result.decision_summary == "Validate evidence before continuing."
    assert result.usage == {
        "model": "gemini-3.5-flash-lite",
        "input_tokens": 100,
        "output_tokens": 23,
        "cached_input_tokens": 5,
        "candidate_output_tokens": 20,
        "thinking_tokens": 3,
        "operation": "llm_reasoning",
    }

    call = client.models.calls[0]
    assert call["model"] == "gemini-3.5-flash-lite"
    assert call["config"]["max_output_tokens"] == 80
    assert call["config"]["response_mime_type"] == "application/json"
    assert call["config"]["temperature"] == 0.2
    assert "approved_candidate_action" in call["contents"]
    assert "raw" not in call["contents"]


def test_constructor_rejects_invalid_model():
    with pytest.raises(ValueError, match="model"):
        GeminiReasoner(model=" ", client=FakeClient(make_response()))

    with pytest.raises(ValueError, match="model"):
        GeminiReasoner(model=None, client=FakeClient(make_response()))


def test_constructor_rejects_invalid_max_output_tokens():
    with pytest.raises(TypeError, match="integer"):
        GeminiReasoner(
            client=FakeClient(make_response()),
            max_output_tokens=True,
        )

    with pytest.raises(TypeError, match="integer"):
        GeminiReasoner(
            client=FakeClient(make_response()),
            max_output_tokens=1.5,
        )

    with pytest.raises(ValueError, match="greater than zero"):
        GeminiReasoner(
            client=FakeClient(make_response()),
            max_output_tokens=0,
        )


def test_constructor_builds_default_gemini_client(monkeypatch):
    sentinel = object()
    fake_genai = ModuleType("google.genai")
    fake_genai.Client = lambda: sentinel
    fake_google = ModuleType("google")
    fake_google.genai = fake_genai
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)

    reasoner = GeminiReasoner()
    assert reasoner.client is sentinel


def test_read_attr_supports_dict_and_object():
    assert GeminiReasoner._read_attr({"x": 1}, "x") == 1
    assert GeminiReasoner._read_attr(SimpleNamespace(x=2), "x") == 2
    assert GeminiReasoner._read_attr({}, "missing", 3) == 3


def test_compact_observation_and_state_summary():
    assert GeminiReasoner._compact_observation("hello") == {
        "result_type": "str"
    }

    compact = GeminiReasoner._compact_observation(
        {
            "success": True,
            "quality_score": 99,
            "records": [1, 2, 3],
        }
    )
    assert compact == {"success": True, "quality_score": 99}

    summary = GeminiReasoner._state_summary(make_state())
    assert summary["turn_count"] == 0
    assert len(summary["completed_observations"]) == 2
    assert summary["completed_observations"][0]["summary"]["recoverable"] is True
    assert summary["completed_observations"][1]["summary"] == {
        "result_type": "str"
    }


def test_response_config_contains_schema_and_system_prompt():
    config = GeminiReasoner._response_config("system", 42)
    assert config["system_instruction"] == "system"
    assert config["max_output_tokens"] == 42
    assert config["response_schema"]["properties"]["decision_summary"]


def test_provider_usage_accepts_mapping_and_none_optional_values():
    response = {
        "usage_metadata": {
            "prompt_token_count": 10,
            "candidates_token_count": None,
            "thoughts_token_count": None,
            "cached_content_token_count": None,
        }
    }
    assert GeminiReasoner._provider_usage(response, "model") == {
        "model": "model",
        "input_tokens": 10,
        "output_tokens": 0,
        "cached_input_tokens": 0,
        "candidate_output_tokens": 0,
        "thinking_tokens": 0,
        "operation": "llm_reasoning",
    }


def test_provider_usage_rejects_missing_or_invalid_values():
    with pytest.raises(RuntimeError, match="did not include"):
        GeminiReasoner._provider_usage({}, "model")

    with pytest.raises(RuntimeError, match="input token"):
        GeminiReasoner._provider_usage(
            {"usage_metadata": {"prompt_token_count": -1}},
            "model",
        )

    with pytest.raises(RuntimeError, match="output token"):
        GeminiReasoner._provider_usage(
            {
                "usage_metadata": {
                    "prompt_token_count": 1,
                    "candidates_token_count": "bad",
                }
            },
            "model",
        )

    with pytest.raises(RuntimeError, match="thinking token"):
        GeminiReasoner._provider_usage(
            {
                "usage_metadata": {
                    "prompt_token_count": 1,
                    "candidates_token_count": 1,
                    "thoughts_token_count": -1,
                }
            },
            "model",
        )

    with pytest.raises(RuntimeError, match="cached token"):
        GeminiReasoner._provider_usage(
            {
                "usage_metadata": {
                    "prompt_token_count": 1,
                    "candidates_token_count": 1,
                    "cached_content_token_count": -1,
                }
            },
            "model",
        )


def test_review_rejects_missing_text():
    response = SimpleNamespace(
        text=None,
        usage_metadata=SimpleNamespace(
            prompt_token_count=1,
            candidates_token_count=1,
        ),
    )
    reasoner = GeminiReasoner(client=FakeClient(response))

    with pytest.raises(RuntimeError, match="text output"):
        reasoner.review_candidate(
            state=make_state(),
            candidate_action="validate_sensor_data",
            fallback_reason="Validate first.",
        )


def test_review_rejects_invalid_json():
    response = SimpleNamespace(
        text="not-json",
        usage_metadata=SimpleNamespace(
            prompt_token_count=1,
            candidates_token_count=1,
        ),
    )
    reasoner = GeminiReasoner(client=FakeClient(response))

    with pytest.raises(RuntimeError, match="valid JSON"):
        reasoner.review_candidate(
            state=make_state(),
            candidate_action="validate_sensor_data",
            fallback_reason="Validate first.",
        )


def test_review_rejects_empty_summary():
    response = SimpleNamespace(
        text=json.dumps({"decision_summary": "   "}),
        usage_metadata=SimpleNamespace(
            prompt_token_count=1,
            candidates_token_count=1,
        ),
    )
    reasoner = GeminiReasoner(client=FakeClient(response))

    with pytest.raises(RuntimeError, match="summary is empty"):
        reasoner.review_candidate(
            state=make_state(),
            candidate_action="validate_sensor_data",
            fallback_reason="Validate first.",
        )
