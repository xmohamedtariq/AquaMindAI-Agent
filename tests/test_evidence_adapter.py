import json
from pathlib import Path

import pytest

from src.agent.state import AgentState
from src.knowledge.evidence_adapter import (
    EvidenceAdapterError,
    _latest_anomaly_result,
    _metric_change,
    _raw_trend_summary,
    _read_vocabulary,
    build_runtime_evidence_bundle,
    validate_diagnostic_context,
)


REAL_VOCAB = Path("knowledge/evidence_vocabulary.json")


def _write_json(tmp_path: Path, value) -> Path:
    path = tmp_path / "vocab.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_read_vocabulary_rejects_invalid_sources(tmp_path: Path) -> None:
    with pytest.raises(EvidenceAdapterError):
        _read_vocabulary(tmp_path / "missing.json")

    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    with pytest.raises(EvidenceAdapterError):
        _read_vocabulary(bad)

    with pytest.raises(EvidenceAdapterError):
        _read_vocabulary(_write_json(tmp_path, []))

    with pytest.raises(EvidenceAdapterError):
        _read_vocabulary(_write_json(tmp_path, {}))


def test_read_vocabulary_rejects_bad_terms(tmp_path: Path) -> None:
    with pytest.raises(EvidenceAdapterError):
        _read_vocabulary(
            _write_json(tmp_path, {"terms": ["bad"]})
        )

    with pytest.raises(EvidenceAdapterError):
        _read_vocabulary(
            _write_json(tmp_path, {"terms": [{"name": ""}]})
        )

    with pytest.raises(EvidenceAdapterError):
        _read_vocabulary(
            _write_json(
                tmp_path,
                {
                    "terms": [
                        {"name": "x", "type": "boolean"},
                        {"name": "x", "type": "boolean"},
                    ]
                },
            )
        )

    with pytest.raises(EvidenceAdapterError):
        _read_vocabulary(
            _write_json(tmp_path, {"terms": []})
        )


def test_validate_context_declared_and_supplemental() -> None:
    declared, supplemental = validate_diagnostic_context(
        {
            "temperature_shift": True,
            "permeate_flow_direction": "down",
            "operator_note": "checked",
        },
        vocabulary_path=REAL_VOCAB,
    )

    assert declared == {
        "temperature_shift": True,
        "permeate_flow_direction": "down",
    }
    assert supplemental == {
        "operator_note": "checked"
    }

    assert validate_diagnostic_context(
        None,
        vocabulary_path=REAL_VOCAB,
    ) == ({}, {})


def test_validate_context_rejects_invalid_values(tmp_path: Path) -> None:
    with pytest.raises(EvidenceAdapterError):
        validate_diagnostic_context(
            "bad",  # type: ignore[arg-type]
            vocabulary_path=REAL_VOCAB,
        )

    with pytest.raises(EvidenceAdapterError):
        validate_diagnostic_context(
            {"temperature_shift": "yes"},
            vocabulary_path=REAL_VOCAB,
        )

    with pytest.raises(EvidenceAdapterError):
        validate_diagnostic_context(
            {"permeate_flow_direction": 1},
            vocabulary_path=REAL_VOCAB,
        )

    with pytest.raises(EvidenceAdapterError):
        validate_diagnostic_context(
            {"permeate_flow_direction": "sideways"},
            vocabulary_path=REAL_VOCAB,
        )

    unsupported = _write_json(
        tmp_path,
        {
            "terms": [
                {"name": "x", "type": "number"}
            ]
        },
    )

    with pytest.raises(EvidenceAdapterError):
        validate_diagnostic_context(
            {"x": 1},
            vocabulary_path=unsupported,
        )


def test_latest_anomaly_result_skips_invalid_entries() -> None:
    state = AgentState(
        task_id="evidence-latest",
        user_request="test",
    )
    state.add_observation("other", {"success": True})
    state.add_observation("detect_anomalies", "bad")
    state.add_observation("detect_anomalies", {"success": False})

    assert _latest_anomaly_result(state) is None

    expected = {
        "success": True,
        "anomaly_detected": True,
    }
    state.add_observation("detect_anomalies", expected)
    assert _latest_anomaly_result(state) == expected


def test_metric_change_branches() -> None:
    comparisons = {
        "valid": {"change_pct": 2},
        "bool": {"change_pct": True},
        "text": {"change_pct": "2"},
        "bad": "not-a-dict",
    }

    assert _metric_change(comparisons, "valid") == 2.0
    assert _metric_change(comparisons, "bool") is None
    assert _metric_change(comparisons, "text") is None
    assert _metric_change(comparisons, "bad") is None
    assert _metric_change(comparisons, "missing") is None


def test_raw_trend_summary_none_and_conductivity_fallback() -> None:
    assert _raw_trend_summary(None) == {}

    result = _raw_trend_summary(
        {
            "method": "baseline_relative_change",
            "anomaly_detected": True,
            "overall_severity": "warning",
            "warning_threshold_pct": 5.0,
            "comparisons": {
                "permeate_flow": {"change_pct": -7.0},
                "conductivity_rejection_estimate_pct": {
                    "change_pct": -6.0
                },
                "pressure_drop": {"change_pct": 8.0},
                "recovery_rate_pct": {"change_pct": -4.0},
                "specific_energy_consumption": {"change_pct": 3.0},
            },
        }
    )

    assert result["rejection_metric"] == (
        "conductivity_rejection_estimate_pct"
    )
    assert result["rejection_change_pct"] == -6.0

    no_comparisons = _raw_trend_summary(
        {
            "success": True,
            "comparisons": "bad",
        }
    )
    assert no_comparisons["rejection_metric"] is None


def test_build_runtime_evidence_bundle_keeps_raw_directions_out() -> None:
    state = AgentState(
        task_id="bundle",
        user_request="test",
        diagnostic_context={
            "raw_performance_change": False,
            "temperature_shift": True,
            "normalized_metrics_available": False,
            "operator_note": "verified",
        },
    )

    state.add_observation(
        "detect_anomalies",
        {
            "success": True,
            "method": "baseline_relative_change",
            "anomaly_detected": True,
            "overall_severity": "critical",
            "warning_threshold_pct": 5.0,
            "comparisons": {
                "permeate_flow": {"change_pct": -12.0},
                "tds_salt_rejection_pct": {"change_pct": -9.0},
                "pressure_drop": {"change_pct": 11.0},
            },
        },
    )

    bundle = build_runtime_evidence_bundle(
        state,
        vocabulary_path=REAL_VOCAB,
    )

    # Detector-owned value overrides any supplied duplicate.
    assert bundle["rule_evidence"]["raw_performance_change"] is True
    assert bundle["evidence_provenance"]["raw_performance_change"] == (
        "detect_anomalies"
    )
    assert bundle["rule_evidence"]["temperature_shift"] is True
    assert "permeate_flow_direction" not in bundle["rule_evidence"]
    assert bundle["supplemental_context"] == {
        "operator_note": "verified"
    }
    assert bundle["raw_trend_summary"]["permeate_flow_change_pct"] == -12.0


def test_build_runtime_evidence_without_anomaly() -> None:
    state = AgentState(
        task_id="bundle-no-anomaly",
        user_request="test",
        diagnostic_context={
            "temperature_shift": False,
        },
    )

    bundle = build_runtime_evidence_bundle(
        state,
        vocabulary_path=REAL_VOCAB,
    )

    assert bundle["rule_evidence"] == {
        "temperature_shift": False
    }
    assert bundle["raw_trend_summary"] == {}
