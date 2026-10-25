from decimal import Decimal

import pytest

from src.cost.tracker import (
    CostTracker,
    ModelPricing,
    _non_negative_decimal,
    _positive_decimal,
    _token_count,
    _utc_now,
    calculate_usage_cost,
    project_task_costs,
)


def sample_pricing():
    return ModelPricing(
        model="test-model",
        input_per_million_usd="1.50",
        output_per_million_usd="6.00",
    )


def make_tracker(
    budget="0.10",
):
    return CostTracker(
        budget_cap_usd=budget,
        pricing=[
            sample_pricing()
        ],
    )


def test_utc_now():
    assert (
        _utc_now()
        .endswith("Z")
    )


def test_non_negative_decimal():
    assert (
        _non_negative_decimal(
            "1.25",
            "value",
        )
        == Decimal("1.25")
    )


def test_non_negative_decimal_rejects_invalid():
    with pytest.raises(
        ValueError,
        match="numeric",
    ):
        _non_negative_decimal(
            "not-a-number",
            "value",
        )


def test_non_negative_decimal_rejects_non_finite():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        _non_negative_decimal(
            "NaN",
            "value",
        )


def test_non_negative_decimal_rejects_negative():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        _non_negative_decimal(
            "-1",
            "value",
        )


def test_positive_decimal():
    assert (
        _positive_decimal(
            "0.10",
            "budget",
        )
        == Decimal("0.10")
    )


def test_positive_decimal_rejects_zero():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        _positive_decimal(
            "0",
            "budget",
        )


def test_token_count():
    assert (
        _token_count(
            100,
            "tokens",
        )
        == 100
    )


def test_token_count_rejects_non_integer():
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        _token_count(
            1.5,
            "tokens",
        )


def test_token_count_rejects_bool():
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        _token_count(
            True,
            "tokens",
        )


def test_token_count_rejects_negative():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        _token_count(
            -1,
            "tokens",
        )


def test_model_pricing():
    pricing = ModelPricing(
        model="  model-a  ",
        input_per_million_usd="2",
        output_per_million_usd="8",
    )

    assert pricing.model == "model-a"

    assert (
        pricing.input_per_million_usd
        == Decimal("2")
    )

    assert (
        pricing.output_per_million_usd
        == Decimal("8")
    )


def test_model_pricing_requires_name():
    with pytest.raises(
        ValueError,
        match="model",
    ):
        ModelPricing(
            model=" ",
            input_per_million_usd="1",
            output_per_million_usd="1",
        )


def test_model_pricing_requires_string_name():
    with pytest.raises(
        ValueError,
        match="model",
    ):
        ModelPricing(
            model=None,
            input_per_million_usd="1",
            output_per_million_usd="1",
        )


def test_model_pricing_serialization():
    result = (
        sample_pricing()
        .to_dict()
    )

    assert result == {
        "model":
            "test-model",
        "input_per_million_usd":
            1.5,
        "output_per_million_usd":
            6.0,
    }


def test_calculate_usage_cost():
    result = calculate_usage_cost(
        input_tokens=1000,
        output_tokens=500,
        pricing=sample_pricing(),
    )

    assert (
        result
        == Decimal("0.0045")
    )


def test_projection():
    result = project_task_costs(
        "0.025"
    )

    assert (
        result[
            "average_cost_per_task_usd"
        ]
        == 0.025
    )

    assert (
        result["100_tasks_usd"]
        == 2.5
    )

    assert (
        result["1000_tasks_usd"]
        == 25.0
    )

    assert (
        result["10000_tasks_usd"]
        == 250.0
    )


def test_tracker_without_initial_pricing():
    tracker = CostTracker(
        budget_cap_usd="0.10"
    )

    assert (
        tracker.total_cost_usd
        == Decimal("0")
    )


def test_register_pricing():
    tracker = CostTracker(
        budget_cap_usd="0.10"
    )

    pricing = sample_pricing()

    tracker.register_pricing(
        pricing
    )

    assert (
        tracker.pricing_for(
            "test-model"
        )
        == pricing
    )


def test_register_pricing_requires_model_pricing():
    tracker = CostTracker(
        budget_cap_usd="0.10"
    )

    with pytest.raises(
        TypeError,
        match="ModelPricing",
    ):
        tracker.register_pricing(
            "bad"
        )


def test_unknown_model_fails():
    tracker = CostTracker(
        budget_cap_usd="0.10"
    )

    with pytest.raises(
        KeyError,
        match="No pricing",
    ):
        tracker.pricing_for(
            "missing-model"
        )


def test_estimate_does_not_change_total():
    tracker = make_tracker()

    result = (
        tracker.estimate_usage_cost(
            model="test-model",
            input_tokens=1000,
            output_tokens=500,
        )
    )

    assert (
        result
        == Decimal("0.0045")
    )

    assert (
        tracker.total_cost_usd
        == Decimal("0")
    )


def test_can_afford_true():
    tracker = make_tracker()

    assert (
        tracker.can_afford(
            model="test-model",
            input_tokens=1000,
            output_tokens=500,
        )
        is True
    )


def test_can_afford_false():
    expensive = ModelPricing(
        model="expensive",
        input_per_million_usd="100",
        output_per_million_usd="100",
    )

    tracker = CostTracker(
        budget_cap_usd="0.01",
        pricing=[
            expensive
        ],
    )

    assert (
        tracker.can_afford(
            model="expensive",
            input_tokens=100000,
            output_tokens=0,
        )
        is False
    )


def test_record_usage():
    tracker = make_tracker()

    result = tracker.record_usage(
        model="test-model",
        input_tokens=1000,
        output_tokens=500,
        operation="diagnosis",
        timestamp=(
            "2026-10-25T05:00:00Z"
        ),
    )

    assert (
        result["call_cost_usd"]
        == 0.0045
    )

    assert (
        result["task_total_usd"]
        == 0.0045
    )

    assert (
        result[
            "budget_remaining_usd"
        ]
        == 0.0955
    )

    assert (
        result["within_budget"]
        is True
    )

    assert (
        result["budget_exhausted"]
        is False
    )


def test_record_usage_default_timestamp():
    tracker = make_tracker()

    result = tracker.record_usage(
        model="test-model",
        input_tokens=0,
        output_tokens=0,
    )

    assert (
        result["timestamp"]
        .endswith("Z")
    )

    assert (
        result["operation"]
        == "llm_call"
    )


def test_record_usage_requires_operation():
    tracker = make_tracker()

    with pytest.raises(
        ValueError,
        match="operation",
    ):
        tracker.record_usage(
            model="test-model",
            input_tokens=1,
            output_tokens=1,
            operation=" ",
        )


def test_multiple_usage_accumulates():
    tracker = make_tracker()

    tracker.record_usage(
        model="test-model",
        input_tokens=1000,
        output_tokens=500,
    )

    tracker.record_usage(
        model="test-model",
        input_tokens=1000,
        output_tokens=500,
    )

    assert (
        tracker.total_cost_usd
        == Decimal("0.0090")
    )

    assert (
        len(
            tracker.events()
        )
        == 2
    )


def test_events_returns_defensive_copy():
    tracker = make_tracker()

    tracker.record_usage(
        model="test-model",
        input_tokens=1000,
        output_tokens=0,
    )

    events = tracker.events()

    events[0][
        "input_tokens"
    ] = 999999

    assert (
        tracker.events()[0][
            "input_tokens"
        ]
        == 1000
    )


def test_exact_budget_is_exhausted():
    pricing = ModelPricing(
        model="exact",
        input_per_million_usd="100",
        output_per_million_usd="0",
    )

    tracker = CostTracker(
        budget_cap_usd="0.10",
        pricing=[
            pricing
        ],
    )

    result = tracker.record_usage(
        model="exact",
        input_tokens=1000,
        output_tokens=0,
    )

    assert (
        result["task_total_usd"]
        == 0.1
    )

    assert (
        result["budget_exhausted"]
        is True
    )

    assert (
        result["within_budget"]
        is True
    )

    assert (
        tracker.remaining_budget_usd
        == Decimal("0")
    )


def test_over_budget():
    pricing = ModelPricing(
        model="over",
        input_per_million_usd="200",
        output_per_million_usd="0",
    )

    tracker = CostTracker(
        budget_cap_usd="0.10",
        pricing=[
            pricing
        ],
    )

    result = tracker.record_usage(
        model="over",
        input_tokens=1000,
        output_tokens=0,
    )

    assert (
        result["task_total_usd"]
        == 0.2
    )

    assert (
        result["budget_exhausted"]
        is True
    )

    assert (
        result["within_budget"]
        is False
    )

    assert (
        tracker.remaining_budget_usd
        == Decimal("0")
    )


def test_empty_summary():
    tracker = make_tracker()

    result = tracker.summary()

    assert (
        result["call_count"]
        == 0
    )

    assert (
        result["total_cost_usd"]
        == 0.0
    )

    assert (
        result[
            "average_call_cost_usd"
        ]
        == 0.0
    )

    assert (
        result["budget_exhausted"]
        is False
    )


def test_summary_after_usage():
    tracker = make_tracker()

    tracker.record_usage(
        model="test-model",
        input_tokens=1000,
        output_tokens=500,
    )

    tracker.record_usage(
        model="test-model",
        input_tokens=2000,
        output_tokens=1000,
    )

    result = tracker.summary()

    assert (
        result["call_count"]
        == 2
    )

    assert (
        result[
            "total_input_tokens"
        ]
        == 3000
    )

    assert (
        result[
            "total_output_tokens"
        ]
        == 1500
    )

    assert (
        result["total_cost_usd"]
        == 0.0135
    )

    assert (
        result[
            "average_call_cost_usd"
        ]
        == 0.00675
    )