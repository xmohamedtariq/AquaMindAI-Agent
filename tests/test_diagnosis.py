from src.agent.state import AgentState
from src.tools.diagnosis import (
    _build_hypothesis,
    _classify_pattern,
    _latest_anomaly_result,
    _metric_change,
    _select_rejection_change,
    diagnose_from_state,
    diagnose_operational_issue,
    make_diagnose_issue,
)


def make_state() -> AgentState:
    return AgentState(
        task_id="diagnosis-test",
        user_request=(
            "Diagnose RO performance deterioration"
        ),
    )


def make_anomaly_result(
    *,
    flow_change: float = -12.0,
    rejection_change: float = -8.0,
    pressure_change: float = 15.0,
    rejection_metric: str = (
        "tds_salt_rejection_pct"
    ),
    detected: bool = True,
    severity: str = "critical",
):
    return {
        "success": True,
        "anomaly_detected": detected,
        "overall_severity": severity,
        "warning_threshold_pct": 5.0,
        "comparisons": {
            "permeate_flow": {
                "change_pct":
                    flow_change,
            },
            rejection_metric: {
                "change_pct":
                    rejection_change,
            },
            "pressure_drop": {
                "change_pct":
                    pressure_change,
            },
        },
    }


def test_metric_change():
    comparisons = {
        "metric": {
            "change_pct": -10,
        }
    }

    assert (
        _metric_change(
            comparisons,
            "metric",
        )
        == -10.0
    )


def test_metric_change_missing_or_invalid():
    assert (
        _metric_change(
            {},
            "metric",
        )
        is None
    )

    assert (
        _metric_change(
            {
                "metric": "bad",
            },
            "metric",
        )
        is None
    )

    assert (
        _metric_change(
            {
                "metric": {
                    "change_pct": "bad",
                }
            },
            "metric",
        )
        is None
    )


def test_selects_tds_rejection_first():
    metric, change = (
        _select_rejection_change(
            {
                "tds_salt_rejection_pct": {
                    "change_pct": -7,
                },
                (
                    "conductivity_rejection_"
                    "estimate_pct"
                ): {
                    "change_pct": -8,
                },
            }
        )
    )

    assert (
        metric
        == "tds_salt_rejection_pct"
    )

    assert change == -7.0


def test_uses_conductivity_rejection_fallback():
    metric, change = (
        _select_rejection_change(
            {
                (
                    "conductivity_rejection_"
                    "estimate_pct"
                ): {
                    "change_pct": -8,
                }
            }
        )
    )

    assert (
        metric
        == (
            "conductivity_rejection_"
            "estimate_pct"
        )
    )

    assert change == -8.0


def test_rejection_can_be_unavailable():
    metric, change = (
        _select_rejection_change(
            {}
        )
    )

    assert metric is None
    assert change is None


def test_scaling_or_colloidal_pattern():
    assert (
        _classify_pattern(
            flow_change=-10,
            rejection_change=-8,
            pressure_change=12,
            threshold_pct=5,
        )
        == (
            "scaling_or_colloidal_fouling"
        )
    )


def test_biofouling_pattern():
    assert (
        _classify_pattern(
            flow_change=-10,
            rejection_change=1,
            pressure_change=12,
            threshold_pct=5,
        )
        == "biofouling"
    )


def test_organic_fouling_pattern():
    assert (
        _classify_pattern(
            flow_change=-10,
            rejection_change=1,
            pressure_change=2,
            threshold_pct=5,
        )
        == "organic_fouling"
    )


def test_integrity_or_seal_pattern():
    assert (
        _classify_pattern(
            flow_change=10,
            rejection_change=-8,
            pressure_change=2,
            threshold_pct=5,
        )
        == (
            "membrane_integrity_or_seal_issue"
        )
    )


def test_compaction_pattern():
    assert (
        _classify_pattern(
            flow_change=-10,
            rejection_change=8,
            pressure_change=2,
            threshold_pct=5,
        )
        == (
            "compaction_or_mechanical_change"
        )
    )


def test_unclassified_pattern():
    assert (
        _classify_pattern(
            flow_change=1,
            rejection_change=10,
            pressure_change=10,
            threshold_pct=5,
        )
        is None
    )


def test_build_hypothesis():
    result = _build_hypothesis(
        pattern="biofouling",
        severity="warning",
        flow_change=-10,
        rejection_metric=(
            "tds_salt_rejection_pct"
        ),
        rejection_change=1,
        pressure_change=12,
    )

    assert (
        result["id"]
        == "biofouling"
    )

    assert (
        result["severity"]
        == "warning"
    )

    assert (
        result["confidence"]
        == 0.74
    )

    assert (
        result["confidence_type"]
        == "heuristic"
    )

    assert len(
        result["evidence"]
    ) == 3

    assert len(
        result["verification_steps"]
    ) == 3


def test_non_dictionary_anomaly_result_fails():
    result = diagnose_operational_issue(
        "bad"
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Anomaly result must be "
            "a dictionary."
        )
    )


def test_unsuccessful_anomaly_result_fails():
    result = diagnose_operational_issue(
        {
            "success": False,
        }
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "A successful anomaly result "
            "is required for diagnosis."
        )
    )


def test_no_anomaly_returns_normal_status():
    result = diagnose_operational_issue(
        make_anomaly_result(
            detected=False,
        )
    )

    assert result["success"] is True

    assert (
        result["insufficient_evidence"]
        is False
    )

    assert (
        result["diagnosis_status"]
        == "no_actionable_anomaly"
    )

    assert (
        result["primary_hypothesis"]
        is None
    )


def test_invalid_comparisons_fail():
    result = diagnose_operational_issue(
        {
            "success": True,
            "anomaly_detected": True,
            "comparisons": "bad",
        }
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Anomaly comparisons are "
            "missing or invalid."
        )
    )


def test_missing_diagnostic_metrics_are_insufficient():
    result = diagnose_operational_issue(
        {
            "success": True,
            "anomaly_detected": True,
            "warning_threshold_pct": 5,
            "comparisons": {
                "permeate_flow": {
                    "change_pct": -10,
                }
            },
        }
    )

    assert result["success"] is True

    assert (
        result["insufficient_evidence"]
        is True
    )

    assert (
        result["diagnosis_status"]
        == "insufficient_evidence"
    )


def test_unclassified_abnormal_pattern():
    result = diagnose_operational_issue(
        make_anomaly_result(
            flow_change=1,
            rejection_change=10,
            pressure_change=10,
        )
    )

    assert result["success"] is True

    assert (
        result["insufficient_evidence"]
        is True
    )

    assert (
        result["diagnosis_status"]
        == "unclassified_pattern"
    )


def test_scaling_or_colloidal_diagnosis():
    result = diagnose_operational_issue(
        make_anomaly_result()
    )

    assert result["success"] is True

    assert (
        result["insufficient_evidence"]
        is False
    )

    assert (
        result["diagnosis_status"]
        == "hypothesis_generated"
    )

    primary = result[
        "primary_hypothesis"
    ]

    assert (
        primary["id"]
        == (
            "scaling_or_colloidal_fouling"
        )
    )

    assert (
        primary["severity"]
        == "critical"
    )


def test_biofouling_diagnosis():
    result = diagnose_operational_issue(
        make_anomaly_result(
            flow_change=-10,
            rejection_change=1,
            pressure_change=12,
            severity="warning",
        )
    )

    assert (
        result[
            "primary_hypothesis"
        ]["id"]
        == "biofouling"
    )


def test_organic_fouling_diagnosis():
    result = diagnose_operational_issue(
        make_anomaly_result(
            flow_change=-10,
            rejection_change=1,
            pressure_change=2,
        )
    )

    assert (
        result[
            "primary_hypothesis"
        ]["id"]
        == "organic_fouling"
    )


def test_membrane_integrity_diagnosis():
    result = diagnose_operational_issue(
        make_anomaly_result(
            flow_change=10,
            rejection_change=-8,
            pressure_change=2,
        )
    )

    assert (
        result[
            "primary_hypothesis"
        ]["id"]
        == (
            "membrane_integrity_or_seal_issue"
        )
    )


def test_compaction_diagnosis():
    result = diagnose_operational_issue(
        make_anomaly_result(
            flow_change=-10,
            rejection_change=8,
            pressure_change=2,
        )
    )

    assert (
        result[
            "primary_hypothesis"
        ]["id"]
        == (
            "compaction_or_mechanical_change"
        )
    )


def test_conductivity_fallback_diagnosis():
    result = diagnose_operational_issue(
        make_anomaly_result(
            rejection_metric=(
                "conductivity_rejection_"
                "estimate_pct"
            )
        )
    )

    evidence = result[
        "primary_hypothesis"
    ]["evidence"]

    assert (
        evidence[1]["metric"]
        == (
            "conductivity_rejection_"
            "estimate_pct"
        )
    )


def test_latest_anomaly_result_covers_skips():
    state = make_state()

    expected = make_anomaly_result()

    state.add_observation(
        source="detect_anomalies",
        content=expected,
    )

    state.add_observation(
        source="detect_anomalies",
        content={
            "success": False,
        },
    )

    state.add_observation(
        source="detect_anomalies",
        content="bad-content",
    )

    state.add_observation(
        source="other_tool",
        content={
            "success": True,
        },
    )

    assert (
        _latest_anomaly_result(
            state
        )
        == expected
    )


def test_latest_anomaly_result_can_be_missing():
    state = make_state()

    assert (
        _latest_anomaly_result(
            state
        )
        is None
    )


def test_diagnose_from_state_without_anomaly_fails():
    result = diagnose_from_state(
        make_state()
    )

    assert result["success"] is False

    assert (
        result["error"]
        == (
            "Successful anomaly evidence "
            "is unavailable for diagnosis."
        )
    )


def test_diagnose_from_state_success():
    state = make_state()

    state.add_observation(
        source="detect_anomalies",
        content=make_anomaly_result(),
    )

    result = diagnose_from_state(
        state
    )

    assert result["success"] is True

    assert (
        result[
            "diagnosis_status"
        ]
        == "hypothesis_generated"
    )


def test_factory_returns_agent_tool():
    state = make_state()

    state.add_observation(
        source="detect_anomalies",
        content=make_anomaly_result(),
    )

    tool = make_diagnose_issue()

    result = tool(
        state
    )

    assert result["success"] is True

    assert (
        result[
            "primary_hypothesis"
        ]["id"]
        == (
            "scaling_or_colloidal_fouling"
        )
    )