from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from src.agent.runtime import (
    AquaMindRuntime,
    RuntimeConfig,
)
from src.agent.state import (
    TerminationReason,
)
from src.tools.diagnosis import (
    diagnose_operational_issue,
)


DATA_DIR = Path("data")

MANIFEST_PATH = (
    DATA_DIR
    / "scenario_manifest.json"
)


DIAGNOSTIC_SCENARIOS = [
    "normal_operation.csv",
    "scaling_colloidal_fouling.csv",
    "biofouling.csv",
    "organic_fouling.csv",
    "membrane_integrity_issue.csv",
    "compaction_mechanical_change.csv",
    "unclassified_abnormal.csv",
    "membrane_fouling.csv",
]


def load_manifest() -> dict[str, Any]:
    """Load the deterministic scenario ground truth."""

    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(
            file
        )


def latest_observation_content(
    state: Any,
    source: str,
) -> dict[str, Any] | None:
    """
    Retrieve the latest dictionary observation
    produced by one tool.
    """

    for observation in reversed(
        state.observations
    ):
        if (
            observation.get(
                "source"
            )
            != source
        ):
            continue

        content = observation.get(
            "content"
        )

        if isinstance(
            content,
            dict,
        ):
            return content

    return None


def normalize_diagnosis(
    diagnosis: dict[str, Any] | None,
) -> str:
    """
    Convert AquaMind's internal diagnostic vocabulary
    into scenario-level evaluation labels.

    Important:
    - no_actionable_anomaly is the expected healthy
      operating outcome.
    - unclassified_pattern means an abnormal pattern
      exists but AquaMind correctly refuses to invent
      a supported root cause.
    """

    if diagnosis is None:
        return "missing_diagnosis"

    primary = diagnosis.get(
        "primary_hypothesis"
    )

    if isinstance(
        primary,
        dict,
    ):
        diagnosis_id = primary.get(
            "id"
        )

        if isinstance(
            diagnosis_id,
            str,
        ) and diagnosis_id.strip():
            return (
                diagnosis_id
                .strip()
            )

    status = diagnosis.get(
        "diagnosis_status"
    )

    if not isinstance(
        status,
        str,
    ):
        return "unknown"

    normalized_status = (
        status
        .strip()
        .lower()
    )

    if normalized_status in {
        "normal",
        "normal_operation",
        "no_actionable_anomaly",
    }:
        return "normal_operation"

    if normalized_status in {
        "unclassified",
        "unclassified_pattern",
        "unclassified_abnormal_pattern",
    }:
        return "unclassified"

    if normalized_status:
        return normalized_status

    return "unknown"


def recover_diagnosis_for_evaluation(
    state: Any,
) -> tuple[
    dict[str, Any] | None,
    str,
]:
    """
    Recover the diagnostic decision for evaluation.

    Normally the diagnosis is available in the agent
    observations.

    For a deliberate safety termination such as an
    unclassified abnormal pattern, AgentLoop may stop
    before storing the diagnosis observation. In that
    case this evaluator applies the SAME deterministic
    diagnosis function to the already-recorded anomaly
    result.

    This does not alter runtime behavior.
    It only makes the safety decision observable for
    system evaluation.
    """

    diagnosis = latest_observation_content(
        state,
        "diagnose_issue",
    )

    if diagnosis is not None:
        return (
            diagnosis,
            "runtime_observation",
        )

    anomaly_result = (
        latest_observation_content(
            state,
            "detect_anomalies",
        )
    )

    if anomaly_result is None:
        return (
            None,
            "unavailable",
        )

    diagnosis = (
        diagnose_operational_issue(
            anomaly_result
        )
    )

    return (
        diagnosis,
        "evaluation_replay",
    )


def expected_termination_for(
    expected: str,
) -> TerminationReason:
    """
    Define expected runtime behavior.

    Supported/normal scenarios should complete with
    a final answer.

    Unsupported abnormal telemetry should fail closed
    with insufficient evidence rather than inventing
    a root cause.
    """

    if expected == "unclassified":
        return (
            TerminationReason
            .INSUFFICIENT_EVIDENCE
        )

    return (
        TerminationReason
        .FINAL_ANSWER
    )


def evaluate_scenario(
    filename: str,
    expected: str,
) -> dict[str, Any]:
    """Run one full AquaMind scenario evaluation."""

    with tempfile.TemporaryDirectory() as directory:

        temporary_root = Path(
            directory
        )

        runtime = AquaMindRuntime(
            RuntimeConfig(
                dataset_path=filename,
                allowed_data_root="data",
                knowledge_root="knowledge",
                memory_db_path=(
                    temporary_root
                    / "memory.db"
                ),
                audit_log_path=(
                    temporary_root
                    / "audit.jsonl"
                ),
                knowledge_limit=3,
                budget_cap_usd=0.10,
            )
        )

        result = runtime.run(
            task_id=(
                "scenario-"
                + filename.replace(
                    ".csv",
                    "",
                )
            ),
            user_request=(
                "Analyze this reverse-osmosis "
                "operational dataset, identify "
                "abnormal performance patterns, "
                "and provide an evidence-based "
                "diagnosis and recommendations."
            ),
            plant_id=(
                "evaluation-ro-plant"
            ),
        )

        state = result[
            "state"
        ]

        (
            diagnosis,
            diagnosis_source,
        ) = (
            recover_diagnosis_for_evaluation(
                state
            )
        )

        actual = (
            normalize_diagnosis(
                diagnosis
            )
        )

        expected_termination = (
            expected_termination_for(
                expected
            )
        )

        label_match = (
            actual
            == expected
        )

        termination_match = (
            state.termination_reason
            == expected_termination
        )

        audit_valid = bool(
            result[
                "audit_integrity"
            ][
                "valid"
            ]
        )

        passed = (
            label_match
            and termination_match
            and audit_valid
        )

        actual_termination = (
            state
            .termination_reason
            .value
            if state
            .termination_reason
            is not None
            else "none"
        )

        return {
            "filename":
                filename,

            "expected":
                expected,

            "actual":
                actual,

            "passed":
                passed,

            "label_match":
                label_match,

            "termination_match":
                termination_match,

            "expected_termination":
                expected_termination.value,

            "termination":
                actual_termination,

            "tool_calls":
                state.tool_call_count,

            "audit_valid":
                audit_valid,

            "diagnosis":
                diagnosis,

            "diagnosis_source":
                diagnosis_source,
        }


def print_separator() -> None:
    print(
        "-" * 150
    )


def main() -> None:
    """Evaluate all deterministic diagnostic scenarios."""

    manifest = load_manifest()

    scenarios = manifest[
        "scenarios"
    ]

    results = []

    print()
    print(
        "AquaMind Scenario Evaluation"
    )

    print(
        "Synthetic evaluation data only - "
        "not real plant telemetry."
    )

    print()

    print_separator()

    print(
        f"{'Scenario':36}"
        f"{'Expected':34}"
        f"{'Actual':34}"
        f"{'Termination':26}"
        f"{'Result':10}"
    )

    print_separator()

    for filename in (
        DIAGNOSTIC_SCENARIOS
    ):

        expected = scenarios[
            filename
        ][
            "expected"
        ]

        result = evaluate_scenario(
            filename,
            expected,
        )

        results.append(
            result
        )

        status = (
            "PASS"
            if result[
                "passed"
            ]
            else "FAIL"
        )

        print(
            f"{filename:36}"
            f"{result['expected']:34}"
            f"{result['actual']:34}"
            f"{result['termination']:26}"
            f"{status:10}"
        )

    print_separator()

    total_count = len(
        results
    )

    passed_count = sum(
        1
        for result in results
        if result[
            "passed"
        ]
    )

    label_pass_count = sum(
        1
        for result in results
        if result[
            "label_match"
        ]
    )

    audit_pass_count = sum(
        1
        for result in results
        if result[
            "audit_valid"
        ]
    )

    supported_results = [
        result
        for result in results
        if result[
            "expected"
        ]
        != "unclassified"
    ]

    supported_pass_count = sum(
        1
        for result
        in supported_results
        if result[
            "label_match"
        ]
    )

    boundary_results = [
        result
        for result in results
        if result[
            "expected"
        ]
        == "unclassified"
    ]

    boundary_pass_count = sum(
        1
        for result
        in boundary_results
        if result[
            "passed"
        ]
    )

    print()

    print(
        "Evaluation summary"
    )

    print(
        f"Scenario conformance: "
        f"{passed_count}/{total_count} "
        f"({(
            passed_count
            / total_count
            * 100.0
        ):0.2f}%)"
    )

    print(
        f"Outcome-label conformance: "
        f"{label_pass_count}/{total_count} "
        f"({(
            label_pass_count
            / total_count
            * 100.0
        ):0.2f}%)"
    )

    print(
        f"Supported diagnosis conformance: "
        f"{supported_pass_count}/"
        f"{len(supported_results)}"
    )

    print(
        f"Safety-boundary conformance: "
        f"{boundary_pass_count}/"
        f"{len(boundary_results)}"
    )

    print(
        f"Audit integrity: "
        f"{audit_pass_count}/"
        f"{total_count}"
    )

    print()

    print(
        "Execution details:"
    )

    for result in results:

        print(
            f"- {result['filename']}: "
            f"actual="
            f"{result['actual']}, "
            f"termination="
            f"{result['termination']}, "
            f"expected_termination="
            f"{result['expected_termination']}, "
            f"tool_calls="
            f"{result['tool_calls']}, "
            f"audit_valid="
            f"{result['audit_valid']}, "
            f"diagnosis_source="
            f"{result['diagnosis_source']}"
        )

    failed = [
        result
        for result in results
        if not result[
            "passed"
        ]
    ]

    if failed:

        print()
        print(
            "Non-conforming scenarios:"
        )

        for result in failed:

            print()
            print(
                result[
                    "filename"
                ]
            )

            print(
                "Expected label:",
                result[
                    "expected"
                ],
            )

            print(
                "Actual label:",
                result[
                    "actual"
                ],
            )

            print(
                "Expected termination:",
                result[
                    "expected_termination"
                ],
            )

            print(
                "Actual termination:",
                result[
                    "termination"
                ],
            )

            print(
                "Label match:",
                result[
                    "label_match"
                ],
            )

            print(
                "Termination match:",
                result[
                    "termination_match"
                ],
            )

            print(
                "Audit valid:",
                result[
                    "audit_valid"
                ],
            )

            print(
                "Raw diagnosis:",
                result[
                    "diagnosis"
                ],
            )

    else:

        print()

        print(
            "All scenarios conformed to "
            "their expected diagnostic and "
            "safety outcomes."
        )


if __name__ == "__main__":
    main()