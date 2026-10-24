from collections.abc import Callable
from typing import Any

from src.agent.state import AgentState
from src.tools.kpi_tools import (
    _calculate_pressure_drop,
    _calculate_recovery,
    _calculate_rejection,
    _column_values,
)


VALIDATION_SOURCE = "validate_sensor_data"

DEFAULT_WARNING_THRESHOLD_PCT = 5.0
DEFAULT_CRITICAL_THRESHOLD_PCT = 10.0
DEFAULT_WINDOW_SIZE = 3


METRIC_DIRECTIONS = {
    "permeate_flow": "decrease",
    "recovery_rate_pct": "decrease",
    "tds_salt_rejection_pct": "decrease",
    "pressure_drop": "increase",
    "specific_energy_consumption": "increase",
}


def _relative_change_pct(
    baseline: float,
    current: float,
) -> float | None:
    """
    Calculate percentage change relative to baseline.

    Returns None when baseline is zero because
    relative change would be undefined.
    """

    if baseline == 0:
        return None

    return (
        (current - baseline)
        / abs(baseline)
        * 100.0
    )


def _severity_for_change(
    change_pct: float,
    direction: str,
    warning_threshold_pct: float,
    critical_threshold_pct: float,
) -> str | None:
    """
    Classify a directional deterioration.

    Thresholds represent anomaly sensitivity,
    not physical plant safety limits.
    """

    if direction == "decrease":
        deterioration = -change_pct

    elif direction == "increase":
        deterioration = change_pct

    else:
        raise ValueError(
            f"Unsupported anomaly direction: {direction}"
        )

    if deterioration >= critical_threshold_pct:
        return "critical"

    if deterioration >= warning_threshold_pct:
        return "warning"

    return None


def _window_comparison(
    values: list[float],
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> dict[str, float] | None:
    """
    Compare an early baseline window with
    the most recent window.

    At least two values are required.
    """

    if len(values) < 2:
        return None

    window = min(
        window_size,
        max(
            1,
            len(values) // 2,
        ),
    )

    baseline_values = values[
        :window
    ]

    current_values = values[
        -window:
    ]

    baseline = (
        sum(baseline_values)
        / len(baseline_values)
    )

    current = (
        sum(current_values)
        / len(current_values)
    )

    change_pct = _relative_change_pct(
        baseline=baseline,
        current=current,
    )

    if change_pct is None:
        return None

    return {
        "baseline": round(
            baseline,
            4,
        ),
        "current": round(
            current,
            4,
        ),
        "change_pct": round(
            change_pct,
            4,
        ),
    }


def _build_metric_series(
    records: list[dict[str, Any]],
) -> dict[str, list[float]]:
    """
    Build operational metric time series from
    validated RO sensor records.
    """

    return {
        "permeate_flow":
            _column_values(
                records,
                "permeate_flow",
            ),

        "recovery_rate_pct":
            _calculate_recovery(
                records
            ),

        "tds_salt_rejection_pct":
            _calculate_rejection(
                records=records,
                feed_column="feed_tds",
                permeate_column="permeate_tds",
            ),

        "pressure_drop":
            _calculate_pressure_drop(
                records
            ),

        "specific_energy_consumption":
            _column_values(
                records,
                "specific_energy_consumption",
            ),
    }


def detect_operational_anomalies(
    records: list[dict[str, Any]],
    warning_threshold_pct: float = (
        DEFAULT_WARNING_THRESHOLD_PCT
    ),
    critical_threshold_pct: float = (
        DEFAULT_CRITICAL_THRESHOLD_PCT
    ),
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> dict[str, Any]:
    """
    Detect directional deterioration in RO data.

    Current method:
    baseline relative-change detection.

    This detects investigation signals only.
    It does not automatically issue physical
    control commands or cleaning instructions.
    """

    if not records:
        return {
            "success": False,
            "recoverable": False,
            "error": (
                "No validated sensor records "
                "were provided for anomaly detection."
            ),
        }

    if warning_threshold_pct <= 0:
        return {
            "success": False,
            "recoverable": False,
            "error": (
                "Warning threshold must be "
                "greater than zero."
            ),
        }

    if (
        critical_threshold_pct
        <= warning_threshold_pct
    ):
        return {
            "success": False,
            "recoverable": False,
            "error": (
                "Critical threshold must be "
                "greater than warning threshold."
            ),
        }

    if window_size <= 0:
        return {
            "success": False,
            "recoverable": False,
            "error": (
                "Window size must be "
                "greater than zero."
            ),
        }

    metric_series = (
        _build_metric_series(
            records
        )
    )

    anomalies: list[
        dict[str, Any]
    ] = []

    comparisons: dict[
        str,
        dict[str, Any],
    ] = {}

    available_metrics: list[str] = []
    insufficient_metrics: list[str] = []

    critical_detected = False
    warning_detected = False

    for (
        metric,
        direction,
    ) in METRIC_DIRECTIONS.items():

        values = metric_series[
            metric
        ]

        comparison = (
            _window_comparison(
                values=values,
                window_size=window_size,
            )
        )

        if comparison is None:
            insufficient_metrics.append(
                metric
            )
            continue

        available_metrics.append(
            metric
        )

        severity = (
            _severity_for_change(
                change_pct=(
                    comparison[
                        "change_pct"
                    ]
                ),
                direction=direction,
                warning_threshold_pct=(
                    warning_threshold_pct
                ),
                critical_threshold_pct=(
                    critical_threshold_pct
                ),
            )
        )

        comparisons[
            metric
        ] = {
            **comparison,
            "direction_of_concern":
                direction,
            "severity":
                severity or "normal",
        }

        if severity is None:
            continue

        anomaly = {
            "metric": metric,
            "severity": severity,
            "direction":
                direction,
            "baseline":
                comparison[
                    "baseline"
                ],
            "current":
                comparison[
                    "current"
                ],
            "change_pct":
                comparison[
                    "change_pct"
                ],
            "evidence": (
                f"{metric} changed "
                f"{comparison['change_pct']}% "
                "relative to the early "
                "operating baseline."
            ),
        }

        anomalies.append(
            anomaly
        )

        if severity == "critical":
            critical_detected = True

        else:
            warning_detected = True

    if critical_detected:
        overall_severity = (
            "critical"
        )

    elif warning_detected:
        overall_severity = (
            "warning"
        )

    else:
        overall_severity = (
            "normal"
        )

    return {
        "success": True,
        "recoverable": False,
        "method":
            "baseline_relative_change",
        "anomaly_detected":
            bool(anomalies),
        "overall_severity":
            overall_severity,
        "warning_threshold_pct":
            warning_threshold_pct,
        "critical_threshold_pct":
            critical_threshold_pct,
        "window_size":
            window_size,
        "available_metrics":
            available_metrics,
        "insufficient_metrics":
            insufficient_metrics,
        "comparisons":
            comparisons,
        "anomalies":
            anomalies,
        "notes": [
            (
                "Relative-change thresholds "
                "are anomaly sensitivity "
                "settings, not plant safety "
                "or shutdown limits."
            ),
            (
                "Operational diagnosis must "
                "consider plant-specific "
                "limits, membrane design, "
                "normalization, and supporting "
                "evidence."
            ),
        ],
    }


def _latest_validated_records(
    state: AgentState,
) -> list[dict[str, Any]] | None:
    """
    Retrieve the latest successful validated
    sensor records from agent observations.
    """

    for observation in reversed(
        state.observations
    ):

        if (
            observation.get(
                "source"
            )
            != VALIDATION_SOURCE
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
            content.get(
                "success"
            )
            is not True
        ):
            continue

        records = content.get(
            "records"
        )

        if isinstance(
            records,
            list,
        ):
            return records

    return None


def detect_anomalies_from_state(
    state: AgentState,
) -> dict[str, Any]:
    """
    AgentLoop-compatible anomaly detector.
    """

    records = (
        _latest_validated_records(
            state
        )
    )

    if records is None:
        return {
            "success": False,
            "recoverable": False,
            "error": (
                "Validated sensor records are "
                "unavailable for anomaly detection."
            ),
        }

    return detect_operational_anomalies(
        records
    )


def make_detect_anomalies(
) -> Callable[
    [AgentState],
    dict[str, Any],
]:
    """
    Create the AgentLoop-compatible
    anomaly-detection tool.
    """

    def tool(
        state: AgentState,
    ) -> dict[str, Any]:

        return detect_anomalies_from_state(
            state
        )

    return tool