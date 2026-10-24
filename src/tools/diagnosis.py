from collections.abc import Callable
from typing import Any

from src.agent.state import AgentState


ANOMALY_SOURCE = "detect_anomalies"


HYPOTHESIS_LIBRARY: dict[
    str,
    dict[str, Any],
] = {
    "scaling_or_colloidal_fouling": {
        "label": (
            "Scaling or colloidal fouling"
        ),
        "confidence": 0.78,
        "confidence_type": "heuristic",
        "interpretation": (
            "The combination of declining permeate "
            "performance, worsening rejection, and "
            "increasing pressure drop is consistent "
            "with membrane deposition. Telemetry "
            "alone cannot reliably distinguish "
            "scaling from colloidal fouling."
        ),
        "verification_steps": [
            (
                "Normalize membrane performance for "
                "temperature, feed salinity, pressure, "
                "and recovery before confirming "
                "membrane deterioration."
            ),
            (
                "Check stage localization. Scaling "
                "often begins toward the final stage, "
                "while particulate or colloidal "
                "deposition may appear earlier."
            ),
            (
                "Review pretreatment performance, "
                "turbidity or SDI evidence, "
                "antiscalant operation, and feed/"
                "concentrate water chemistry."
            ),
        ],
    },

    "biofouling": {
        "label": "Possible biofouling",
        "confidence": 0.74,
        "confidence_type": "heuristic",
        "interpretation": (
            "Declining permeate performance with "
            "relatively stable rejection and "
            "increasing pressure drop is consistent "
            "with a biofouling-type pattern."
        ),
        "verification_steps": [
            (
                "Check whether deterioration is "
                "strongest in the front end of "
                "the RO system."
            ),
            (
                "Review pretreatment and biological "
                "control history."
            ),
            (
                "Seek microbiological or deposit "
                "evidence before confirming "
                "biofouling."
            ),
        ],
    },

    "organic_fouling": {
        "label": "Possible organic fouling",
        "confidence": 0.62,
        "confidence_type": "heuristic",
        "interpretation": (
            "Reduced permeate performance with "
            "relatively stable rejection and "
            "pressure drop can be consistent with "
            "organic fouling."
        ),
        "verification_steps": [
            (
                "Normalize membrane performance "
                "before attributing the trend "
                "to fouling."
            ),
            (
                "Review feed-water organic loading "
                "and pretreatment history."
            ),
            (
                "Check for oil, organic contaminants, "
                "or incompatible treatment chemicals."
            ),
        ],
    },

    "membrane_integrity_or_seal_issue": {
        "label": (
            "Possible membrane integrity "
            "or seal issue"
        ),
        "confidence": 0.70,
        "confidence_type": "heuristic",
        "interpretation": (
            "Increasing permeate flow together with "
            "worsening rejection and relatively "
            "stable pressure drop can indicate an "
            "integrity or sealing problem."
        ),
        "verification_steps": [
            (
                "Check membrane and pressure-vessel "
                "integrity using approved diagnostic "
                "procedures."
            ),
            (
                "Inspect interconnector and O-ring "
                "condition where appropriate."
            ),
            (
                "Review oxidant exposure and "
                "membrane-damage history."
            ),
        ],
    },

    "compaction_or_mechanical_change": {
        "label": (
            "Possible membrane compaction "
            "or mechanical change"
        ),
        "confidence": 0.65,
        "confidence_type": "heuristic",
        "interpretation": (
            "Declining permeate performance with "
            "improving rejection and relatively "
            "stable pressure drop can be consistent "
            "with compaction or a mechanical "
            "operating change."
        ),
        "verification_steps": [
            (
                "Review pressure excursions and "
                "water-hammer events."
            ),
            (
                "Normalize performance for "
                "temperature and operating pressure."
            ),
            (
                "Review membrane age and prior "
                "operating conditions."
            ),
        ],
    },
}


def _failure(
    message: str,
) -> dict[str, Any]:
    """Return a standard diagnostic failure."""

    return {
        "success": False,
        "recoverable": False,
        "error": message,
    }


def _metric_change(
    comparisons: dict[str, Any],
    metric: str,
) -> float | None:
    """
    Extract a metric's relative percentage change.
    """

    comparison = comparisons.get(
        metric
    )

    if not isinstance(
        comparison,
        dict,
    ):
        return None

    change = comparison.get(
        "change_pct"
    )

    if not isinstance(
        change,
        (int, float),
    ):
        return None

    return float(
        change
    )


def _select_rejection_change(
    comparisons: dict[str, Any],
) -> tuple[str | None, float | None]:
    """
    Prefer TDS-based rejection evidence.

    Conductivity-based rejection is used only
    when TDS rejection is unavailable.
    """

    tds_change = _metric_change(
        comparisons,
        "tds_salt_rejection_pct",
    )

    if tds_change is not None:
        return (
            "tds_salt_rejection_pct",
            tds_change,
        )

    conductivity_change = _metric_change(
        comparisons,
        (
            "conductivity_rejection_"
            "estimate_pct"
        ),
    )

    if conductivity_change is not None:
        return (
            (
                "conductivity_rejection_"
                "estimate_pct"
            ),
            conductivity_change,
        )

    return (
        None,
        None,
    )


def _classify_pattern(
    flow_change: float,
    rejection_change: float,
    pressure_change: float,
    threshold_pct: float,
) -> str | None:
    """
    Classify an RO troubleshooting pattern.

    All changes are relative to the detector's
    operating baseline.

    The result is a hypothesis category,
    not a confirmed root cause.
    """

    flow_down = (
        flow_change
        <= -threshold_pct
    )

    flow_up = (
        flow_change
        >= threshold_pct
    )

    rejection_down = (
        rejection_change
        <= -threshold_pct
    )

    rejection_up = (
        rejection_change
        >= threshold_pct
    )

    rejection_stable = (
        abs(
            rejection_change
        )
        < threshold_pct
    )

    pressure_up = (
        pressure_change
        >= threshold_pct
    )

    pressure_stable = (
        abs(
            pressure_change
        )
        < threshold_pct
    )

    if (
        flow_down
        and rejection_down
        and pressure_up
    ):
        return (
            "scaling_or_colloidal_fouling"
        )

    if (
        flow_down
        and rejection_stable
        and pressure_up
    ):
        return "biofouling"

    if (
        flow_down
        and rejection_stable
        and pressure_stable
    ):
        return "organic_fouling"

    if (
        flow_up
        and rejection_down
        and pressure_stable
    ):
        return (
            "membrane_integrity_or_seal_issue"
        )

    if (
        flow_down
        and rejection_up
        and pressure_stable
    ):
        return (
            "compaction_or_mechanical_change"
        )

    return None


def _build_hypothesis(
    pattern: str,
    severity: str,
    flow_change: float,
    rejection_metric: str,
    rejection_change: float,
    pressure_change: float,
) -> dict[str, Any]:
    """
    Build an evidence-backed diagnostic hypothesis.
    """

    template = HYPOTHESIS_LIBRARY[
        pattern
    ]

    return {
        "id": pattern,
        "label": template[
            "label"
        ],
        "confidence": template[
            "confidence"
        ],
        "confidence_type": template[
            "confidence_type"
        ],
        "severity": severity,
        "interpretation": template[
            "interpretation"
        ],
        "evidence": [
            {
                "metric":
                    "permeate_flow",
                "change_pct":
                    round(
                        flow_change,
                        4,
                    ),
            },
            {
                "metric":
                    rejection_metric,
                "change_pct":
                    round(
                        rejection_change,
                        4,
                    ),
            },
            {
                "metric":
                    "pressure_drop",
                "change_pct":
                    round(
                        pressure_change,
                        4,
                    ),
            },
        ],
        "verification_steps": list(
            template[
                "verification_steps"
            ]
        ),
    }


def diagnose_operational_issue(
    anomaly_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate a cautious RO root-cause hypothesis
    from anomaly-detection evidence.

    The function deliberately returns hypotheses,
    not definitive diagnoses.
    """

    if not isinstance(
        anomaly_result,
        dict,
    ):
        return _failure(
            (
                "Anomaly result must be "
                "a dictionary."
            )
        )

    if (
        anomaly_result.get(
            "success"
        )
        is not True
    ):
        return _failure(
            (
                "A successful anomaly result "
                "is required for diagnosis."
            )
        )

    if not anomaly_result.get(
        "anomaly_detected",
        False,
    ):
        return {
            "success": True,
            "recoverable": False,
            "insufficient_evidence": False,
            "diagnosis_status":
                "no_actionable_anomaly",
            "hypotheses": [],
            "primary_hypothesis": None,
            "conclusion": (
                "No actionable directional "
                "anomaly pattern was detected."
            ),
            "notes": [
                (
                    "Absence of a detected trend "
                    "does not prove that the RO "
                    "system is fault-free."
                )
            ],
        }

    comparisons = anomaly_result.get(
        "comparisons"
    )

    if not isinstance(
        comparisons,
        dict,
    ):
        return _failure(
            (
                "Anomaly comparisons are "
                "missing or invalid."
            )
        )

    flow_change = _metric_change(
        comparisons,
        "permeate_flow",
    )

    pressure_change = _metric_change(
        comparisons,
        "pressure_drop",
    )

    (
        rejection_metric,
        rejection_change,
    ) = _select_rejection_change(
        comparisons
    )

    if (
        flow_change is None
        or pressure_change is None
        or rejection_change is None
        or rejection_metric is None
    ):
        return {
            "success": True,
            "recoverable": False,
            "insufficient_evidence": True,
            "diagnosis_status":
                "insufficient_evidence",
            "hypotheses": [],
            "primary_hypothesis": None,
            "conclusion": (
                "The available anomaly evidence "
                "is insufficient for a defensible "
                "RO root-cause hypothesis."
            ),
            "notes": [
                (
                    "Permeate-flow, rejection, and "
                    "pressure-drop trends are needed "
                    "for this diagnostic pattern "
                    "classifier."
                )
            ],
        }

    threshold_pct = float(
        anomaly_result.get(
            "warning_threshold_pct",
            5.0,
        )
    )

    pattern = _classify_pattern(
        flow_change=flow_change,
        rejection_change=(
            rejection_change
        ),
        pressure_change=(
            pressure_change
        ),
        threshold_pct=threshold_pct,
    )

    if pattern is None:
        return {
            "success": True,
            "recoverable": False,
            "insufficient_evidence": True,
            "diagnosis_status":
                "unclassified_pattern",
            "hypotheses": [],
            "primary_hypothesis": None,
            "conclusion": (
                "An abnormal trend exists, but "
                "its combination does not match "
                "a supported diagnostic pattern."
            ),
            "notes": [
                (
                    "AquaMind will not invent a "
                    "root cause when the telemetry "
                    "pattern is ambiguous."
                )
            ],
        }

    severity = str(
        anomaly_result.get(
            "overall_severity",
            "warning",
        )
    )

    hypothesis = _build_hypothesis(
        pattern=pattern,
        severity=severity,
        flow_change=flow_change,
        rejection_metric=(
            rejection_metric
        ),
        rejection_change=(
            rejection_change
        ),
        pressure_change=(
            pressure_change
        ),
    )

    return {
        "success": True,
        "recoverable": False,
        "insufficient_evidence": False,
        "diagnosis_status":
            "hypothesis_generated",
        "hypotheses": [
            hypothesis
        ],
        "primary_hypothesis":
            hypothesis,
        "conclusion": (
            "A supported RO troubleshooting "
            "pattern was identified. The result "
            "is a hypothesis and requires "
            "verification before operational "
            "intervention."
        ),
        "notes": [
            (
                "Confidence values are heuristic "
                "reasoning scores, not calibrated "
                "failure probabilities."
            ),
            (
                "No physical control action is "
                "authorized by this diagnosis."
            ),
        ],
    }


def _latest_anomaly_result(
    state: AgentState,
) -> dict[str, Any] | None:
    """
    Retrieve the latest successful anomaly result
    from agent observations.
    """

    for observation in reversed(
        state.observations
    ):

        if (
            observation.get(
                "source"
            )
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
            content.get(
                "success"
            )
            is not True
        ):
            continue

        return content

    return None


def diagnose_from_state(
    state: AgentState,
) -> dict[str, Any]:
    """
    AgentLoop-compatible diagnosis tool.
    """

    anomaly_result = (
        _latest_anomaly_result(
            state
        )
    )

    if anomaly_result is None:
        return _failure(
            (
                "Successful anomaly evidence "
                "is unavailable for diagnosis."
            )
        )

    return diagnose_operational_issue(
        anomaly_result
    )


def make_diagnose_issue(
) -> Callable[
    [AgentState],
    dict[str, Any],
]:
    """
    Create an AgentLoop-compatible
    diagnostic tool.
    """

    def tool(
        state: AgentState,
    ) -> dict[str, Any]:

        return diagnose_from_state(
            state
        )

    return tool