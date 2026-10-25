from src.agent.state import AgentState
from src.tools.reporting import (
    ANOMALY_SOURCE,
    DIAGNOSIS_SOURCE,
    KNOWLEDGE_SOURCE,
    KPI_SOURCE,
    MEMORY_SOURCE,
    VALIDATION_SOURCE,
    _collect_recommendations,
    _dedupe_strings,
    _latest_observation,
    _utc_now,
    build_incident_report,
    generate_incident_report_from_state,
    make_generate_incident_report,
)


def make_state() -> AgentState:
    return AgentState(
        task_id="report-test",
        user_request=(
            "Investigate RO performance degradation"
        ),
        plant_id="plant-a",
    )


def diagnosis_result():
    return {
        "success": True,
        "diagnosis_status":
            "hypothesis_generated",
        "conclusion":
            (
                "The evidence supports a possible "
                "biofouling pattern."
            ),
        "primary_hypothesis": {
            "id":
                "biofouling",
            "label":
                "Possible biofouling",
            "severity":
                "warning",
            "confidence":
                0.74,
            "verification_steps": [
                (
                    "Review pretreatment "
                    "performance."
                ),
                (
                    "Inspect recent pressure-drop "
                    "trend."
                ),
            ],
        },
    }


def add_complete_observations(
    state: AgentState,
) -> None:

    state.add_observation(
        source=VALIDATION_SOURCE,
        content={
            "success": True,
            "data_quality_score": 0.98,
        },
    )

    state.add_observation(
        source=KPI_SOURCE,
        content={
            "success": True,
            "recovery_rate_pct": 42.0,
        },
    )

    state.add_observation(
        source=ANOMALY_SOURCE,
        content={
            "success": True,
            "severity": "warning",
        },
    )

    state.add_observation(
        source=KNOWLEDGE_SOURCE,
        content={
            "success": True,
            "match_count": 2,
        },
    )

    state.add_observation(
        source=MEMORY_SOURCE,
        content={
            "success": True,
            "match_count": 1,
        },
    )

    state.add_observation(
        source=DIAGNOSIS_SOURCE,
        content=diagnosis_result(),
    )


def test_utc_now():
    assert (
        _utc_now()
        .endswith("Z")
    )


def test_latest_observation():
    state = make_state()

    expected = {
        "success": True,
        "value": 2,
    }

    state.add_observation(
        source=KPI_SOURCE,
        content={
            "success": True,
            "value": 1,
        },
    )

    state.add_observation(
        source=KPI_SOURCE,
        content=expected,
    )

    assert (
        _latest_observation(
            state,
            KPI_SOURCE,
        )
        == expected
    )


def test_latest_observation_skips_invalid_entries():
    state = make_state()

    expected = {
        "success": True,
        "value": "valid",
    }

    state.add_observation(
        source=KPI_SOURCE,
        content=expected,
    )

    state.add_observation(
        source=KPI_SOURCE,
        content={
            "success": False,
        },
    )

    state.add_observation(
        source=KPI_SOURCE,
        content="invalid",
    )

    state.add_observation(
        source="other",
        content={
            "success": True,
        },
    )

    assert (
        _latest_observation(
            state,
            KPI_SOURCE,
        )
        == expected
    )


def test_latest_observation_can_be_missing():
    assert (
        _latest_observation(
            make_state(),
            KPI_SOURCE,
        )
        is None
    )


def test_dedupe_strings():
    result = _dedupe_strings(
        [
            " one ",
            "two",
            "one",
            "",
            "   ",
            42,
        ]
    )

    assert result == [
        "one",
        "two",
    ]


def test_collect_recommendations():
    state = make_state()

    state.recommendations = [
        "Review pretreatment performance.",
        "Check feed-water quality.",
    ]

    result = (
        _collect_recommendations(
            state,
            diagnosis_result(),
        )
    )

    assert result == [
        "Review pretreatment performance.",
        "Check feed-water quality.",
        "Inspect recent pressure-drop trend.",
    ]


def test_collect_recommendations_without_valid_primary():
    state = make_state()

    state.recommendations = [
        "Continue monitoring."
    ]

    result = (
        _collect_recommendations(
            state,
            {
                "primary_hypothesis":
                    "invalid",
            },
        )
    )

    assert result == [
        "Continue monitoring."
    ]


def test_collect_recommendations_with_invalid_steps():
    state = make_state()

    result = (
        _collect_recommendations(
            state,
            {
                "primary_hypothesis": {
                    "verification_steps":
                        "invalid",
                }
            },
        )
    )

    assert result == []


def test_report_requires_diagnosis():
    result = build_incident_report(
        make_state()
    )

    assert (
        result["success"]
        is False
    )

    assert (
        "diagnosis"
        in result["error"]
    )


def test_complete_report():
    state = make_state()

    state.turn_count = 7
    state.tool_call_count = 7
    state.cumulative_cost_usd = 0.012
    state.input_tokens = 2000
    state.output_tokens = 500

    add_complete_observations(
        state
    )

    result = build_incident_report(
        state,
        generated_at=(
            "2026-10-25T05:00:00Z"
        ),
    )

    assert (
        result["success"]
        is True
    )

    report = result["report"]

    assert (
        report["report_version"]
        == "1.0"
    )

    assert (
        report["generated_at"]
        == "2026-10-25T05:00:00Z"
    )

    assert (
        report["task_id"]
        == "report-test"
    )

    assert (
        report["plant_id"]
        == "plant-a"
    )

    assert (
        report["diagnosis_status"]
        == "hypothesis_generated"
    )

    assert (
        report["primary_hypothesis"][
            "id"
        ]
        == "biofouling"
    )

    assert (
        report["evidence"][
            "validation"
        ][
            "data_quality_score"
        ]
        == 0.98
    )

    assert (
        report["evidence"][
            "operational_knowledge"
        ][
            "match_count"
        ]
        == 2
    )

    assert (
        report["evidence"][
            "historical_memory"
        ][
            "match_count"
        ]
        == 1
    )

    assert (
        report["execution"][
            "turn_count"
        ]
        == 7
    )

    assert (
        report["execution"][
            "cumulative_cost_usd"
        ]
        == 0.012
    )

    assert (
        len(
            report[
                "recommendations"
            ]
        )
        == 2
    )

    assert (
        "does not authorize"
        in report[
            "safety_notice"
        ]
    )


def test_missing_optional_context_is_supported():
    state = make_state()

    state.add_observation(
        source=DIAGNOSIS_SOURCE,
        content=diagnosis_result(),
    )

    result = build_incident_report(
        state
    )

    assert (
        result["success"]
        is True
    )

    evidence = (
        result["report"][
            "evidence"
        ]
    )

    assert (
        evidence["validation"]
        is None
    )

    assert (
        evidence["plant_kpis"]
        is None
    )

    assert (
        evidence["anomaly_analysis"]
        is None
    )

    assert (
        evidence[
            "operational_knowledge"
        ]
        is None
    )

    assert (
        evidence[
            "historical_memory"
        ]
        is None
    )


def test_invalid_primary_hypothesis_is_normalized():
    state = make_state()

    diagnosis = diagnosis_result()

    diagnosis[
        "primary_hypothesis"
    ] = "invalid"

    state.add_observation(
        source=DIAGNOSIS_SOURCE,
        content=diagnosis,
    )

    result = build_incident_report(
        state
    )

    assert (
        result["report"][
            "primary_hypothesis"
        ]
        is None
    )


def test_missing_conclusion_uses_fallback():
    state = make_state()

    diagnosis = diagnosis_result()

    diagnosis[
        "conclusion"
    ] = " "

    state.add_observation(
        source=DIAGNOSIS_SOURCE,
        content=diagnosis,
    )

    result = build_incident_report(
        state
    )

    assert (
        result["report"][
            "executive_summary"
        ]
        == (
            "No diagnostic conclusion "
            "was produced."
        )
    )


def test_non_string_conclusion_uses_fallback():
    state = make_state()

    diagnosis = diagnosis_result()

    diagnosis[
        "conclusion"
    ] = None

    state.add_observation(
        source=DIAGNOSIS_SOURCE,
        content=diagnosis,
    )

    result = build_incident_report(
        state
    )

    assert (
        result["report"][
            "executive_summary"
        ]
        == (
            "No diagnostic conclusion "
            "was produced."
        )
    )


def test_generate_from_state():
    state = make_state()

    state.add_observation(
        source=DIAGNOSIS_SOURCE,
        content=diagnosis_result(),
    )

    result = (
        generate_incident_report_from_state(
            state
        )
    )

    assert (
        result["success"]
        is True
    )


def test_factory():
    state = make_state()

    state.add_observation(
        source=DIAGNOSIS_SOURCE,
        content=diagnosis_result(),
    )

    tool = (
        make_generate_incident_report()
    )

    result = tool(
        state
    )

    assert (
        result["success"]
        is True
    )