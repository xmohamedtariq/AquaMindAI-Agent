import pytest

from src.agent.state import AgentState
from src.tools.anomaly_detection import (
    _build_metric_series,
    _latest_validated_records,
    _relative_change_pct,
    _severity_for_change,
    _window_comparison,
    detect_anomalies_from_state,
    detect_operational_anomalies,
    make_detect_anomalies,
)


def make_state() -> AgentState:
    return AgentState(
        task_id="anomaly-test",
        user_request=(
            "Detect abnormal RO performance"
        ),
    )


def normal_records():
    return [
        {
            "feed_flow": 200.0,
            "permeate_flow": 100.0,
            "feed_pressure": 60.0,
            "concentrate_pressure": 57.0,
            "feed_tds": 35000.0,
            "permeate_tds": 350.0,
            "specific_energy_consumption": 3.0,
        },
        {
            "feed_flow": 200.0,
            "permeate_flow": 98.0,
            "feed_pressure": 60.2,
            "concentrate_pressure": 57.1,
            "feed_tds": 35000.0,
            "permeate_tds": 360.0,
            "specific_energy_consumption": 3.05,
        },
    ]


def warning_records():
    return [
        {
            "feed_flow": 200.0,
            "permeate_flow": 100.0,
            "feed_pressure": 60.0,
            "concentrate_pressure": 57.0,
            "feed_tds": 35000.0,
            "permeate_tds": 350.0,
            "specific_energy_consumption": 3.0,
        },
        {
            "feed_flow": 200.0,
            "permeate_flow": 93.0,
            "feed_pressure": 60.0,
            "concentrate_pressure": 57.0,
            "feed_tds": 35000.0,
            "permeate_tds": 350.0,
            "specific_energy_consumption": 3.0,
        },
    ]


def critical_records():
    return [
        {
            "feed_flow": 200.0,
            "permeate_flow": 100.0,
            "feed_pressure": 60.0,
            "concentrate_pressure": 57.0,
            "feed_tds": 35000.0,
            "permeate_tds": 350.0,
            "specific_energy_consumption": 3.0,
        },
        {
            "feed_flow": 200.0,
            "permeate_flow": 80.0,
            "feed_pressure": 61.0,
            "concentrate_pressure": 57.0,
            "feed_tds": 35000.0,
            "permeate_tds": 700.0,
            "specific_energy_consumption": 3.6,
        },
    ]


def test_relative_change():
    assert (
        _relative_change_pct(
            baseline=100.0,
            current=90.0,
        )
        == -10.0
    )

    assert (
        _relative_change_pct(
            baseline=100.0,
            current=110.0,
        )
        == 10.0
    )

    assert (
        _relative_change_pct(
            baseline=0.0,
            current=10.0,
        )
        is None
    )


def test_decrease_severity():
    assert (
        _severity_for_change(
            change_pct=-3.0,
            direction="decrease",
            warning_threshold_pct=5.0,
            critical_threshold_pct=10.0,
        )
        is None
    )

    assert (
        _severity_for_change(
            change_pct=-7.0,
            direction="decrease",
            warning_threshold_pct=5.0,
            critical_threshold_pct=10.0,
        )
        == "warning"
    )

    assert (
        _severity_for_change(
            change_pct=-12.0,
            direction="decrease",
            warning_threshold_pct=5.0,
            critical_threshold_pct=10.0,
        )
        == "critical"
    )


def test_increase_severity():
    assert (
        _severity_for_change(
            change_pct=7.0,
            direction="increase",
            warning_threshold_pct=5.0,
            critical_threshold_pct=10.0,
        )
        == "warning"
    )

    assert (
        _severity_for_change(
            change_pct=12.0,
            direction="increase",
            warning_threshold_pct=5.0,
            critical_threshold_pct=10.0,
        )
        == "critical"
    )


def test_invalid_direction_fails():
    with pytest.raises(
        ValueError,
        match=(
            "Unsupported anomaly direction"
        ),
    ):
        _severity_for_change(
            change_pct=10.0,
            direction="sideways",
            warning_threshold_pct=5.0,
            critical_threshold_pct=10.0,
        )


def test_window_comparison():
    result = _window_comparison(
        [
            100.0,
            100.0,
            90.0,
            90.0,
        ],
        window_size=2,
    )

    assert result == {
        "baseline": 100.0,
        "current": 90.0,
        "change_pct": -10.0,
    }


def test_window_comparison_requires_two_values():
    assert (
        _window_comparison(
            [100.0]
        )
        is None
    )


def test_window_comparison_zero_baseline():
    assert (
        _window_comparison(
            [
                0.0,
                10.0,
            ]
        )
        is None
    )


def test_build_metric_series():
    result = _build_metric_series(
        normal_records()
    )

    assert result[
        "permeate_flow"
    ] == [
        100.0,
        98.0,
    ]

    assert result[
        "recovery_rate_pct"
    ] == [
        50.0,
        49.0,
    ]

    assert result[
        "pressure_drop"
    ] == pytest.approx(
        [
            3.0,
            3.1,
        ]
    )

    assert len(
        result[
            "tds_salt_rejection_pct"
        ]
    ) == 2

    assert result[
        "specific_energy_consumption"
    ] == [
        3.0,
        3.05,
    ]


def test_empty_records_fail():
    result = (
        detect_operational_anomalies(
            []
        )
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "No validated sensor records "
            "were provided for anomaly detection."
        )
    )


def test_invalid_warning_threshold_fails():
    result = (
        detect_operational_anomalies(
            normal_records(),
            warning_threshold_pct=0,
        )
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Warning threshold must be "
            "greater than zero."
        )
    )


def test_invalid_critical_threshold_fails():
    result = (
        detect_operational_anomalies(
            normal_records(),
            warning_threshold_pct=5,
            critical_threshold_pct=5,
        )
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Critical threshold must be "
            "greater than warning threshold."
        )
    )


def test_invalid_window_size_fails():
    result = (
        detect_operational_anomalies(
            normal_records(),
            window_size=0,
        )
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Window size must be "
            "greater than zero."
        )
    )


def test_normal_operation_has_no_anomaly():
    result = (
        detect_operational_anomalies(
            normal_records()
        )
    )

    assert result["success"] is True

    assert (
        result["anomaly_detected"]
        is False
    )

    assert (
        result["overall_severity"]
        == "normal"
    )

    assert result["anomalies"] == []


def test_warning_anomaly():
    result = (
        detect_operational_anomalies(
            warning_records()
        )
    )

    assert result["success"] is True

    assert (
        result["anomaly_detected"]
        is True
    )

    assert (
        result["overall_severity"]
        == "warning"
    )

    assert any(
        anomaly["metric"]
        == "permeate_flow"
        and anomaly["severity"]
        == "warning"
        for anomaly
        in result["anomalies"]
    )


def test_critical_anomaly():
    result = (
        detect_operational_anomalies(
            critical_records()
        )
    )

    assert result["success"] is True

    assert (
        result["anomaly_detected"]
        is True
    )

    assert (
        result["overall_severity"]
        == "critical"
    )

    assert any(
        anomaly["severity"]
        == "critical"
        for anomaly
        in result["anomalies"]
    )


def test_insufficient_metrics_are_reported():
    result = (
        detect_operational_anomalies(
            [
                {
                    "feed_pressure": 60.0,
                }
            ]
        )
    )

    assert result["success"] is True

    assert (
        result["available_metrics"]
        == []
    )

    assert len(
        result[
            "insufficient_metrics"
        ]
    ) == 5

    assert (
        result["overall_severity"]
        == "normal"
    )


def test_latest_validated_records_covers_skips():
    state = make_state()

    expected = normal_records()

    state.add_observation(
        source="validate_sensor_data",
        content={
            "success": True,
            "records": expected,
        },
    )

    state.add_observation(
        source="validate_sensor_data",
        content={
            "success": False,
        },
    )

    state.add_observation(
        source="validate_sensor_data",
        content="bad-content",
    )

    state.add_observation(
        source="other_tool",
        content={
            "success": True,
        },
    )

    assert (
        _latest_validated_records(
            state
        )
        == expected
    )


def test_latest_validated_records_requires_list():
    state = make_state()

    state.add_observation(
        source="validate_sensor_data",
        content={
            "success": True,
            "records": "not-a-list",
        },
    )

    assert (
        _latest_validated_records(
            state
        )
        is None
    )


def test_state_without_validation_fails():
    result = (
        detect_anomalies_from_state(
            make_state()
        )
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Validated sensor records are "
            "unavailable for anomaly detection."
        )
    )


def test_state_anomaly_detection_success():
    state = make_state()

    state.add_observation(
        source="validate_sensor_data",
        content={
            "success": True,
            "records": warning_records(),
        },
    )

    result = (
        detect_anomalies_from_state(
            state
        )
    )

    assert result["success"] is True

    assert (
        result["anomaly_detected"]
        is True
    )


def test_factory_returns_agent_tool():
    state = make_state()

    state.add_observation(
        source="validate_sensor_data",
        content={
            "success": True,
            "records": normal_records(),
        },
    )

    tool = make_detect_anomalies()

    result = tool(
        state
    )

    assert result["success"] is True