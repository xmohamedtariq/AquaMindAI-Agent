from __future__ import annotations

import pytest

from scripts.evaluate_scenarios import (
    evaluate_scenario,
)


SCENARIOS = [
    (
        "normal_operation.csv",
        "normal_operation",
    ),
    (
        "scaling_colloidal_fouling.csv",
        "scaling_or_colloidal_fouling",
    ),
    (
        "biofouling.csv",
        "biofouling",
    ),
    (
        "organic_fouling.csv",
        "organic_fouling",
    ),
    (
        "membrane_integrity_issue.csv",
        "membrane_integrity_or_seal_issue",
    ),
    (
        "compaction_mechanical_change.csv",
        "compaction_or_mechanical_change",
    ),
    (
        "unclassified_abnormal.csv",
        "unclassified",
    ),
    (
        "membrane_fouling.csv",
        "scaling_or_colloidal_fouling",
    ),
]


@pytest.mark.parametrize(
    (
        "filename",
        "expected",
    ),
    SCENARIOS,
)
def test_system_scenario_conformance(
    filename: str,
    expected: str,
) -> None:
    """
    End-to-end system evaluation.

    Each scenario must match both its expected
    diagnostic outcome and expected safe
    termination behavior.
    """

    result = evaluate_scenario(
        filename,
        expected,
    )

    assert (
        result["label_match"]
        is True
    )

    assert (
        result["termination_match"]
        is True
    )

    assert (
        result["audit_valid"]
        is True
    )

    assert (
        result["passed"]
        is True
    )


def test_supported_diagnoses_complete_normally() -> None:
    """
    Supported diagnostic patterns should produce
    a final answer rather than terminate early.
    """

    supported = [
        (
            "normal_operation.csv",
            "normal_operation",
        ),
        (
            "scaling_colloidal_fouling.csv",
            "scaling_or_colloidal_fouling",
        ),
        (
            "biofouling.csv",
            "biofouling",
        ),
        (
            "organic_fouling.csv",
            "organic_fouling",
        ),
        (
            "membrane_integrity_issue.csv",
            "membrane_integrity_or_seal_issue",
        ),
        (
            "compaction_mechanical_change.csv",
            "compaction_or_mechanical_change",
        ),
    ]

    for (
        filename,
        expected,
    ) in supported:
        result = evaluate_scenario(
            filename,
            expected,
        )

        assert (
            result["termination"]
            == "FINAL_ANSWER"
        )

        assert (
            result["audit_valid"]
            is True
        )


def test_unclassified_pattern_fails_closed() -> None:
    """
    An abnormal pattern outside AquaMind's supported
    diagnostic boundary must not produce an invented
    root-cause hypothesis.
    """

    result = evaluate_scenario(
        "unclassified_abnormal.csv",
        "unclassified",
    )

    assert (
        result["actual"]
        == "unclassified"
    )

    assert (
        result["termination"]
        == "INSUFFICIENT_EVIDENCE"
    )

    assert (
        result["diagnosis"]
        is not None
    )

    assert (
        result["diagnosis"][
            "diagnosis_status"
        ]
        == "unclassified_pattern"
    )

    assert (
        result["diagnosis"][
            "insufficient_evidence"
        ]
        is True
    )

    assert (
        result["diagnosis"][
            "primary_hypothesis"
        ]
        is None
    )

    assert (
        result["audit_valid"]
        is True
    )


def test_normal_operation_has_no_actionable_hypothesis() -> None:
    """
    Stable operation should normalize to the
    normal-operation outcome without inventing
    a fault hypothesis.
    """

    result = evaluate_scenario(
        "normal_operation.csv",
        "normal_operation",
    )

    assert (
        result["actual"]
        == "normal_operation"
    )

    assert (
        result["termination"]
        == "FINAL_ANSWER"
    )

    assert (
        result["diagnosis"]
        is not None
    )

    assert (
        result["diagnosis"][
            "diagnosis_status"
        ]
        == "no_actionable_anomaly"
    )

    assert (
        result["diagnosis"][
            "primary_hypothesis"
        ]
        is None
    )

    assert (
        result["audit_valid"]
        is True
    )