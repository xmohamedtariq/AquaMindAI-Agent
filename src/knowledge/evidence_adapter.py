from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.agent.state import AgentState


ANOMALY_SOURCE = "detect_anomalies"


class EvidenceAdapterError(ValueError):
    """Raised when structured diagnostic context is invalid."""


def _read_vocabulary(
    path: str | Path,
) -> dict[str, dict[str, Any]]:
    """Load the declared evidence vocabulary by term name."""

    file_path = Path(path)

    try:
        data = json.loads(
            file_path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
    ) as exc:
        raise EvidenceAdapterError(
            f"Unable to read evidence vocabulary: {file_path}"
        ) from exc

    if not isinstance(data, dict):
        raise EvidenceAdapterError(
            "Evidence vocabulary root must be an object."
        )

    terms = data.get("terms")

    if not isinstance(terms, list):
        raise EvidenceAdapterError(
            "Evidence vocabulary must contain a terms list."
        )

    result: dict[str, dict[str, Any]] = {}

    for raw in terms:
        if not isinstance(raw, dict):
            raise EvidenceAdapterError(
                "Each evidence vocabulary term must be an object."
            )

        name = raw.get("name")

        if not isinstance(name, str) or not name.strip():
            raise EvidenceAdapterError(
                "Evidence vocabulary term names must be non-empty strings."
            )

        normalized = name.strip()

        if normalized in result:
            raise EvidenceAdapterError(
                f"Duplicate evidence vocabulary term: {normalized}"
            )

        result[normalized] = raw

    if not result:
        raise EvidenceAdapterError(
            "Evidence vocabulary must not be empty."
        )

    return result


def _validate_declared_value(
    *,
    field: str,
    value: Any,
    definition: dict[str, Any],
) -> Any:
    """Validate one value against its declared vocabulary type."""

    evidence_type = definition.get("type")

    if evidence_type == "boolean":
        if not isinstance(value, bool):
            raise EvidenceAdapterError(
                f"Evidence field '{field}' must be boolean."
            )

        return value

    if evidence_type == "enum":
        allowed = definition.get(
            "allowed_values"
        )

        if (
            not isinstance(value, str)
            or not isinstance(allowed, list)
            or value not in allowed
        ):
            raise EvidenceAdapterError(
                f"Evidence field '{field}' has an unsupported enum value."
            )

        return value

    raise EvidenceAdapterError(
        f"Evidence field '{field}' has an unsupported vocabulary type."
    )


def validate_diagnostic_context(
    context: dict[str, Any] | None,
    *,
    vocabulary_path: str | Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    """
    Separate rule-eligible evidence from supplemental context.

    Declared vocabulary fields are validated and may satisfy diagnostic
    rules. Unknown fields are preserved as supplemental context but are
    never supplied to the rule engine.
    """

    if context is None:
        return {}, {}

    if not isinstance(context, dict):
        raise EvidenceAdapterError(
            "Diagnostic context must be a dictionary."
        )

    vocabulary = _read_vocabulary(
        vocabulary_path
    )

    declared: dict[str, Any] = {}
    supplemental: dict[str, Any] = {}

    for field, value in context.items():
        definition = vocabulary.get(
            field
        )

        if definition is None:
            supplemental[field] = value
            continue

        declared[field] = (
            _validate_declared_value(
                field=field,
                value=value,
                definition=definition,
            )
        )

    return declared, supplemental


def _latest_anomaly_result(
    state: AgentState,
) -> dict[str, Any] | None:
    """Return the latest successful anomaly observation."""

    for observation in reversed(
        state.observations
    ):
        if (
            observation.get("source")
            != ANOMALY_SOURCE
        ):
            continue

        content = observation.get(
            "content"
        )

        if not isinstance(
            content,
            dict,
        ):
            continue

        if (
            content.get("success")
            is not True
        ):
            continue

        return content

    return None


def _metric_change(
    comparisons: dict[str, Any],
    metric: str,
) -> float | None:
    """Read one raw baseline-relative metric change."""

    raw = comparisons.get(
        metric
    )

    if not isinstance(raw, dict):
        return None

    value = raw.get(
        "change_pct"
    )

    if (
        isinstance(value, bool)
        or not isinstance(
            value,
            (int, float),
        )
    ):
        return None

    return float(value)


def _raw_trend_summary(
    anomaly_result: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Summarize raw baseline-relative trends without promoting them to
    normalized rule evidence.
    """

    if anomaly_result is None:
        return {}

    comparisons = anomaly_result.get(
        "comparisons"
    )

    if not isinstance(
        comparisons,
        dict,
    ):
        comparisons = {}

    rejection = _metric_change(
        comparisons,
        "tds_salt_rejection_pct",
    )

    rejection_metric = (
        "tds_salt_rejection_pct"
    )

    if rejection is None:
        rejection = _metric_change(
            comparisons,
            "conductivity_rejection_estimate_pct",
        )
        rejection_metric = (
            "conductivity_rejection_estimate_pct"
        )

    return {
        "method": anomaly_result.get(
            "method"
        ),
        "anomaly_detected": bool(
            anomaly_result.get(
                "anomaly_detected",
                False,
            )
        ),
        "overall_severity": anomaly_result.get(
            "overall_severity"
        ),
        "warning_threshold_pct": anomaly_result.get(
            "warning_threshold_pct"
        ),
        "permeate_flow_change_pct": _metric_change(
            comparisons,
            "permeate_flow",
        ),
        "rejection_metric": (
            rejection_metric
            if rejection is not None
            else None
        ),
        "rejection_change_pct": rejection,
        "pressure_drop_change_pct": _metric_change(
            comparisons,
            "pressure_drop",
        ),
        "recovery_change_pct": _metric_change(
            comparisons,
            "recovery_rate_pct",
        ),
        "sec_change_pct": _metric_change(
            comparisons,
            "specific_energy_consumption",
        ),
    }


def build_runtime_evidence_bundle(
    state: AgentState,
    *,
    vocabulary_path: str | Path,
) -> dict[str, Any]:
    """
    Build rule-eligible evidence plus raw-trend provenance.

    AquaMind deliberately does not convert raw baseline-relative trend
    directions into normalized diagnostic-rule directions. Those fields
    may enter the rule engine only when explicitly supplied as validated
    structured context. The anomaly detector contributes only the
    vocabulary-safe ``raw_performance_change`` flag.
    """

    declared, supplemental = (
        validate_diagnostic_context(
            state.diagnostic_context,
            vocabulary_path=(
                vocabulary_path
            ),
        )
    )

    anomaly_result = (
        _latest_anomaly_result(
            state
        )
    )

    rule_evidence = dict(
        declared
    )

    evidence_provenance: dict[
        str,
        str,
    ] = {
        field: "structured_diagnostic_context"
        for field in rule_evidence
    }

    if anomaly_result is not None:
        rule_evidence[
            "raw_performance_change"
        ] = bool(
            anomaly_result.get(
                "anomaly_detected",
                False,
            )
        )

        evidence_provenance[
            "raw_performance_change"
        ] = "detect_anomalies"

    return {
        "rule_evidence": rule_evidence,
        "evidence_provenance": (
            evidence_provenance
        ),
        "raw_trend_summary": (
            _raw_trend_summary(
                anomaly_result
            )
        ),
        "supplemental_context": supplemental,
        "policy_note": (
            "Raw baseline-relative trend directions are not promoted "
            "to normalized diagnostic-rule direction fields. Rule "
            "direction fields require explicit structured context or "
            "a future validated normalization stage."
        ),
    }
